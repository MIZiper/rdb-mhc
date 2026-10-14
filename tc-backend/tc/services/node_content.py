"""Central content write path.

Every write to ``nodes.content`` funnels through here so that file links and
the ``node_fields`` projection index are always refreshed together with the
content itself.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from asyncpg.connection import Connection

from tc.services.file_link import extract_file_ids
from tc.types.descriptor import extract_field_rows
from tc.types.registry import get_descriptor


async def link_file_refs(conn: Connection, node_id: UUID, content: Any) -> None:
    """Associate uploaded files referenced by ``file_id`` fields to a node."""
    ids = extract_file_ids(content)
    if not ids:
        return
    await conn.execute(
        "UPDATE files SET node_id=$1 WHERE id = ANY($2::uuid[])", node_id, ids
    )


async def reindex_node_fields(
    conn: Connection,
    node_id: UUID,
    content: Any,
    content_type: str | None,
) -> None:
    """Rebuild the projection rows for a node from its content."""
    await conn.execute("DELETE FROM node_fields WHERE node_id=$1", node_id)
    if not content:
        return

    descriptor = get_descriptor(content_type)
    field_rows = extract_field_rows(content, descriptor)
    if not field_rows:
        return

    await conn.executemany(
        """INSERT INTO node_fields
               (node_id, key, kind, unit, num_value, text_value, ts_value, search_tsv)
           VALUES ($1, $2, $3, $4, $5, $6, $7,
                   CASE WHEN $8::text IS NULL OR $8::text = ''
                        THEN NULL
                        ELSE to_tsvector('english', $8::text) END)""",
        [
            (
                node_id,
                row["key"],
                row["kind"],
                row["unit"],
                row["num_value"],
                row["text_value"],
                row["ts_value"],
                row["text_value"] if row["kind"] == "text" else None,
            )
            for row in field_rows
        ],
    )


async def persist_content(
    conn: Connection,
    node_id: UUID,
    content: Any,
    content_type: str | None,
) -> Any:
    """Write content, relink files and rebuild the projection index.

    Returns the ``RETURNING`` row (updated_at, title, description, creator_*,
    status, visibility).
    """
    row = await conn.fetchrow(
        """UPDATE nodes SET content=$1, content_type=$2, updated_at=NOW()
           WHERE id=$3
           RETURNING updated_at, title, description, creator_name, creator_sub,
                     status, visibility""",
        content,
        content_type,
        node_id,
    )
    await link_file_refs(conn, node_id, content)
    await reindex_node_fields(conn, node_id, content, content_type)
    return row
