"""Node persistence and shared query helpers.

Every write to ``nodes.content`` funnels through :func:`persist_content` so
file links and the ``node_fields`` projection stay in sync. The visibility /
filter SQL builder helpers live here too, so all node endpoints share a
single implementation.
"""

from __future__ import annotations

from typing import Any, Callable, Optional
from uuid import UUID

from asyncpg.connection import Connection

from tc.auth.permissions import ROLE_READ_ALL
from tc.content_types.descriptor import extract_field_rows
from tc.content_types.registry import get_descriptor
from tc.models.node import NodeMetaRead
from tc.models.query import QueryFilter
from tc.services.files import link_file_refs
from tc.services.metahub import expand_tag_ids

# Column list used by every "meta" SELECT; row_to_meta expects this shape.
NODE_META_COLUMNS = """n.id, n.title, n.description, n.updated_at, n.content_type,
                       n.creator_name, n.creator_sub, n.status, n.visibility"""


def row_to_meta(row, tag_ids: Optional[list[int]] = None) -> NodeMetaRead:
    return NodeMetaRead(
        id=row["id"],
        title=row["title"],
        description=row["description"],
        updated_at=row["updated_at"],
        tag_ids=tag_ids or [],
        data_type=row["content_type"],
        creator_name=row["creator_name"],
        creator_sub=row["creator_sub"],
        status=row["status"],
        visibility=row["visibility"],
    )


async def load_tags_map(
    conn: Connection, node_ids: list[UUID]
) -> dict[UUID, list[int]]:
    if not node_ids:
        return {}
    rows = await conn.fetch(
        "SELECT node_id, tag_id FROM node_tags WHERE node_id = ANY($1)", node_ids
    )
    result: dict[UUID, list[int]] = {nid: [] for nid in node_ids}
    for row in rows:
        result.setdefault(row["node_id"], []).append(row["tag_id"])
    return result


# --- visibility / filter SQL -------------------------------------------------
# The two builders below share semantics but differ in how they consume query
# parameters: ``add_visibility`` appends to a caller-owned argument list and
# returns ``$N`` placeholders, while ``visibility_clause`` returns a standalone
# clause starting at a fixed ``$start_index`` for the legacy positional style.


def add_visibility(
    user: Optional[dict],
    add: Callable[[Any], int],
    table_alias: str = "n",
    prefix: str = "",
) -> Optional[str]:
    """Return a bare visibility expression, optionally led by ``prefix``.

    ``prefix`` defaults to empty because the common caller (``build_conditions``)
    joins conditions itself; pass ``"WHERE"``/``"AND"`` when the result is
    embedded directly into a query.
    """
    lead = f"{prefix} " if prefix else ""
    if user is None:
        return f"{lead}{table_alias}.visibility = 'public'"
    roles = user.get("roles", [])
    if ROLE_READ_ALL in roles:
        return None
    role_idx = add(list(roles))
    sub_idx = add(user["sub"])
    return (
        f"{lead}({table_alias}.visibility = 'public' "
        f"OR ('nodes:visibility:' || {table_alias}.visibility) = ANY(${role_idx}::text[]) "
        f"OR {table_alias}.creator_sub = ${sub_idx})"
    )


def visibility_clause(
    user: Optional[dict],
    table_alias: str = "n",
    start_index: int = 1,
    use_and: bool = False,
) -> tuple[str, list]:
    args: list = []

    def _add(value: Any) -> int:
        args.append(value)
        return start_index + len(args) - 1

    clause = add_visibility(
        user, _add, table_alias, "AND" if use_and else "WHERE"
    )
    if clause is None:
        return "", []
    return clause, args


def field_condition(f: QueryFilter, add: Callable[[Any], int]) -> str:
    key_idx = add(f.key)
    is_num = isinstance(f.value, (int, float)) and not isinstance(f.value, bool)
    if f.op == "contains":
        val_idx = add(f"%{f.value}%")
        return (
            "EXISTS (SELECT 1 FROM node_fields nf WHERE nf.node_id=n.id "
            f"AND nf.key=${key_idx} AND nf.text_value ILIKE ${val_idx})"
        )
    if f.op in ("gt", "gte", "lt", "lte"):
        sym = {"gt": ">", "gte": ">=", "lt": "<", "lte": "<="}[f.op]
        val_idx = add(f.value)
        return (
            "EXISTS (SELECT 1 FROM node_fields nf WHERE nf.node_id=n.id "
            f"AND nf.key=${key_idx} AND nf.num_value {sym} ${val_idx})"
        )
    col = "num_value" if is_num else "text_value"
    val_idx = add(f.value if is_num else str(f.value))
    if f.op == "ne":
        return (
            "NOT EXISTS (SELECT 1 FROM node_fields nf WHERE nf.node_id=n.id "
            f"AND nf.key=${key_idx} AND nf.{col}=${val_idx})"
        )
    return (
        "EXISTS (SELECT 1 FROM node_fields nf WHERE nf.node_id=n.id "
        f"AND nf.key=${key_idx} AND nf.{col}=${val_idx})"
    )


async def build_conditions(
    conn: Connection,
    user: Optional[dict],
    *,
    types: Optional[list[str]],
    tag_ids: list[int],
    tag_mode: str,
    filters: list[QueryFilter],
    status: Optional[str],
    text: Optional[str],
    add: Callable[[Any], int],
) -> list[str]:
    conditions: list[str] = []

    # No "WHERE"/"AND" prefix here: callers join these conditions themselves.
    visibility = add_visibility(user, add, prefix="")
    if visibility:
        conditions.append(visibility)
    if types:
        conditions.append(f"n.content_type = ANY(${add(list(types))}::text[])")
    if status:
        conditions.append(f"n.status = ${add(status)}")
    if tag_ids:
        resolved = tag_ids
        if tag_mode == "ancestors":
            resolved = await expand_tag_ids(tag_ids)
        conditions.append(
            "EXISTS (SELECT 1 FROM node_tags nt WHERE nt.node_id=n.id "
            f"AND nt.tag_id = ANY(${add(list(resolved))}::int[]))"
        )
    for f in filters:
        conditions.append(field_condition(f, add))
    if text and text.strip():
        text_idx = add(text.strip())
        conditions.append(
            f"(n.search_vector @@ plainto_tsquery('english', ${text_idx}) "
            "OR EXISTS (SELECT 1 FROM node_fields nf WHERE nf.node_id=n.id "
            f"AND nf.search_tsv @@ plainto_tsquery('english', ${text_idx})))"
        )
    return conditions


# --- content write path ------------------------------------------------------


async def reindex_node_fields(
    conn: Connection,
    node_id: UUID,
    content: Any,
    content_type: Optional[str],
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
               (node_id, key, kind, unit, num_value, text_value, ts_value,
                idx_path, search_tsv)
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8::integer[],
                   CASE WHEN $9::text IS NULL OR $9::text = ''
                        THEN NULL
                        ELSE to_tsvector('english', $9::text) END)""",
        [
            (
                node_id,
                row["key"],
                row["kind"],
                row["unit"],
                row["num_value"],
                row["text_value"],
                row["ts_value"],
                row.get("idx_path"),
                row["text_value"] if row["kind"] == "text" else None,
            )
            for row in field_rows
        ],
    )


async def persist_content(
    conn: Connection,
    node_id: UUID,
    content: Any,
    content_type: Optional[str],
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
