"""Cross-type retrieval and aggregation.

Queries run against the ``node_fields`` projection built by
``tc.services.node_content`` and join the regular node metadata, so a single
request can search, filter and aggregate across every content type.
"""

from __future__ import annotations

from itertools import product
from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from asyncpg.connection import Connection

from tc.auth.keycloak import get_optional_user
from tc.auth.permissions import ROLE_READ_ALL
from tc.db.connection import get_db
from tc.models.query import AggregateRequest, NodeQuery, QueryFilter
from tc.services.metahub_client import expand_tag_ids
from tc.types.registry import get_descriptor

router = APIRouter(prefix="/nodes")


def _add_factory() -> tuple[list, Any]:
    args: list = []

    def add(value: Any) -> int:
        args.append(value)
        return len(args)

    return args, add


def _visibility_condition(user: Optional[dict], add) -> Optional[str]:
    if user is None:
        return "n.visibility = 'public'"
    roles = user.get("roles", [])
    if ROLE_READ_ALL in roles:
        return None
    role_idx = add(list(roles))
    sub_idx = add(user["sub"])
    return (
        "(n.visibility = 'public' "
        f"OR ('nodes:visibility:' || n.visibility) = ANY(${role_idx}::text[]) "
        f"OR n.creator_sub = ${sub_idx})"
    )


def _field_condition(f: QueryFilter, add) -> str:
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


async def _conditions(
    conn: Connection,
    user: Optional[dict],
    *,
    types: Optional[list[str]],
    tag_ids: list[int],
    tag_mode: str,
    filters: list[QueryFilter],
    status: Optional[str],
    text: Optional[str],
    add,
) -> list[str]:
    conds: list[str] = []
    visibility = _visibility_condition(user, add)
    if visibility:
        conds.append(visibility)
    if types:
        conds.append(f"n.content_type = ANY(${add(list(types))}::text[])")
    if status:
        conds.append(f"n.status = ${add(status)}")
    if tag_ids:
        resolved = tag_ids
        if tag_mode == "ancestors":
            resolved = await expand_tag_ids(tag_ids)
        conds.append(
            "EXISTS (SELECT 1 FROM node_tags nt WHERE nt.node_id=n.id "
            f"AND nt.tag_id = ANY(${add(list(resolved))}::int[]))"
        )
    for f in filters:
        conds.append(_field_condition(f, add))
    if text and text.strip():
        t_idx = add(text.strip())
        conds.append(
            f"(n.search_vector @@ plainto_tsquery('english', ${t_idx}) "
            "OR EXISTS (SELECT 1 FROM node_fields nf WHERE nf.node_id=n.id "
            f"AND nf.search_tsv @@ plainto_tsquery('english', ${t_idx})))"
        )
    return conds


def _where(conds: list[str]) -> str:
    return (" WHERE " + " AND ".join(conds)) if conds else ""


async def _attach_meta(conn: Connection, rows) -> list[dict]:
    node_ids = [r["id"] for r in rows]
    tags_map: dict = {nid: [] for nid in node_ids}
    if node_ids:
        tag_rows = await conn.fetch(
            "SELECT node_id, tag_id FROM node_tags WHERE node_id = ANY($1)", node_ids
        )
        for t in tag_rows:
            tags_map.setdefault(t["node_id"], []).append(t["tag_id"])

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


def _field_value(row) -> Any:
    if row["kind"] == "number":
        return row["num_value"]
    if row["kind"] == "date":
        return row["ts_value"]
    return row["text_value"]


@router.post("/query")
async def query_nodes(
    body: NodeQuery,
    conn: Connection = Depends(get_db),
    user=Depends(get_optional_user),
):
    args, add = _add_factory()
    conds = await _conditions(
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
    where_sql = _where(conds)
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
    items = await _attach_meta(conn, rows)
    return {"items": items, "total": total}


@router.post("/aggregate")
async def aggregate_nodes(
    body: AggregateRequest,
    conn: Connection = Depends(get_db),
    user=Depends(get_optional_user),
):
    args, add = _add_factory()
    conds = await _conditions(
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
    where_sql = _where(conds)
    rows = await conn.fetch(
        f"SELECT n.id FROM nodes n{where_sql}", *args
    )
    node_ids = [r["id"] for r in rows]
    if not node_ids:
        return {"groups": [], "total_nodes": 0}

    metric_map: dict[UUID, list[float]] = {nid: [] for nid in node_ids}
    if body.metric:
        mrows = await conn.fetch(
            """SELECT node_id, num_value FROM node_fields
               WHERE node_id = ANY($1) AND key = $2 AND kind = 'number'""",
            node_ids,
            body.metric,
        )
        for m in mrows:
            if m["num_value"] is not None:
                metric_map[m["node_id"]].append(float(m["num_value"]))

    group_values: dict[UUID, dict[str, list]] = {nid: {} for nid in node_ids}
    if body.group_by:
        grows = await conn.fetch(
            """SELECT node_id, key, kind, num_value, text_value, ts_value
               FROM node_fields
               WHERE node_id = ANY($1) AND key = ANY($2)""",
            node_ids,
            list(body.group_by),
        )
        for g in grows:
            group_values[g["node_id"]].setdefault(g["key"], []).append(_field_value(g))

    tag_values: dict[UUID, list[int]] = {nid: [] for nid in node_ids}
    if body.group_by_tag:
        trows = await conn.fetch(
            "SELECT node_id, tag_id FROM node_tags WHERE node_id = ANY($1)", node_ids
        )
        for t in trows:
            tag_values[t["node_id"]].append(t["tag_id"])

    buckets: dict[tuple, dict] = {}
    for nid in node_ids:
        dims: list[list] = []
        for key in body.group_by:
            dims.append(group_values[nid].get(key) or [None])
        if body.group_by_tag:
            dims.append(tag_values[nid] or [None])

        combos = product(*dims) if dims else [()]
        metric_vals = metric_map[nid]
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
            bucket["values"].extend(metric_vals)

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

    from tc.auth.permissions import can_see_node

    visible = []
    for r in rows:
        if user is None:
            if r["visibility"] != "public":
                continue
        elif not can_see_node(
            user.get("roles", []),
            r["visibility"],
            r["creator_sub"],
            user["sub"],
        ):
            continue
        visible.append(r)

    if not visible:
        return {"items": []}

    vis_ids = [r["id"] for r in visible]
    tag_rows = await conn.fetch(
        "SELECT node_id, tag_id FROM node_tags WHERE node_id = ANY($1)", vis_ids
    )
    tag_map: dict = {nid: [] for nid in vis_ids}
    for t in tag_rows:
        tag_map.setdefault(t["node_id"], []).append(t["tag_id"])

    return {
        "items": [
            {
                "id": r["id"],
                "title": r["title"],
                "description": r["description"],
                "content": r["content"],
                "data_type": r["content_type"],
                "updated_at": r["updated_at"],
                "tag_ids": tag_map.get(r["id"], []),
                "creator_name": r["creator_name"],
                "creator_sub": r["creator_sub"],
                "status": r["status"],
                "visibility": r["visibility"],
            }
            for r in visible
        ]
    }
