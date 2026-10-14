"""External push endpoints.

Let an upstream analysis program write content into an existing node, either
replacing (``mode=w``) or merging/appending (``mode=a``). Frozen nodes are
immutable.
"""

from __future__ import annotations

import secrets
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, status
from asyncpg.connection import Connection

from tc.auth.permissions import check_edit_node
from tc.auth.provider import get_current_user
from tc.db.connection import get_db
from tc.services.nodes import persist_content

router = APIRouter(prefix="/nodes")


def _generate_validate_key() -> str:
    return secrets.token_hex(10)


@router.put("/{node_id}/push/data")
async def push_to_node(
    node_id: UUID,
    data: dict = Body(...),
    mode: str = Body("w"),
    conn: Connection = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    node = await conn.fetchrow(
        "SELECT id, creator_sub, frozen, content FROM nodes WHERE id=$1", node_id
    )
    if node is None:
        raise HTTPException(status_code=404, detail="Node not found")
    check_edit_node(user, node.get("creator_sub"))

    if node["frozen"]:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Node is frozen, cannot be changed.",
        )

    if mode == "w":
        merged = data
    elif mode == "a":
        existing = node["content"] or {}
        if isinstance(existing, dict) and isinstance(data, dict):
            merged = {**existing, **data}
        elif isinstance(existing, list) and isinstance(data, list):
            merged = existing + data
        else:
            merged = data
    else:
        raise HTTPException(
            status_code=400, detail="Unknown push mode. Use 'w' or 'a'."
        )

    content_type = merged.get("type") if isinstance(merged, dict) else None
    await persist_content(conn, node_id, merged, content_type)
    return {"status": "ok", "node_id": str(node_id)}


@router.post("/{node_id}/push/valkey")
async def reset_validate_key(
    node_id: UUID,
    conn: Connection = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    existing = await conn.fetchrow(
        "SELECT id, creator_sub FROM nodes WHERE id=$1", node_id
    )
    if existing is None:
        raise HTTPException(status_code=404, detail="Node not found")
    check_edit_node(user, existing.get("creator_sub"))

    new_key = _generate_validate_key()
    await conn.execute("UPDATE nodes SET validate_key=$1 WHERE id=$2", new_key, node_id)
    return {"validate_key": new_key}
