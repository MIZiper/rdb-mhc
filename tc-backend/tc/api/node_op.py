from fastapi import APIRouter, Depends, Query
from typing import Optional
from asyncpg.connection import Connection
from tc.db.connection import get_db
from tc.models import NodeMeta, NodeDetail, NodeResponse

router = APIRouter(prefix="/nodes")

@router.get("/", response_model=NodeResponse)
async def list_nodes(
    conn: Connection = Depends(get_db),
    page: Optional[int]=Query(1, ge=1),
    q: Optional[str] = Query(None, description="Search by content"),
    tags: Optional[str]=Query(None, description="Search by tags"),
):
    page_size = 10
    offset = (page-1) * page_size

    if q and q.strip():
        # --- 搜索模式 ---
        # 使用 plainto_tsquery 防止用户输入语法错误导致报错
        # 按相关性排序
        sql = """
            SELECT 
                id, 
                title, 
                description, 
                updated_at,
                ts_headline('english', title, query, 'StartSel=<strong>, StopSel=</strong>') as title_highlight,
                ts_rank(search_vector, query) as relevance
            FROM nodes, plainto_tsquery('english', $1) as query
            WHERE search_vector @@ query
            ORDER BY relevance DESC
            LIMIT $2 OFFSET $3
        """
        params = (q, page_size, offset)

        count_sql = """
            SELECT COUNT(*) FROM nodes, plainto_tsquery('english', $1) as query
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
                NULL as title_highlight,
                NULL as relevance
            FROM nodes
            ORDER BY updated_at DESC
            LIMIT $1 OFFSET $2
        """
        params = (page_size, offset)

        count_sql = "SELECT COUNT(*) FROM nodes"
        count_result = await conn.fetchval(count_sql)

    rows = await conn.fetch(sql, *params)

    return NodeResponse(
        items = [
            NodeMeta(id=str(r['id']), title=r['title'], description=r['description'], updated_at=r['updated_at'], tags=[]) for r in rows
        ],
        total=count_result
    )

@router.get("/{node_id}")
async def get_node_detail(node_id: str, conn: Connection=Depends(get_db)):
    row = await conn.fetchrow("")

@router.post("/", response_model=NodeMeta)
async def add_node_with_tags(node: NodeDetail, conn: Connection=Depends(get_db)):
    row = await conn.fetchrow("INSERT INTO nodes (title, description, backlink) VALUES ($1, $2, $3) RETURNING id, updated_at", node.title, node.description, node.backlink)
    for tag in node.tags:
        await conn.execute("INSERT INTO node_tags (node_id, tag_id) VALUES ($1, $2)", row['id'], tag.id)

    return NodeMeta(id=str(row['id']), title=node.title, description=node.description, updated_at=row['updated_at'], tags=[])