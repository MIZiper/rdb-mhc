"""Node operation on typed data

The basic implementation for RDB, with typed data.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from typing import Optional
from uuid import UUID
from asyncpg.connection import Connection
from tc.db.connection import get_db
from tc.models import NodeMetaRead, NodeMetaList
from tc.models.typed_node import NodeData, NodeDataRead, NodeDataPayload

router = APIRouter(prefix="/nodes")



@router.get("/types/{data_type}", response_model=NodeMetaList)
async def list_nodes_by_type(
    data_type: str,
    conn: Connection = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, le=100),
):
    offset = (page - 1) * page_size

    sql = """
        SELECT id, title, description, updated_at, content, content_type
        FROM nodes
        WHERE content_type = $1
        ORDER BY updated_at DESC
        LIMIT $2 OFFSET $3
    """
    params = (data_type, page_size, offset)

    count_sql = "SELECT COUNT(*) FROM nodes WHERE content_type = $1"
    count_result = await conn.fetchval(count_sql, data_type)

    nodes_rows = await conn.fetch(sql, *params)
    node_ids = [row["id"] for row in nodes_rows]

    tags_query = """
        SELECT node_id, tag_id
        FROM node_tags
        WHERE node_id = ANY($1)
    """
    tags_rows = await conn.fetch(tags_query, node_ids)

    result_map = {
        r["id"]: NodeMetaRead(
            id=r["id"],
            title=r["title"],
            description=r["description"],
            updated_at=r["updated_at"],
            tag_ids=[],
            data_type=r["content_type"],
        )
        for r in nodes_rows
    }

    for tag_row in tags_rows:
        nid = tag_row["node_id"]
        if nid in result_map:
            result_map[nid].tag_ids.append(tag_row["tag_id"])

    return NodeMetaList(items=[result_map[nid] for nid in node_ids], total=count_result)


@router.get("/{node_id}/data", response_model=NodeDataRead)
async def get_node_data(node_id: UUID, conn: Connection = Depends(get_db)):
    row = await conn.fetchrow(
        "SELECT id, content, content_type, updated_at FROM nodes WHERE id=$1", node_id
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Node not found")

    content = row["content"]
    if content is None or content == {}:
        raise HTTPException(status_code=404, detail="Node has no data")

    return NodeDataRead(
        id=row["id"],
        content=content,
        data_type=row["content_type"],
        updated_at=row["updated_at"],
    )


@router.patch("/{node_id}/data")
async def patch_node_data(
    node_id: UUID,
    updates: dict = Body(..., description="Partial data updates"),
    conn: Connection = Depends(get_db),
):
    row = await conn.fetchrow(
        "SELECT id, content, content_type, updated_at FROM nodes WHERE id=$1", node_id
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Node not found")

    existing_content = row["content"] or {}

    def deep_merge(base: dict, updates: dict) -> dict:
        result = base.copy()
        for key, value in updates.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    merged_content = deep_merge(existing_content, updates)

    try:
        validated_data = NodeData.model_validate(merged_content)
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Invalid data structure after merge: {str(e)}"
        )

    content_dict = validated_data.model_dump()
    updated_row = await conn.fetchrow(
        "UPDATE nodes SET content=$1, content_type=$2, updated_at=NOW() WHERE id=$3 RETURNING updated_at",
        content_dict,
        validated_data.type,
        node_id,
    )

    return NodeDataRead(
        id=node_id,
        content=validated_data,
        data_type=validated_data.type,
        updated_at=updated_row["updated_at"],
    )


@router.post("/{node_id}/data")
async def ingest_node_data(
    node_id: UUID, payload: NodeDataPayload, conn: Connection = Depends(get_db)
):
    existing = await conn.fetchrow("SELECT id FROM nodes WHERE id=$1", node_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Node not found")

    content_dict = payload.content.model_dump()
    row = await conn.fetchrow(
        "UPDATE nodes SET content=$1, content_type=$2, updated_at=NOW() WHERE id=$3 RETURNING updated_at",
        content_dict,
        payload.content.type,
        node_id,
    )

    return NodeDataRead(
        id=node_id,
        content=payload.content,
        data_type=payload.content.type,
        updated_at=row["updated_at"],
    )
