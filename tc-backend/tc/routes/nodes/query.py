"""Cross-type retrieval and aggregation.

Queries run against the ``node_fields`` projection built by
``tc.services.nodes`` and join regular node metadata, so a single request can
search, filter and aggregate across every content type.
"""

from __future__ import annotations

from itertools import product
from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from asyncpg.connection import Connection

from tc.auth.permissions import can_see_node
from tc.auth.provider import get_optional_user
from tc.db.connection import get_db
from tc.models.query import AggregateRequest, NodeQuery
from tc.content_types.registry import get_descriptor
from tc.services.nodes import build_conditions, load_tags_map

router = APIRouter(prefix="/nodes")


def _add_factory() -> tuple[list, Any]:
    args: list = []

    def add(value: Any) -> int:
        args.append(value)
        return len(args)

    return args, add


def _where(conditions: list[str]) -> str:
    return (" WHERE " + " AND ".join(conditions)) if conditions else ""


def _field_value(row) -> Any:
    if row["kind"] == "number":
        return row["num_value"]
    if row["kind"] == "date":
        return row["ts_value"]
    return row["text_value"]


async def _attach_meta(conn: Connection, rows) -> list[dict]:
    node_ids = [r["id"] for r in rows]
    tags_map = await load_tags_map(conn, node_ids)

    preview_keys: set[str] = set()
    for r in rows:
        descriptor = get_descriptor(r["content_type"])
        if descriptor:
            preview_keys.update(descriptor.preview)

    fields_map: dict = {nid: {} for nid in node_ids}
    if node_ids and preview_keys:
        field_rows = await conn.fetch(
            """SELECT node_id, key, kind, num_value, text_value, ts_value
               FROM node_fields
               WHERE node_id = ANY($1) AND key = ANY($2)""",
            node_ids,
            list(preview_keys),
        )
        for f in field_rows:
            value = _field_value(f)
            bucket = fields_map.setdefault(f["node_id"], {})
            if f["key"] in bucket:
                existing = bucket[f["key"]]
                if isinstance(existing, list):
                    existing.append(value)
                else:
                    bucket[f["key"]] = [existing, value]
            else:
                bucket[f["key"]] = value

    return [
        {
            "id": r["id"],
            "title": r["title"],
            "description": r["description"],
            "updated_at": r["updated_at"],
            "data_type": r["content_type"],
            "tag_ids": tags_map.get(r["id"], []),
            "creator_name": r["creator_name"],
            "creator_sub": r["creator_sub"],
            "status": r["status"],
            "visibility": r["visibility"],
            "fields": fields_map.get(r["id"], {}),
        }
        for r in rows
    ]


@router.post("/query")
async def query_nodes(
    body: NodeQuery,
    conn: Connection = Depends(get_db),
    user=Depends(get_optional_user),
):
    args, add = _add_factory()
    conditions = await build_conditions(
        conn,
        user,
        types=body.types,
        tag_ids=body.tag_ids,
        tag_mode=body.tag_mode,
        filters=body.filters,
        status=body.status,
        text=body.text,
        add=add,
    )
    where_sql = _where(conditions)
    total = await conn.fetchval(f"SELECT COUNT(*) FROM nodes n{where_sql}", *args)

    limit_idx = add(body.page_size)
    offset_idx = add((body.page - 1) * body.page_size)
    rows = await conn.fetch(
        f"""SELECT n.id, n.title, n.description, n.updated_at, n.content_type,
                   n.creator_name, n.creator_sub, n.status, n.visibility
            FROM nodes n{where_sql}
            ORDER BY n.updated_at DESC
            LIMIT ${limit_idx} OFFSET ${offset_idx}""",
        *args,
    )
    return {"items": await _attach_meta(conn, rows), "total": total}


@router.post("/aggregate")
async def aggregate_nodes(
    body: AggregateRequest,
    conn: Connection = Depends(get_db),
    user=Depends(get_optional_user),
):
    args, add = _add_factory()
    conditions = await build_conditions(
        conn,
        user,
        types=body.types,
        tag_ids=body.tag_ids,
        tag_mode=body.tag_mode,
        filters=body.filters,
        status=body.status,
        text=None,
        add=add,
    )
    where_sql = _where(conditions)
    rows = await conn.fetch(f"SELECT n.id FROM nodes n{where_sql}", *args)
    node_ids = [r["id"] for r in rows]
    if not node_ids:
        return {"groups": [], "total_nodes": 0}

    metric_map: dict[UUID, list[float]] = {nid: [] for nid in node_ids}
    if body.metric:
        metric_rows = await conn.fetch(
            """SELECT node_id, num_value FROM node_fields
               WHERE node_id = ANY($1) AND key = $2 AND kind = 'number'""",
            node_ids,
            body.metric,
        )
        for m in metric_rows:
            if m["num_value"] is not None:
                metric_map[m["node_id"]].append(float(m["num_value"]))

    group_values: dict[UUID, dict[str, list]] = {nid: {} for nid in node_ids}
    if body.group_by:
        group_rows = await conn.fetch(
            """SELECT node_id, key, kind, num_value, text_value, ts_value
               FROM node_fields
               WHERE node_id = ANY($1) AND key = ANY($2)""",
            node_ids,
            list(body.group_by),
        )
        for g in group_rows:
            group_values[g["node_id"]].setdefault(g["key"], []).append(_field_value(g))

    tag_values: dict[UUID, list[int]] = {nid: [] for nid in node_ids}
    if body.group_by_tag:
        tag_rows = await conn.fetch(
            "SELECT node_id, tag_id FROM node_tags WHERE node_id = ANY($1)", node_ids
        )
        for t in tag_rows:
            tag_values[t["node_id"]].append(t["tag_id"])

    buckets: dict[tuple, dict] = {}
    for nid in node_ids:
        dims: list[list] = []
        for key in body.group_by:
            dims.append(group_values[nid].get(key) or [None])
        if body.group_by_tag:
            dims.append(tag_values[nid] or [None])

        combos = product(*dims) if dims else [()]
        metric_values = metric_map[nid]
        for combo in combos:
            group: dict[str, Any] = {}
            i = 0
            for key in body.group_by:
                group[key] = combo[i]
                i += 1
            if body.group_by_tag:
                group["tag_id"] = combo[i]
            bucket_key = tuple(sorted(group.items(), key=lambda kv: kv[0]))
            bucket = buckets.setdefault(
                bucket_key, {"group": group, "nodes": set(), "values": []}
            )
            bucket["nodes"].add(nid)
            bucket["values"].extend(metric_values)

    groups = []
    for bucket in buckets.values():
        values = bucket["values"]
        count = len(bucket["nodes"])
        if body.func == "count":
            result = count
        elif not values:
            result = None
        elif body.func == "avg":
            result = sum(values) / len(values)
        elif body.func == "min":
            result = min(values)
        elif body.func == "max":
            result = max(values)
        else:  # sum
            result = sum(values)
        groups.append(
            {
                "group": bucket["group"],
                "value": result,
                "count": count,
                "sample_size": len(values),
            }
        )

    groups.sort(key=lambda g: [str(v) for v in g["group"].values()])
    return {"groups": groups, "total_nodes": len(node_ids)}


@router.get("/fields")
async def list_field_keys(conn: Connection = Depends(get_db)):
    try:
        rows = await conn.fetch(
            "SELECT key, kind, unit, label, comparable FROM field_keys ORDER BY key"
        )
    except Exception:  # noqa: BLE001 - table may not be migrated yet
        rows = []
    return [dict(r) for r in rows]


@router.get("/fields/{key}/values")
async def field_values(
    key: str,
    limit: int = Query(50, ge=1, le=500),
    conn: Connection = Depends(get_db),
):
    row = await conn.fetchrow("SELECT kind FROM field_keys WHERE key=$1", key)
    if row is None:
        raise HTTPException(status_code=404, detail="Unknown field key")

    if row["kind"] == "number":
        stats = await conn.fetchrow(
            """SELECT COUNT(*) AS count, MIN(num_value) AS min, MAX(num_value) AS max
               FROM node_fields WHERE key=$1 AND kind='number'""",
            key,
        )
        return {
            "key": key,
            "kind": "number",
            "count": stats["count"],
            "min": stats["min"],
            "max": stats["max"],
            "values": [],
        }

    rows = await conn.fetch(
        """SELECT text_value AS value, COUNT(*) AS count
           FROM node_fields
           WHERE key=$1 AND text_value IS NOT NULL
           GROUP BY text_value
           ORDER BY count DESC, text_value ASC
           LIMIT $2""",
        key,
        limit,
    )
    return {
        "key": key,
        "kind": row["kind"],
        "values": [{"value": r["value"], "count": r["count"]} for r in rows],
    }


@router.get("/data")
async def batch_node_data(
    ids: str = Query(..., description="Comma separated node UUIDs"),
    conn: Connection = Depends(get_db),
    user=Depends(get_optional_user),
):
    raw = [x.strip() for x in ids.split(",") if x.strip()]
    try:
        node_ids = [UUID(x) for x in raw]
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid node id")
    if not node_ids:
        return {"items": []}

    rows = await conn.fetch(
        """SELECT id, title, description, content, content_type, updated_at,
                  creator_name, creator_sub, status, visibility
           FROM nodes WHERE id = ANY($1)""",
        node_ids,
    )

    visible = []
    for r in rows:
        if user is None:
            if r["visibility"] != "public":
                continue
        elif not can_see_node(
            user.get("roles", []), r["visibility"], r["creator_sub"], user["sub"]
        ):
            continue
        visible.append(r)

    if not visible:
        return {"items": []}

    visible_ids = [r["id"] for r in visible]
    tags_map = await load_tags_map(conn, visible_ids)
    return {
        "items": [
            {
                "id": r["id"],
                "title": r["title"],
                "description": r["description"],
                "content": r["content"],
                "data_type": r["content_type"],
                "updated_at": r["updated_at"],
                "tag_ids": tags_map.get(r["id"], []),
                "creator_name": r["creator_name"],
                "creator_sub": r["creator_sub"],
                "status": r["status"],
                "visibility": r["visibility"],
            }
            for r in visible
        ]
    }
