"""External push endpoints.

Let an upstream analysis program write content into an existing node, either
replacing (``mode=w``) or merging/appending (``mode=a``). Frozen nodes are
immutable. Successful pushes are recorded in ``node_contributions`` so a node
can show every source that contributed to it.
"""

from __future__ import annotations

import secrets
from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from asyncpg.connection import Connection

from tc.auth.permissions import check_edit_node
from tc.auth.provider import get_current_user
from tc.content_types.registry import get_descriptor, is_source_item
from tc.db.connection import get_db
from tc.models.content import NodePushRequest
from tc.services.nodes import is_frozen, persist_content

router = APIRouter(prefix="/nodes")


def _generate_validate_key() -> str:
    return secrets.token_hex(10)


def _merge_content(existing: Any, data: Any, mode: str) -> Any:
    if mode == "w":
        return data
    if isinstance(existing, dict) and isinstance(data, dict):
        return {**existing, **data}
    if isinstance(existing, list) and isinstance(data, list):
        return existing + data
    return data


def _embedded_type(content: Any) -> Optional[str]:
    if isinstance(content, dict):
        value = content.get("type")
        if isinstance(value, str):
            return value
    return None


async def _record_contribution(
    conn: Connection,
    node_id: UUID,
    body: NodePushRequest,
    user: dict,
    data_type: str,
) -> None:
    values = (
        body.source_system,
        body.source_id,
        body.source_part,
    )
    if not all(values):
        return
    await conn.execute(
        """INSERT INTO node_contributions
               (node_id, source_system, source_id, source_part, source_url,
                data_type, mode, push_count, pushed_at, pushed_by)
           VALUES ($1, $2, $3, $4, $5, $6, $7, 1, NOW(), $8)
           ON CONFLICT (node_id, source_system, source_id, source_part)
           DO UPDATE SET
               source_url = EXCLUDED.source_url,
               data_type  = EXCLUDED.data_type,
               mode       = EXCLUDED.mode,
               push_count = node_contributions.push_count + 1,
               pushed_at  = NOW(),
               pushed_by  = EXCLUDED.pushed_by""",
        node_id,
        body.source_system,
        body.source_id,
        body.source_part,
        body.source_url,
        data_type,
        body.mode,
        user.get("sub") or "",
    )


@router.put("/{node_id}/push/data")
async def push_to_node(
    node_id: UUID,
    body: NodePushRequest,
    conn: Connection = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    source_values = (body.source_system, body.source_id, body.source_part)
    if any(source_values) and not all(source_values):
        raise HTTPException(
            status_code=400,
            detail="source_system, source_id and source_part must be provided together",
        )

    async with conn.transaction():
        node = await conn.fetchrow(
            """SELECT id, creator_sub, frozen, status, content, content_type,
                      source_system
               FROM nodes WHERE id=$1 FOR UPDATE""",
            node_id,
        )
        if node is None:
            raise HTTPException(status_code=404, detail="Node not found")
        check_edit_node(user, node.get("creator_sub"))

        if is_frozen(node.get("status"), node.get("frozen", False)):
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Node is frozen, cannot be changed.",
            )

        if node.get("source_system"):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Node content is managed by its linked source",
            )

        payload_type = body.data_type or _embedded_type(body.content)
        target_type = payload_type or node.get("content_type")
        if not target_type:
            raise HTTPException(
                status_code=400,
                detail="data_type is required when the node has no type",
            )

        descriptor = get_descriptor(target_type)
        if descriptor is None:
            raise HTTPException(status_code=400, detail="Unknown data type")
        if descriptor.source_system:
            raise HTTPException(
                status_code=400,
                detail="Source-managed metadata types cannot receive pushed content",
            )
        if is_source_item(target_type):
            raise HTTPException(
                status_code=400,
                detail="data_type is required when pushing into a Source Item",
            )

        current_type = node.get("content_type")
        if (
            current_type
            and current_type != target_type
            and not is_source_item(current_type)
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Node already has type '{current_type}'; "
                    f"cannot push '{target_type}'"
                ),
            )

        if body.mode == "a" and descriptor.merge:
            merged = descriptor.merge(node.get("content"), body.content)
        else:
            merged = _merge_content(node.get("content"), body.content, body.mode)
        await persist_content(conn, node_id, merged, target_type)
        await _record_contribution(conn, node_id, body, user, target_type)

    return {
        "status": "ok",
        "node_id": str(node_id),
        "data_type": target_type,
        "mode": body.mode,
    }


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
