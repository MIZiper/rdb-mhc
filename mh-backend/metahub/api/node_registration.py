from fastapi import APIRouter, Depends, HTTPException
from asyncpg.connection import Connection
from metahub.db.connection import get_db
from metahub.models.nodes import (
    NodeRegistrationCreate,
    NodeRegistrationRead,
    NodeRegistrationList,
)

router = APIRouter(prefix="/nodes")


@router.post("/", response_model=NodeRegistrationRead)
async def register_node(
    data: NodeRegistrationCreate, conn: Connection = Depends(get_db)
):
    existing = await conn.fetchrow(
        "SELECT tag_id FROM registered_nodes WHERE tag_id=$1", data.tag_id
    )
    if existing:
        raise HTTPException(
            status_code=409,
            detail="A node is already registered for this tag. Delete it first.",
        )

    params = {}
    if data.description:
        params["description"] = data.description
    if data.link:
        params["link"] = data.link

    await conn.execute(
        """
        INSERT INTO registered_nodes (tag_id, client_id, client_node_id, node_tag_ids, params)
        VALUES ($1, $2, $3, $4, $5)
        """,
        data.tag_id,
        data.client_id,
        data.client_node_id,
        data.node_tag_ids,
        params,
    )
    return NodeRegistrationRead(
        tag_id=data.tag_id,
        client_id=data.client_id,
        client_node_id=data.client_node_id,
        node_tag_ids=data.node_tag_ids,
        params=params,
    )


@router.get("/", response_model=NodeRegistrationList)
async def list_registered_nodes(
    conn: Connection = Depends(get_db),
    client_id: int | None = None,
):
    if client_id is not None:
        rows = await conn.fetch(
            "SELECT tag_id, client_id, client_node_id, node_tag_ids, params "
            "FROM registered_nodes WHERE client_id=$1 ORDER BY tag_id",
            client_id,
        )
    else:
        rows = await conn.fetch(
            "SELECT tag_id, client_id, client_node_id, node_tag_ids, params "
            "FROM registered_nodes ORDER BY tag_id"
        )

    items = [
        NodeRegistrationRead(
            tag_id=r["tag_id"],
            client_id=r["client_id"],
            client_node_id=r["client_node_id"],
            node_tag_ids=r["node_tag_ids"] or [],
            params=r["params"] or {},
        )
        for r in rows
    ]
    return NodeRegistrationList(items=items, total=len(items))


@router.get("/by-tag/{tag_id}", response_model=NodeRegistrationRead)
async def get_node_by_tag(tag_id: int, conn: Connection = Depends(get_db)):
    row = await conn.fetchrow(
        "SELECT tag_id, client_id, client_node_id, node_tag_ids, params "
        "FROM registered_nodes WHERE tag_id=$1",
        tag_id,
    )
    if row is None:
        raise HTTPException(
            status_code=404,
            detail="No node registered for this tag",
        )
    return NodeRegistrationRead(
        tag_id=row["tag_id"],
        client_id=row["client_id"],
        client_node_id=row["client_node_id"],
        node_tag_ids=row["node_tag_ids"] or [],
        params=row["params"] or {},
    )


@router.delete("/{tag_id}")
async def delete_node_registration(
    tag_id: int, conn: Connection = Depends(get_db)
):
    result = await conn.execute(
        "DELETE FROM registered_nodes WHERE tag_id=$1", tag_id
    )
    if result == "DELETE 0":
        raise HTTPException(
            status_code=404,
            detail="No node registered for this tag",
        )
    return {"status": "deleted"}


@router.patch("/{tag_id}")
async def update_node_registration(
    tag_id: int,
    data: NodeRegistrationCreate,
    conn: Connection = Depends(get_db),
):
    existing = await conn.fetchrow(
        "SELECT tag_id FROM registered_nodes WHERE tag_id=$1", tag_id
    )
    if existing is None:
        raise HTTPException(
            status_code=404,
            detail="No node registered for this tag",
        )

    params = {}
    if data.description:
        params["description"] = data.description
    if data.link:
        params["link"] = data.link

    await conn.execute(
        """
        UPDATE registered_nodes
        SET client_id=$1, client_node_id=$2, node_tag_ids=$3, params=$4
        WHERE tag_id=$5
        """,
        data.client_id,
        data.client_node_id,
        data.node_tag_ids,
        params,
        tag_id,
    )
    return NodeRegistrationRead(
        tag_id=tag_id,
        client_id=data.client_id,
        client_node_id=data.client_node_id,
        node_tag_ids=data.node_tag_ids,
        params=params,
    )
