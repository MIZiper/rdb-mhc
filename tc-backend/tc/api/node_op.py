from fastapi import APIRouter, Depends, Query, Body, HTTPException
from typing import Optional
from uuid import UUID
from asyncpg.connection import Connection
from tc.db.connection import get_db
from tc.models import NodeMeta, NodeDetail, NodeResponse

router = APIRouter(prefix="/nodes")

@router.get("/", response_model=NodeResponse)
async def list_nodes(
    conn: Connection = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, le=100),
    q: Optional[str] = Query(None, description="Search by content"),
):
    offset = (page - 1) * page_size

    if q and q.strip():
        # --- 搜索模式 ---
        # xx_tsquery:
        #   - to_tsquery, most flexible but cannot 'a b'
        #   - plainto_tsquery, convert 'a b' to 'a & b', but 'a | b' also to 'a & b'
        #   - websearch_to_tsquery, 'a b' to 'a & b', 'a or b' to 'a | b', but no 'a:*'
        # 按相关性排序
        sql = """
            SELECT
                id,
                title,
                description,
                updated_at,
                to_jsonb(n) ->> 'content_type' AS content_type,
                ts_headline('english', title, query, 'StartSel=<strong>, StopSel=</strong>') as title_highlight,
                ts_rank(search_vector, query) as relevance
            FROM nodes n, to_tsquery('english', $1) as query
            WHERE search_vector @@ query
            ORDER BY relevance DESC
            LIMIT $2 OFFSET $3
        """
        params = (q, page_size, offset)

        count_sql = """
            SELECT COUNT(*) FROM nodes, to_tsquery('english', $1) as query
            WHERE search_vector @@ query
        """
        count_result = await conn.fetchval(count_sql, q)

    else:
        # --- 默认浏览模式 ---
        # 按时间倒序排序，不需要计算 ts_rank 和 headline，性能更高
        sql = """
            SELECT
                id,
                title,
                description,
                updated_at,
                to_jsonb(n) ->> 'content_type' AS content_type,
                NULL as title_highlight,
                NULL as relevance
            FROM nodes n
            ORDER BY updated_at DESC
            LIMIT $1 OFFSET $2
        """
        params = (page_size, offset)

        count_sql = "SELECT COUNT(*) FROM nodes"
        count_result = await conn.fetchval(count_sql)

    nodes_rows = await conn.fetch(sql, *params)
    node_ids = [row["id"] for row in nodes_rows]

    tags_query = """
        SELECT node_id, tag_id
        FROM node_tags
        WHERE node_id = ANY($1)
    """
    tags_rows = await conn.fetch(tags_query, node_ids)

    result_map = {
        r["id"]: NodeMeta(
            id=r["id"],
            title=r["title"],
            description=r["description"],
            updated_at=r["updated_at"],
            tag_ids=[],
            data_type=r["content_type"],
        )
        for r in nodes_rows
    }

    for tag_row in tags_rows:
        nid = tag_row["node_id"]
        if nid in result_map:
            result_map[nid].tag_ids.append(tag_row["tag_id"])

    return NodeResponse(items=[result_map[nid] for nid in node_ids], total=count_result)


@router.post("/by_tags")
async def search_nodes_by_tags(
    conn: Connection = Depends(get_db),
    tag_ids: list[int] = Body(..., description="Search by tags"),
    limit: Optional[int] = Query(
        None, ge=1, le=100, description="Limits of results returned"
    ),
    mode: Optional[str] = Query(
        "exact", description="Tag search mode: exact | ancestors | expanded"
    ),
):
    if not tag_ids:
        return []

    # 构建 SQL 查询
    # 关键点：
    # 1. WHERE nt.tag_id = ANY($1): 高效过滤数组
    # 2. COUNT(nt.tag_id) AS match_count: 计算相关性权重
    # 3. GROUP BY n.id: 按节点分组以进行计数
    # 4. ORDER BY match_count DESC: 匹配越多越靠前
    query = """
        SELECT
            n.id,
            n.title,
            n.description,
            n.updated_at,
            to_jsonb(n) ->> 'content_type' AS content_type,
            COUNT(nt.tag_id) AS match_count,
            (
                SELECT array_agg(t2.tag_id)
                FROM node_tags t2
                WHERE t2.node_id = n.id
            ) AS tag_ids
        FROM nodes n
        JOIN node_tags nt ON n.id = nt.node_id
        WHERE nt.tag_id = ANY($1)
        GROUP BY n.id
        ORDER BY match_count DESC, n.id ASC
        ${limit_clause}
    """

    final_query = query.replace("${limit_clause}", "LIMIT $2" if limit else "")
    args = [tag_ids, limit] if limit else [tag_ids]

    rows = await conn.fetch(final_query, *args)

    return NodeResponse(
        items=[
            NodeMeta(
                id=r["id"],
                title=r["title"],
                description=r["description"],
                updated_at=r["updated_at"],
                tag_ids=r["tag_ids"],
                data_type=r["content_type"],
            )
            for r in rows
        ],
        total=len(rows),
    )


@router.get("/{node_id}/meta", response_model=NodeMeta)
async def get_node_meta(node_id: UUID, conn: Connection = Depends(get_db)):
    row = await conn.fetchrow(
        "SELECT id, title, description, updated_at FROM nodes WHERE id=$1;",
        node_id,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Node not found")
    return NodeMeta(
        id=row["id"],
        tag_ids=[],
        title=row["title"],
        description=row["description"],
        updated_at=row["updated_at"],
        data_type=None,
    )


@router.post("/", response_model=NodeMeta)
async def add_node_with_tags(node: NodeMeta, conn: Connection = Depends(get_db)):
    row = await conn.fetchrow(
        "INSERT INTO nodes (title, description) VALUES ($1, $2) RETURNING id, updated_at",
        node.title,
        node.description,
    )
    if not row:
        raise HTTPException(status_code=500, detail="Failed to create node")

    for tag_id in node.tag_ids:
        await conn.execute(
            "INSERT INTO node_tags (node_id, tag_id) VALUES ($1, $2)", row["id"], tag_id
        )

    return NodeMeta(
        id=row["id"],
        title=node.title,
        description=node.description,
        updated_at=row["updated_at"],
        tag_ids=node.tag_ids,
        data_type=None,
    )