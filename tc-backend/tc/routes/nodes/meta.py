"""Node metadata operations.

Data-agnostic CRUD over node metadata (title, description, tags, status,
visibility); the content itself is handled by ``nodes/content.py``.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

import asyncpg
from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from asyncpg.connection import Connection

from tc.auth.permissions import (
    ROLE_CREATE,
    ROLE_EDIT_ANY,
    ROLE_REVIEW,
    can_see_node,
    check_edit_node,
    require_role,
)
from tc.auth.provider import get_current_user, get_optional_user
from tc.content_types.registry import SOURCE_ITEM, all_descriptors
from tc.db.connection import get_db
from tc.models import (
    NodeCreate,
    NodeMetaList,
    NodeMetaRead,
    NodeStatusUpdate,
    NodeUpdate,
)
from tc.services.metahub import expand_tag_ids
from tc.services.nodes import (
    NODE_META_COLUMNS,
    load_tags_map,
    row_to_meta,
    visibility_clause,
)
from tc.settings import settings

router = APIRouter(prefix="/nodes")

_SELECT = f"SELECT {NODE_META_COLUMNS} FROM nodes n"
_RETURNING = """RETURNING id, title, description, updated_at, content_type,
                creator_name, creator_sub, status, visibility,
                source_system, source_id, source_part, source_url,
                source_linked_at, source_linked_by, frozen"""


def _can_see_row(row, user: Optional[dict]) -> bool:
    if user is None:
        return row["visibility"] == "public"
    return can_see_node(
        user.get("roles", []),
        row["visibility"],
        row["creator_sub"],
        user["sub"],
    )


@router.get("/", response_model=NodeMetaList)
async def list_nodes(
    conn: Connection = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, le=100),
    q: Optional[str] = Query(None, description="Search title/description"),
    user=Depends(get_optional_user),
):
    offset = (page - 1) * page_size
    has_search = bool(q and q.strip())
    v_clause, v_args = visibility_clause(user, "n", use_and=has_search)

    if has_search:
        base = len(v_args)
        q_idx, limit_idx, offset_idx = base + 1, base + 2, base + 3
        sql = f"""
            SELECT
                id, title, description, updated_at, n.content_type,
                n.creator_name, n.creator_sub, n.status, n.visibility,
                n.frozen,
                ts_headline('english', title, query,
                            'StartSel=<strong>, StopSel=</strong>') AS title_highlight,
                ts_rank(search_vector, query) AS relevance
            FROM nodes n, to_tsquery('english', ${q_idx}) AS query
            WHERE search_vector @@ query {v_clause}
            ORDER BY relevance DESC
            LIMIT ${limit_idx} OFFSET ${offset_idx}
        """
        params = v_args + [q, page_size, offset]
        count_sql = f"""
            SELECT COUNT(*) FROM nodes n, to_tsquery('english', ${q_idx}) AS query
            WHERE search_vector @@ query {v_clause}
        """
        count_args = v_args + [q]
    else:
        base = len(v_args)
        limit_idx, offset_idx = base + 1, base + 2
        sql = f"""
            SELECT
                id, title, description, updated_at, n.content_type,
                n.creator_name, n.creator_sub, n.status, n.visibility,
                n.frozen,
                NULL AS title_highlight, NULL AS relevance
            FROM nodes n
            {v_clause}
            ORDER BY updated_at DESC
            LIMIT ${limit_idx} OFFSET ${offset_idx}
        """
        params = v_args + [page_size, offset]
        count_sql = f"SELECT COUNT(*) FROM nodes n {v_clause}"
        count_args = v_args

    try:
        total = await conn.fetchval(count_sql, *count_args)
        rows = await conn.fetch(sql, *params)
    except asyncpg.exceptions.PostgresSyntaxError:
        raise HTTPException(status_code=400, detail="Invalid search query syntax")
    node_ids = [row["id"] for row in rows]
    tags_map = await load_tags_map(conn, node_ids)

    return NodeMetaList(
        items=[row_to_meta(row, tags_map.get(row["id"], [])) for row in rows],
        total=total,
    )


@router.post("/by-tags", response_model=NodeMetaList)
async def search_nodes_by_tags(
    conn: Connection = Depends(get_db),
    tag_ids: list[int] = Body(..., description="Tag ids to match"),
    limit: Optional[int] = Query(None, ge=1, le=100),
    mode: Optional[str] = Query("exact", description="exact | ancestors | expanded"),
    user=Depends(get_optional_user),
):
    if not tag_ids:
        return NodeMetaList(items=[], total=0)

    search_ids = tag_ids
    if mode in ("ancestors", "expanded"):
        search_ids = await expand_tag_ids(tag_ids)

    v_clause, v_args = visibility_clause(user, "n", use_and=True)
    args: list = v_args + [search_ids]
    tag_param = len(v_args) + 1

    limit_clause = ""
    if limit:
        limit_clause = f"LIMIT ${len(args) + 1}"
        args.append(limit)

    query = f"""
        SELECT
            n.id, n.title, n.description, n.updated_at, n.content_type,
            n.creator_name, n.creator_sub, n.status, n.visibility,
            n.frozen,
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
        items=[row_to_meta(row, row["tag_ids"]) for row in rows],
        total=len(rows),
    )


@router.get("/source-candidates", response_model=NodeMetaList)
async def list_source_candidates(
    source_system: Optional[str] = Query(None),
    q: str = Query(""),
    page_size: int = Query(20, ge=1, le=100),
    conn: Connection = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Unlinked Source Items the caller may attach to a source resource."""
    types = [SOURCE_ITEM.type]
    types += [
        descriptor.type
        for descriptor in all_descriptors()
        if descriptor.source_system
        and (source_system is None or descriptor.source_system == source_system)
    ]
    types = list(dict.fromkeys(types))

    args: list = [types]
    clauses = [
        "n.source_system IS NULL",
        "n.content_type = ANY($1::text[])",
    ]
    if ROLE_EDIT_ANY not in user.get("roles", []):
        args.append(user["sub"])
        clauses.append(f"n.creator_sub = ${len(args)}")
    if q.strip():
        args.append(f"%{q.strip()}%")
        idx = len(args)
        clauses.append(f"(n.title ILIKE ${idx} OR n.description ILIKE ${idx})")

    args.append(page_size)
    rows = await conn.fetch(
        f"""SELECT {NODE_META_COLUMNS} FROM nodes n
            WHERE {' AND '.join(clauses)}
            ORDER BY n.updated_at DESC
            LIMIT ${len(args)}""",
        *args,
    )
    tags_map = await load_tags_map(conn, [row["id"] for row in rows])
    return NodeMetaList(
        items=[row_to_meta(row, tags_map.get(row["id"], [])) for row in rows],
        total=len(rows),
    )


@router.get("/push-candidates", response_model=NodeMetaList)
async def list_push_candidates(
    q: str = Query(""),
    data_type: Optional[str] = Query(None),
    page_size: int = Query(20, ge=1, le=100),
    conn: Connection = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Editable, non-frozen nodes a source application may push content into."""
    args: list = []
    clauses = [
        "n.content_type IS NOT NULL",
        "n.source_system IS NULL",
        "n.frozen = FALSE",
    ]
    if settings.frozen_status_set:
        args.append(sorted(settings.frozen_status_set))
        clauses.append(f"n.status <> ALL(${len(args)}::text[])")

    if ROLE_EDIT_ANY not in user.get("roles", []):
        args.append(user["sub"])
        clauses.append(f"n.creator_sub = ${len(args)}")

    source_types = [
        descriptor.type
        for descriptor in all_descriptors()
        if descriptor.source_system
    ]
    if source_types:
        args.append(source_types)
        clauses.append(f"n.content_type <> ALL(${len(args)}::text[])")

    if data_type:
        args.append([SOURCE_ITEM.type, data_type])
        clauses.append(f"n.content_type = ANY(${len(args)}::text[])")

    if q.strip():
        args.append(f"%{q.strip()}%")
        idx = len(args)
        clauses.append(f"(n.title ILIKE ${idx} OR n.description ILIKE ${idx})")

    args.append(page_size)
    rows = await conn.fetch(
        f"""SELECT {NODE_META_COLUMNS} FROM nodes n
            WHERE {' AND '.join(clauses)}
            ORDER BY n.updated_at DESC
            LIMIT ${len(args)}""",
        *args,
    )
    tags_map = await load_tags_map(conn, [row["id"] for row in rows])
    return NodeMetaList(
        items=[row_to_meta(row, tags_map.get(row["id"], [])) for row in rows],
        total=len(rows),
    )


@router.get("/mine", response_model=NodeMetaList)
async def list_my_nodes(
    conn: Connection = Depends(get_db),
    user: dict = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
):
    offset = (page - 1) * page_size
    if status_filter:
        sql = f"SELECT {NODE_META_COLUMNS} FROM nodes n WHERE creator_sub=$1 AND status=$3 ORDER BY updated_at DESC LIMIT $2 OFFSET {offset}"
        params = [user["sub"], page_size, status_filter]
        count_sql = "SELECT COUNT(*) FROM nodes WHERE creator_sub=$1 AND status=$2"
        count_args = [user["sub"], status_filter]
    else:
        sql = f"SELECT {NODE_META_COLUMNS} FROM nodes n WHERE creator_sub=$1 ORDER BY updated_at DESC LIMIT $2 OFFSET {offset}"
        params = [user["sub"], page_size]
        count_sql = "SELECT COUNT(*) FROM nodes WHERE creator_sub=$1"
        count_args = [user["sub"]]

    total = await conn.fetchval(count_sql, *count_args)
    rows = await conn.fetch(sql, *params)
    node_ids = [row["id"] for row in rows]
    tags_map = await load_tags_map(conn, node_ids)

    return NodeMetaList(
        items=[row_to_meta(row, tags_map.get(row["id"], [])) for row in rows],
        total=total,
    )


@router.get("/{node_id}/meta", response_model=NodeMetaRead)
async def get_node_meta(
    node_id: UUID,
    conn: Connection = Depends(get_db),
    user=Depends(get_optional_user),
):
    row = await conn.fetchrow(f"{_SELECT} WHERE id=$1", node_id)
    if row is None or not _can_see_row(row, user):
        raise HTTPException(status_code=404, detail="Node not found")
    tags_map = await load_tags_map(conn, [node_id])
    return row_to_meta(row, tags_map.get(node_id, []))


@router.patch("/{node_id}/meta", response_model=NodeMetaRead)
async def update_node_meta(
    node_id: UUID,
    node: NodeUpdate,
    conn: Connection = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    existing = await conn.fetchrow(
        "SELECT id, creator_sub FROM nodes WHERE id=$1", node_id
    )
    if existing is None:
        raise HTTPException(status_code=404, detail="Node not found")
    check_edit_node(user, existing.get("creator_sub"))

    if node.status is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Use PATCH /api/nodes/{id}/state to change status",
        )

    sets: list[str] = []
    args: list = []
    for field, value in (
        ("title", node.title),
        ("description", node.description),
        ("visibility", node.visibility),
    ):
        if value is not None:
            args.append(value)
            sets.append(f"{field}=${len(args)}")

    if sets:
        args.append(node_id)
        sql = f"UPDATE nodes SET {', '.join(sets)}, updated_at=NOW() WHERE id=${len(args)} {_RETURNING}"
        row = await conn.fetchrow(sql, *args)
    else:
        row = await conn.fetchrow(f"{_SELECT} WHERE id=$1", node_id)

    if node.tag_ids is not None:
        await conn.execute("DELETE FROM node_tags WHERE node_id=$1", node_id)
        for tag_id in node.tag_ids:
            await conn.execute(
                "INSERT INTO node_tags (node_id, tag_id) VALUES ($1, $2)",
                node_id,
                tag_id,
            )

    tags_map = await load_tags_map(conn, [node_id])
    return row_to_meta(row, tags_map.get(node_id, []))


@router.post("/", response_model=NodeMetaRead)
async def add_node(
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
    for tag_id in node.tag_ids:
        await conn.execute(
            "INSERT INTO node_tags (node_id, tag_id) VALUES ($1, $2)",
            row["id"],
            tag_id,
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


@router.patch("/{node_id}/status", response_model=NodeMetaRead)
async def update_node_status(
    node_id: UUID,
    body: NodeStatusUpdate,
    conn: Connection = Depends(get_db),
    user: dict = Depends(require_role(ROLE_REVIEW)),
):
    existing = await conn.fetchrow("SELECT id FROM nodes WHERE id=$1", node_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Node not found")

    row = await conn.fetchrow(
        f"UPDATE nodes SET status=$1, updated_at=NOW() WHERE id=$2 {_RETURNING}",
        body.status,
        node_id,
    )
    tags_map = await load_tags_map(conn, [node_id])
    return row_to_meta(row, tags_map.get(node_id, []))
