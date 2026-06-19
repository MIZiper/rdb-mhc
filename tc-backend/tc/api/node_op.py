"""Nodes Operation

In this handler, it provides basic operations on nodes.
The nodes are data irrelevant, meaning client can have its own data structure.
"""

from fastapi import APIRouter, Depends, Query, Body, HTTPException, status
from typing import Optional
from uuid import UUID
from asyncpg.connection import Connection
from tc.db.connection import get_db
from tc.models import NodeMetaRead, NodeMetaList, NodeCreate, NodeUpdate, NodeStatusUpdate
from tc.services.metahub_client import expand_tag_ids
from tc.auth.keycloak import get_current_user, get_optional_user, require_reviewer

router = APIRouter(prefix="/nodes")


def _row_to_meta(r, tag_ids: list[int] = None) -> NodeMetaRead:
    return NodeMetaRead(
        id=r["id"],
        title=r["title"],
        description=r["description"],
        updated_at=r["updated_at"],
        tag_ids=tag_ids or [],
        data_type=r["content_type"],
        creator_name=r.get("creator_name"),
        creator_sub=r.get("creator_sub"),
        status=r.get("status") or "draft",
    )


@router.get("/", response_model=NodeMetaList)
async def list_nodes(
    conn: Connection = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, le=100),
    q: Optional[str] = Query(None, description="Search by content"),
    user: Optional[dict] = Depends(get_optional_user),
):
    offset = (page - 1) * page_size

    if q and q.strip():
        sql = """
            SELECT
                id,
                title,
                description,
                updated_at,
                to_jsonb(n) ->> 'content_type' AS content_type,
                to_jsonb(n) ->> 'creator_name' AS creator_name,
                to_jsonb(n) ->> 'creator_sub' AS creator_sub,
                to_jsonb(n) ->> 'status' AS status,
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
        sql = """
            SELECT
                id,
                title,
                description,
                updated_at,
                to_jsonb(n) ->> 'content_type' AS content_type,
                to_jsonb(n) ->> 'creator_name' AS creator_name,
                to_jsonb(n) ->> 'creator_sub' AS creator_sub,
                to_jsonb(n) ->> 'status' AS status,
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

    result_map = {r["id"]: _row_to_meta(r) for r in nodes_rows}

    for tag_row in tags_rows:
        nid = tag_row["node_id"]
        if nid in result_map:
            result_map[nid].tag_ids.append(tag_row["tag_id"])

    return NodeMetaList(items=[result_map[nid] for nid in node_ids], total=count_result)


@router.post("/by-tags", response_model=NodeMetaList)
async def search_nodes_by_tags(
    conn: Connection = Depends(get_db),
    tag_ids: list[int] = Body(..., description="Tag IDs to search"),
    limit: Optional[int] = Query(
        None, ge=1, le=100, description="Limits of results returned"
    ),
    mode: Optional[str] = Query(
        "exact", description="Tag search mode: exact | ancestors | expanded"
    ),
):
    if not tag_ids:
        return NodeMetaList(items=[], total=0)

    search_tag_ids = tag_ids
    if mode == "ancestors" or mode == "expanded":
        search_tag_ids = await expand_tag_ids(tag_ids)

    limit_clause = "LIMIT $2" if limit else ""
    args = [search_tag_ids, limit] if limit else [search_tag_ids]

    query = f"""
        SELECT
            n.id,
            n.title,
            n.description,
            n.updated_at,
            to_jsonb(n) ->> 'content_type' AS content_type,
            to_jsonb(n) ->> 'creator_name' AS creator_name,
            to_jsonb(n) ->> 'creator_sub' AS creator_sub,
            to_jsonb(n) ->> 'status' AS status,
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
        {limit_clause}
    """

    rows = await conn.fetch(query, *args)

    return NodeMetaList(
        items=[_row_to_meta(r, r["tag_ids"]) for r in rows],
        total=len(rows),
    )


@router.get("/{node_id}/meta", response_model=NodeMetaRead)
async def get_node_meta(node_id: UUID, conn: Connection = Depends(get_db)):
    row = await conn.fetchrow(
        """SELECT id, title, description, updated_at,
            to_jsonb(n) ->> 'content_type' AS content_type,
            to_jsonb(n) ->> 'creator_name' AS creator_name,
            to_jsonb(n) ->> 'creator_sub' AS creator_sub,
            to_jsonb(n) ->> 'status' AS status
           FROM nodes n WHERE id=$1""",
        node_id,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Node not found")
    tags_rows = await conn.fetch(
        "SELECT tag_id FROM node_tags WHERE node_id=$1", node_id
    )
    tag_ids = [r["tag_id"] for r in tags_rows]
    return _row_to_meta(row, tag_ids)


@router.patch("/{node_id}/meta", response_model=NodeMetaRead)
async def update_node_meta(
    node_id: UUID,
    node: NodeUpdate,
    conn: Connection = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    existing = await conn.fetchrow(
        """SELECT id, creator_sub, creator_name, status, content_type
           FROM nodes WHERE id=$1""", node_id
    )
    if existing is None:
        raise HTTPException(status_code=404, detail="Node not found")

    if existing["creator_sub"] is not None and existing["creator_sub"] != user["sub"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the creator can edit this node",
        )

    sets = []
    args = []
    idx = 1

    if node.title is not None:
        sets.append(f"title=${idx}")
        args.append(node.title)
        idx += 1
    if node.description is not None:
        sets.append(f"description=${idx}")
        args.append(node.description)
        idx += 1
    if node.status is not None:
        sets.append(f"status=${idx}")
        args.append(node.status)
        idx += 1
    if sets:
        sets.append("updated_at=NOW()")
        sql = f"""UPDATE nodes SET {', '.join(sets)} WHERE id=${idx}
                  RETURNING id, title, description, updated_at, content_type,
                            creator_name, creator_sub, status"""
        args.append(node_id)
        row = await conn.fetchrow(sql, *args)
    else:
        row = await conn.fetchrow(
            """SELECT id, title, description, updated_at, content_type,
                      creator_name, creator_sub, status
               FROM nodes WHERE id=$1""",
            node_id,
        )

    if node.tag_ids is not None:
        await conn.execute("DELETE FROM node_tags WHERE node_id=$1", node_id)
        for tid in node.tag_ids:
            await conn.execute(
                "INSERT INTO node_tags (node_id, tag_id) VALUES ($1, $2)",
                node_id,
                tid,
            )

    tags_rows = await conn.fetch(
        "SELECT tag_id FROM node_tags WHERE node_id=$1", node_id
    )
    tag_ids = [r["tag_id"] for r in tags_rows]

    return _row_to_meta(row, tag_ids)


@router.post("/", response_model=NodeMetaRead)
async def add_node_with_tags(
    node: NodeCreate,
    conn: Connection = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    row = await conn.fetchrow(
        """INSERT INTO nodes (title, description, creator_sub, creator_name, status)
           VALUES ($1, $2, $3, $4, 'draft')
           RETURNING id, updated_at""",
        node.title,
        node.description,
        user["sub"],
        user["name"],
    )
    if not row:
        raise HTTPException(status_code=500, detail="Failed to create node")

    for tag_id in node.tag_ids:
        await conn.execute(
            "INSERT INTO node_tags (node_id, tag_id) VALUES ($1, $2)", row["id"], tag_id
        )

    return NodeMetaRead(
        id=row["id"],
        title=node.title,
        description=node.description,
        updated_at=row["updated_at"],
        tag_ids=node.tag_ids,
        data_type=None,
        creator_name=user["name"],
        creator_sub=user["sub"],
        status="draft",
    )


@router.get("/mine", response_model=NodeMetaList)
async def list_my_nodes(
    conn: Connection = Depends(get_db),
    user: dict = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, le=100),
    status_filter: Optional[str] = Query(
        None, alias="status", description="Filter by status"
    ),
):
    offset = (page - 1) * page_size

    if status_filter:
        status_where = "AND status = $3"
        params = [user["sub"], page_size, status_filter]
        count_where = "AND status = $2"
        count_params = [user["sub"], status_filter]
    else:
        status_where = ""
        params = [user["sub"], page_size]
        count_where = ""
        count_params = [user["sub"]]

    sql = f"""
        SELECT
            id, title, description, updated_at,
            to_jsonb(n) ->> 'content_type' AS content_type,
            to_jsonb(n) ->> 'creator_name' AS creator_name,
            to_jsonb(n) ->> 'creator_sub' AS creator_sub,
            to_jsonb(n) ->> 'status' AS status
        FROM nodes n
        WHERE creator_sub = $1 {status_where}
        ORDER BY updated_at DESC
        LIMIT $2 OFFSET {offset}
    """

    count_sql = f"""
        SELECT COUNT(*) FROM nodes WHERE creator_sub = $1 {count_where}
    """
    count_result = await conn.fetchval(count_sql, *count_params)

    nodes_rows = await conn.fetch(sql, *params)
    node_ids = [row["id"] for row in nodes_rows]

    tags_query = """
        SELECT node_id, tag_id FROM node_tags WHERE node_id = ANY($1)
    """
    tags_rows = await conn.fetch(tags_query, node_ids)

    result_map = {r["id"]: _row_to_meta(r) for r in nodes_rows}
    for tag_row in tags_rows:
        nid = tag_row["node_id"]
        if nid in result_map:
            result_map[nid].tag_ids.append(tag_row["tag_id"])

    return NodeMetaList(items=[result_map[nid] for nid in node_ids], total=count_result)


@router.patch("/{node_id}/status", response_model=NodeMetaRead)
async def update_node_status(
    node_id: UUID,
    body: NodeStatusUpdate,
    conn: Connection = Depends(get_db),
    user: dict = Depends(require_reviewer),
):
    existing = await conn.fetchrow(
        """SELECT id, creator_sub
           FROM nodes WHERE id=$1""", node_id
    )
    if existing is None:
        raise HTTPException(status_code=404, detail="Node not found")

    row = await conn.fetchrow(
        """UPDATE nodes SET status=$1, updated_at=NOW()
           WHERE id=$2
           RETURNING id, title, description, updated_at, content_type,
                     creator_name, creator_sub, status""",
        body.status,
        node_id,
    )
    tags_rows = await conn.fetch(
        "SELECT tag_id FROM node_tags WHERE node_id=$1", node_id
    )
    tag_ids = [r["tag_id"] for r in tags_rows]
    return _row_to_meta(row, tag_ids)