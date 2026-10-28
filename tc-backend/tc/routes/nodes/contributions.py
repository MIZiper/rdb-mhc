"""Source contribution records for nodes.

``nodes.source_*`` is the single owner link; ``node_contributions`` records
every source that pushed content into the node (possibly several projects).
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from asyncpg.connection import Connection

from tc.auth.permissions import can_see_node
from tc.auth.provider import get_optional_user
from tc.db.connection import get_db
from tc.models.node import NodeContributionRead

router = APIRouter(prefix="/nodes")

_SELECT = """
    SELECT c.node_id, n.title AS node_title, n.content_type AS node_data_type,
           n.status AS node_status, n.visibility, n.creator_sub,
           c.source_system, c.source_id, c.source_part, c.source_url,
           c.data_type AS contributed_type, c.mode, c.push_count,
           c.pushed_at, c.pushed_by
    FROM node_contributions c
    JOIN nodes n ON n.id = c.node_id
"""


def _row_to_contribution(row) -> NodeContributionRead:
    return NodeContributionRead(
        node_id=row["node_id"],
        node_title=row["node_title"],
        data_type=row["node_data_type"],
        status=row["node_status"],
        source_system=row["source_system"],
        source_id=row["source_id"],
        source_part=row["source_part"],
        source_url=row["source_url"],
        contributed_type=row["contributed_type"],
        mode=row["mode"],
        push_count=row["push_count"],
        pushed_at=row["pushed_at"],
        pushed_by=row["pushed_by"],
    )


def _can_see(row, user: Optional[dict]) -> bool:
    if user is None:
        return row["visibility"] == "public"
    return can_see_node(
        user.get("roles", []),
        row["visibility"],
        row["creator_sub"],
        user["sub"],
    )


@router.get("/{node_id}/contributions", response_model=list[NodeContributionRead])
async def list_node_contributions(
    node_id: UUID,
    conn: Connection = Depends(get_db),
    user=Depends(get_optional_user),
):
    node = await conn.fetchrow(
        "SELECT visibility, creator_sub FROM nodes WHERE id=$1", node_id
    )
    if node is None or not _can_see(node, user):
        raise HTTPException(status_code=404, detail="Node not found")
    rows = await conn.fetch(
        f"{_SELECT} WHERE c.node_id=$1 ORDER BY c.pushed_at DESC", node_id
    )
    return [_row_to_contribution(row) for row in rows]


@router.get("/contributions", response_model=list[NodeContributionRead])
async def list_contributions_by_source(
    source_system: str = Query(...),
    source_id: str = Query(...),
    conn: Connection = Depends(get_db),
    user=Depends(get_optional_user),
):
    rows = await conn.fetch(
        f"""{_SELECT}
            WHERE c.source_system=$1 AND c.source_id=$2
            ORDER BY c.pushed_at DESC""",
        source_system,
        source_id,
    )
    return [_row_to_contribution(row) for row in rows if _can_see(row, user)]
