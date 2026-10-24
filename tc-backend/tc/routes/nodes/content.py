"""Typed-content node operations.

Create and edit the content of a node. Content is arbitrary JSON; the type
descriptor decides how it is projected for search/aggregation.
"""

from __future__ import annotations

from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from asyncpg.connection import Connection

from tc.auth.permissions import ROLE_CREATE, can_see_node, check_edit_node, require_role
from tc.auth.provider import get_current_user, get_optional_user
from tc.db.connection import get_db
from tc.models import NodeMetaList, NodeMetaRead
from tc.models.content import ContentPayload, NodeContentCreate, NodeContentRead
from tc.services.nodes import (
    NODE_META_COLUMNS,
    link_file_refs,
    load_tags_map,
    persist_content,
    reindex_node_fields,
    row_to_meta,
    visibility_clause,
)

router = APIRouter(prefix="/nodes")


@router.get("/types/{data_type}", response_model=NodeMetaList)
async def list_nodes_by_type(
    data_type: str,
    conn: Connection = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, le=100),
    user=Depends(get_optional_user),
):
    offset = (page - 1) * page_size
    v_clause, v_args = visibility_clause(user, "n", use_and=True)
    base = len(v_args)
    type_idx, limit_idx, offset_idx = base + 1, base + 2, base + 3

    rows = await conn.fetch(
        f"""SELECT {NODE_META_COLUMNS}, n.content
            FROM nodes n
            WHERE content_type = ${type_idx} {v_clause}
            ORDER BY updated_at DESC
            LIMIT ${limit_idx} OFFSET ${offset_idx}""",
        *(v_args + [data_type, page_size, offset]),
    )
    total = await conn.fetchval(
        f"SELECT COUNT(*) FROM nodes n WHERE content_type = ${type_idx} {v_clause}",
        *(v_args + [data_type]),
    )

    node_ids = [row["id"] for row in rows]
    tags_map = await load_tags_map(conn, node_ids)
    return NodeMetaList(
        items=[row_to_meta(row, tags_map.get(row["id"], [])) for row in rows],
        total=total,
    )


@router.post("/typed", response_model=NodeMetaRead)
async def add_node_with_content(
    node: NodeContentCreate,
    conn: Connection = Depends(get_db),
    user: dict = Depends(require_role(ROLE_CREATE)),
):
    row = await conn.fetchrow(
        """INSERT INTO nodes (title, description, content, content_type,
                              creator_sub, creator_name, status, visibility)
           VALUES ($1, $2, $3, $4, $5, $6, 'draft', $7)
           RETURNING id, updated_at""",
        node.title,
        node.description,
        node.content,
        node.data_type,
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
    await link_file_refs(conn, row["id"], node.content)
    await reindex_node_fields(conn, row["id"], node.content, node.data_type)

    return NodeMetaRead(
        id=row["id"],
        title=node.title,
        description=node.description,
        updated_at=row["updated_at"],
        tag_ids=node.tag_ids,
        data_type=node.data_type,
        creator_name=user["name"],
        creator_sub=user["sub"],
        status="draft",
        visibility=node.visibility,
    )


@router.get("/{node_id}/data", response_model=NodeContentRead)
async def get_node_data(
    node_id: UUID,
    conn: Connection = Depends(get_db),
    user=Depends(get_optional_user),
):
    row = await conn.fetchrow(
        """SELECT id, title, description, content, content_type, updated_at,
                  creator_name, creator_sub, status, visibility,
                  source_system, source_id, source_part, source_url,
                  source_linked_at, source_linked_by
           FROM nodes WHERE id=$1""",
        node_id,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Node not found")
    if user is None:
        if row["visibility"] != "public":
            raise HTTPException(status_code=404, detail="Node not found")
    elif not can_see_node(
        user.get("roles", []), row["visibility"], row["creator_sub"], user["sub"]
    ):
        raise HTTPException(status_code=404, detail="Node not found")

    if not row["content"]:
        raise HTTPException(status_code=404, detail="Node has no data")

    tags_map = await load_tags_map(conn, [node_id])
    return NodeContentRead(
        id=row["id"],
        title=row["title"],
        description=row["description"],
        content=row["content"],
        data_type=row["content_type"],
        updated_at=row["updated_at"],
        tag_ids=tags_map.get(node_id, []),
        creator_name=row["creator_name"],
        creator_sub=row["creator_sub"],
        status=row["status"],
        visibility=row["visibility"],
        source_system=row.get("source_system"),
        source_id=row.get("source_id"),
        source_part=row.get("source_part"),
        source_url=row.get("source_url"),
        source_linked_at=row.get("source_linked_at"),
        source_linked_by=row.get("source_linked_by"),
    )


@router.patch("/{node_id}/data")
async def patch_node_data(
    node_id: UUID,
    updates: dict = Body(..., description="Partial content updates"),
    conn: Connection = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    row = await conn.fetchrow(
        "SELECT content, content_type, creator_sub FROM nodes WHERE id=$1", node_id
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Node not found")
    check_edit_node(user, row.get("creator_sub"))

    merged = _deep_merge(row["content"] or {}, updates)
    updated = await persist_content(conn, node_id, merged, row["content_type"])

    tags_map = await load_tags_map(conn, [node_id])
    return {
        "id": node_id,
        "title": updated["title"],
        "description": updated["description"],
        "content": merged,
        "data_type": row["content_type"],
        "updated_at": updated["updated_at"],
        "tag_ids": tags_map.get(node_id, []),
        "creator_name": updated["creator_name"],
        "creator_sub": updated["creator_sub"],
        "status": updated["status"],
        "visibility": updated["visibility"],
        "source_system": updated.get("source_system"),
        "source_id": updated.get("source_id"),
        "source_part": updated.get("source_part"),
        "source_url": updated.get("source_url"),
        "source_linked_at": updated.get("source_linked_at"),
        "source_linked_by": updated.get("source_linked_by"),
    }


@router.post("/{node_id}/data")
async def ingest_node_data(
    node_id: UUID,
    payload: ContentPayload,
    conn: Connection = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    existing = await conn.fetchrow(
        "SELECT id, creator_sub FROM nodes WHERE id=$1", node_id
    )
    if existing is None:
        raise HTTPException(status_code=404, detail="Node not found")
    check_edit_node(user, existing.get("creator_sub"))

    content_type = payload.data_type or _embedded_type(payload.content)
    row = await persist_content(conn, node_id, payload.content, content_type)

    tags_map = await load_tags_map(conn, [node_id])
    return NodeContentRead(
        id=node_id,
        title=row["title"],
        description=row["description"],
        content=payload.content,
        data_type=content_type,
        updated_at=row["updated_at"],
        tag_ids=tags_map.get(node_id, []),
        creator_name=row["creator_name"],
        creator_sub=row["creator_sub"],
        status=row["status"],
        visibility=row["visibility"],
        source_system=row.get("source_system"),
        source_id=row.get("source_id"),
        source_part=row.get("source_part"),
        source_url=row.get("source_url"),
        source_linked_at=row.get("source_linked_at"),
        source_linked_by=row.get("source_linked_by"),
    )


def _embedded_type(content: Any) -> Optional[str]:
    if isinstance(content, dict):
        value = content.get("type")
        if isinstance(value, str):
            return value
    return None


def _deep_merge(base: Any, updates: dict) -> Any:
    if not isinstance(base, dict):
        return updates
    result = base.copy()
    for key, value in updates.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result
