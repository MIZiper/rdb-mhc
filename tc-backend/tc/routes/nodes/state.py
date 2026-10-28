"""Publication state and source-link endpoints.

Applications create their TC node first, then link it to their own resource.
The link stores the source coordinates needed to redirect search results back
to the source application. Status changes remain owned by TC reviewers.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, status
from asyncpg.connection import Connection

from tc.auth.permissions import (
    ROLE_REVIEW,
    can_see_node,
    check_edit_node,
    require_role,
)
from tc.auth.provider import get_current_user, get_optional_user
from tc.content_types.registry import (
    SOURCE_ITEM,
    get_descriptor,
    is_source_item,
    resolve_source_type,
)
from tc.db.connection import get_db
from tc.models.node import (
    NodeSourceUpdate,
    NodeStateRead,
    NodeStatusUpdate,
)
from tc.services.nodes import is_frozen, load_tags_map, reindex_node_fields

router = APIRouter(prefix="/nodes")

_STATE_COLUMNS = """id, title, description, content_type, status, updated_at,
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


async def _state(conn: Connection, row) -> NodeStateRead:
    tags_map = await load_tags_map(conn, [row["id"]])
    return NodeStateRead(
        id=row["id"],
        title=row["title"],
        description=row["description"],
        data_type=row.get("content_type"),
        status=row["status"],
        updated_at=row["updated_at"],
        tag_ids=tags_map.get(row["id"], []),
        source_system=row.get("source_system"),
        source_id=row.get("source_id"),
        source_part=row.get("source_part"),
        source_url=row.get("source_url"),
        source_linked_at=row.get("source_linked_at"),
        source_linked_by=row.get("source_linked_by"),
        frozen=is_frozen(row.get("status"), row.get("frozen", False)),
        source_item=is_source_item(row.get("content_type")),
    )


@router.get("/{node_id}/state", response_model=NodeStateRead)
async def get_node_state(
    node_id: UUID,
    conn: Connection = Depends(get_db),
    user=Depends(get_optional_user),
):
    row = await conn.fetchrow(
        f"SELECT {_STATE_COLUMNS}, creator_sub, visibility FROM nodes WHERE id=$1",
        node_id,
    )
    if row is None or not _can_see_row(row, user):
        raise HTTPException(status_code=404, detail="Node not found")
    return await _state(conn, row)


@router.patch("/{node_id}/state", response_model=NodeStateRead)
async def update_node_state(
    node_id: UUID,
    body: NodeStatusUpdate,
    conn: Connection = Depends(get_db),
    user: dict = Depends(require_role(ROLE_REVIEW)),
):
    row = await conn.fetchrow(
        f"UPDATE nodes SET status=$1 WHERE id=$2 RETURNING {_STATE_COLUMNS}",
        body.status,
        node_id,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Node not found")
    return await _state(conn, row)


@router.get("/{node_id}/source", response_model=NodeStateRead)
async def get_node_source(
    node_id: UUID,
    conn: Connection = Depends(get_db),
    user=Depends(get_optional_user),
):
    return await get_node_state(node_id, conn, user)


@router.put("/{node_id}/source", response_model=NodeStateRead)
async def attach_node_source(
    node_id: UUID,
    body: NodeSourceUpdate,
    conn: Connection = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    target_type = body.data_type or resolve_source_type(
        body.source_system, body.source_part
    )
    if not target_type:
        raise HTTPException(
            status_code=400,
            detail="data_type is required for this source",
        )
    descriptor = get_descriptor(target_type)
    if descriptor is None:
        raise HTTPException(status_code=400, detail="Unknown data type")
    if descriptor.source_system != body.source_system:
        raise HTTPException(
            status_code=400,
            detail=f"Data type '{target_type}' is not managed by '{body.source_system}'",
        )

    async with conn.transaction():
        existing = await conn.fetchrow(
            """SELECT creator_sub, source_system, source_id, source_part,
                      content_type, content, status, frozen
               FROM nodes WHERE id=$1 FOR UPDATE""",
            node_id,
        )
        if existing is None:
            raise HTTPException(status_code=404, detail="Node not found")
        check_edit_node(user, existing.get("creator_sub"))

        if is_frozen(existing.get("status"), existing.get("frozen", False)):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Node is frozen and cannot be linked",
            )

        same_source = (
            existing["source_system"] == body.source_system
            and existing["source_id"] == body.source_id
            and existing["source_part"] == body.source_part
        )
        if existing.get("source_system") is not None:
            if not same_source:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Node is already linked to another source",
                )
            if (
                existing.get("content_type") != target_type
                and not is_source_item(existing.get("content_type"))
            ):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Node is already linked to another content type",
                )
        elif (
            existing.get("content_type") != target_type
            and not is_source_item(existing.get("content_type"))
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Node must be a Source Item or already have type "
                    f"'{target_type}' before linking"
                ),
            )

        try:
            row = await conn.fetchrow(
                f"""UPDATE nodes
                    SET source_system=$1, source_id=$2, source_part=$3,
                        source_url=$4, content_type=$5,
                        source_linked_at=NOW(), source_linked_by=$6
                    WHERE id=$7
                    RETURNING {_STATE_COLUMNS}""",
                body.source_system,
                body.source_id,
                body.source_part,
                body.source_url,
                target_type,
                user.get("sub") or "",
                node_id,
            )
        except asyncpg.exceptions.UniqueViolationError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Source is already linked to another node",
            )

        if existing.get("content_type") != target_type:
            await reindex_node_fields(
                conn, node_id, existing.get("content"), target_type
            )

    return await _state(conn, row)


@router.delete("/{node_id}/source", response_model=NodeStateRead)
async def detach_node_source(
    node_id: UUID,
    conn: Connection = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    async with conn.transaction():
        existing = await conn.fetchrow(
            """SELECT creator_sub, status, source_system, content_type, content, frozen
               FROM nodes WHERE id=$1 FOR UPDATE""",
            node_id,
        )
        if existing is None:
            raise HTTPException(status_code=404, detail="Node not found")
        check_edit_node(user, existing.get("creator_sub"))

        if existing.get("source_system") is None:
            raise HTTPException(status_code=404, detail="Node has no source link")
        if (
            is_frozen(existing.get("status"), existing.get("frozen", False))
            or existing["status"] != "draft"
        ) and ROLE_REVIEW not in user.get("roles", []):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Only reviewers can unlink a node that is not editable",
            )

        descriptor = get_descriptor(existing.get("content_type"))
        revert_type = (
            SOURCE_ITEM.type
            if descriptor and descriptor.source_system == existing["source_system"]
            else None
        )

        row = await conn.fetchrow(
            f"""UPDATE nodes
                SET source_system=NULL, source_id=NULL, source_part=NULL,
                    source_url=NULL, source_linked_at=NULL, source_linked_by=NULL,
                    content_type=COALESCE($2::varchar, content_type)
                WHERE id=$1
                RETURNING {_STATE_COLUMNS}""",
            node_id,
            revert_type,
        )

        if revert_type is not None:
            await reindex_node_fields(
                conn, node_id, existing.get("content"), revert_type
            )

    return await _state(conn, row)
