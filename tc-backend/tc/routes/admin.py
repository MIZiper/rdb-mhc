"""Administrative maintenance endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from asyncpg.connection import Connection

from tc.auth.permissions import ROLE_EDIT_ANY, require_role
from tc.content_types.registry import get_descriptor
from tc.content_types.seed import seed_data_types
from tc.db.connection import get_db
from tc.services.nodes import persist_content, reindex_node_fields

router = APIRouter(prefix="/admin")


@router.post("/reindex")
async def reindex_all(
    conn: Connection = Depends(get_db),
    user: dict = Depends(require_role(ROLE_EDIT_ANY)),
):
    """Rebuild projection rows for every node, upcasting content if needed."""
    rows = await conn.fetch("SELECT id, content, content_type FROM nodes")
    reindexed = 0
    migrated = 0
    for row in rows:
        content = row["content"]
        content_type = row["content_type"]
        descriptor = get_descriptor(content_type)
        if descriptor and descriptor.upcast:
            upcast = descriptor.upcast(content)
            if upcast != content:
                await persist_content(conn, row["id"], upcast, content_type)
                migrated += 1
                reindexed += 1
                continue
        await reindex_node_fields(conn, row["id"], content, content_type)
        reindexed += 1
    return {"reindexed": reindexed, "migrated": migrated}


@router.post("/seed-types")
async def seed_types(
    conn: Connection = Depends(get_db),
    user: dict = Depends(require_role(ROLE_EDIT_ANY)),
):
    """Re-sync code-defined descriptors into the database."""
    await seed_data_types(conn)
    return {"status": "ok"}
