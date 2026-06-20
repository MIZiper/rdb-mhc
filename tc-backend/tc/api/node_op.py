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
from tc.auth.keycloak import get_current_user, get_optional_user
from tc.auth.permissions import (
    require_role,
    check_edit_node,
    can_see_node,
    ROLE_CREATE,
    ROLE_READ_ALL,
    ROLE_REVIEW,
)

router = APIRouter(prefix="/nodes")


def _base_select() -> str:
    return """SELECT id, title, description, updated_at,
        to_jsonb(n) ->> 'content_type' AS content_type,
        to_jsonb(n) ->> 'creator_name' AS creator_name,
        to_jsonb(n) ->> 'creator_sub' AS creator_sub,
        to_jsonb(n) ->> 'status' AS status,
        COALESCE(to_jsonb(n) ->> 'visibility', 'public') AS visibility
     FROM nodes n"""


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
        visibility=r.get("visibility") or "public",
    )


def _visibility_clause(
    user: Optional[dict], table_alias: str = "n", use_and: bool = False
) -> tuple[str, list]:
    """
    Returns (clause, args) where clause uses $1 and $2 for the
    roles array and creator sub. Caller must prepend these args to
    their parameter list and shift their own $N accordingly.
    """
    prefix = "AND" if use_and else "WHERE"
    if user is None:
        return f"{prefix} COALESCE({table_alias}.visibility, 'public') = 'public'", []
    roles = user.get("roles", [])
    if ROLE_READ_ALL in roles:
        return "", []
    sub = user["sub"]
    clause = f"{prefix} ("
    clause += f"COALESCE({table_alias}.visibility, 'public') = 'public' "
    clause += f"OR ('nodes:visibility:' || COALESCE({table_alias}.visibility, 'public')) = ANY($1::text[]) "
    clause += f"OR {table_alias}.creator_sub = $2)"
    return clause, [list(roles), sub]


def _can_see_row(row: dict, user: Optional[dict]) -> bool:
    if user is None:
        return row.get("visibility", "public") == "public"
    return can_see_node(
        user.get("roles", []),
        row.get("visibility", "public"),
        row.get("creator_sub"),
        user["sub"],
    )


@router.get("/", response_model=NodeMetaList)
async def list_nodes(
    conn: Connection = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, le=100),
    q: Optional[str] = Query(None, description="Search by content"),
    user=Depends(get_optional_user),
):
    offset = (page - 1) * page_size
    v_clause, v_args = _visibility_clause(user, "n", use_and=True if q and q.strip() else False)

    has_search = q and q.strip()

    if has_search:
        v_offset = len(v_args)
        q_idx = v_offset + 1
        limit_idx = v_offset + 2
        offset_idx = v_offset + 3
        sql = f"""
            SELECT
                id,
                title,
                description,
                updated_at,
                to_jsonb(n) ->> 'content_type' AS content_type,
                to_jsonb(n) ->> 'creator_name' AS creator_name,
                to_jsonb(n) ->> 'creator_sub' AS creator_sub,
                to_jsonb(n) ->> 'status' AS status,
                COALESCE(to_jsonb(n) ->> 'visibility', 'public') AS visibility,
                ts_headline('english', title, query, 'StartSel=<strong>, StopSel=</strong>') as title_highlight,
                ts_rank(search_vector, query) as relevance
            FROM nodes n, to_tsquery('english', ${q_idx}) as query
            WHERE search_vector @@ query {v_clause}
            ORDER BY relevance DESC
            LIMIT ${limit_idx} OFFSET ${offset_idx}
        """
        params = v_args + [q, page_size, offset]

        count_sql = f"""
            SELECT COUNT(*) FROM nodes n, to_tsquery('english', ${q_idx}) as query
            WHERE search_vector @@ query {v_clause}
        """
        count_args = v_args + [q]
        count_result = await conn.fetchval(count_sql, *count_args)

    else:
        v_offset = len(v_args)
        limit_idx = v_offset + 1
        offset_idx = v_offset + 2
        sql = f"""
            SELECT
                id,
                title,
                description,
                updated_at,
                to_jsonb(n) ->> 'content_type' AS content_type,
                to_jsonb(n) ->> 'creator_name' AS creator_name,
                to_jsonb(n) ->> 'creator_sub' AS creator_sub,
                to_jsonb(n) ->> 'status' AS status,
                COALESCE(to_jsonb(n) ->> 'visibility', 'public') AS visibility,
                NULL as title_highlight,
                NULL as relevance
            FROM nodes n
            {v_clause}
            ORDER BY updated_at DESC
            LIMIT ${limit_idx} OFFSET ${offset_idx}
        """
        params = v_args + [page_size, offset]

        count_sql = f"SELECT COUNT(*) FROM nodes n {v_clause}"
        count_result = await conn.fetchval(count_sql, *v_args)

    nodes_rows = await conn.fetch(sql, *params)
    node_ids = [row["id"] for row in nodes_rows]

    if node_ids:
        tags_rows = await conn.fetch(
            "SELECT node_id, tag_id FROM node_tags WHERE node_id = ANY($1)", node_ids
        )
    else:
        tags_rows = []

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
    user=Depends(get_optional_user),
):
    if not tag_ids:
        return NodeMetaList(items=[], total=0)

    search_tag_ids = tag_ids
    if mode == "ancestors" or mode == "expanded":
        search_tag_ids = await expand_tag_ids(tag_ids)

    v_clause, v_args = _visibility_clause(user, "n", use_and=True)

    limit_clause = ""
    args: list = v_args + [search_tag_ids]
    if limit:
        limit_clause = f"LIMIT ${len(args) + 1}"
        args.append(limit)

    tag_param = len(v_args) + 1

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
            COALESCE(to_jsonb(n) ->> 'visibility', 'public') AS visibility,
            COUNT(nt.tag_id) AS match_count,
            (
                SELECT array_agg(t2.tag_id)
                FROM node_tags t2
                WHERE t2.node_id = n.id
            ) AS tag_ids
        FROM nodes n
        JOIN node_tags nt ON n.id = nt.node_id
        WHERE nt.tag_id = ANY(${tag_param}) {v_clause}
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
async def get_node_meta(
    node_id: UUID,
    conn: Connection = Depends(get_db),
    user=Depends(get_optional_user),
):
    row = await conn.fetchrow(
        f"""{_base_select()} WHERE id=$1""",
        node_id,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Node not found")

    if not _can_see_row(row, user):
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
        """SELECT id, creator_sub, creator_name, status, content_type, visibility
           FROM nodes WHERE id=$1""", node_id
    )
    if existing is None:
        raise HTTPException(status_code=404, detail="Node not found")

    check_edit_node(user, existing.get("creator_sub"))

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
    if node.visibility is not None:
        sets.append(f"visibility=${idx}")
        args.append(node.visibility)
        idx += 1
    if sets:
        sets.append("updated_at=NOW()")
        sql = f"""UPDATE nodes SET {', '.join(sets)} WHERE id=${idx}
                  RETURNING id, title, description, updated_at, content_type,
                            creator_name, creator_sub, status,
                            COALESCE(visibility, 'public') AS visibility"""
        args.append(node_id)
        row = await conn.fetchrow(sql, *args)
    else:
        row = await conn.fetchrow(
            f"""{_base_select()} WHERE id=$1""",
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
    user: dict = Depends(require_role(ROLE_CREATE)),
):
    row = await conn.fetchrow(
        """INSERT INTO nodes (title, description, creator_sub, creator_name, status, visibility)
           VALUES ($1, $2, $3, $4, 'draft', $5)
           RETURNING id, updated_at""",
        node.title,
        node.description,
        user["sub"],
        user["name"],
        node.visibility,
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
        visibility=node.visibility,
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
            to_jsonb(n) ->> 'status' AS status,
            COALESCE(to_jsonb(n) ->> 'visibility', 'public') AS visibility
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
    user: dict = Depends(require_role(ROLE_REVIEW)),
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
                     creator_name, creator_sub, status,
                     COALESCE(visibility, 'public') AS visibility""",
        body.status,
        node_id,
    )
    tags_rows = await conn.fetch(
        "SELECT tag_id FROM node_tags WHERE node_id=$1", node_id
    )
    tag_ids = [r["tag_id"] for r in tags_rows]
    return _row_to_meta(row, tag_ids)
