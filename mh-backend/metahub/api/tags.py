from fastapi import APIRouter, Depends, Query, Body
from asyncpg.connection import Connection
from metahub.db.connection import get_db
from metahub.models.tags import TagCreateUpdate, TagRead, TagWithParent, TagExposed
from metahub.models.clients import CategoryRead
from metahub.models.nodes import (
    DeepSearchRequest,
    DeepSearchResult,
    TagDescendant,
)
from metahub.services.tc_client import fetch_tc_nodes_by_tags

router = APIRouter()


@router.get("/tags", response_model=list[TagRead])
async def get_tags_of(category_id: int, conn: Connection = Depends(get_db)):
    rows = await conn.fetch(
        "SELECT id, name, exposed, category_id FROM tags WHERE category_id=$1",
        category_id,
    )
    return [
        TagRead(
            id=r["id"],
            name=r["name"],
            category_id=r["category_id"],
            exposed=r["exposed"],
        )
        for r in rows
    ]


@router.get("/tags/with-parent", response_model=list[TagWithParent])
async def get_tags_with_parent(category_id: int, conn: Connection = Depends(get_db)):
    rows = await conn.fetch(
        "SELECT id, name, exposed, category_id, parent_id FROM tags WHERE category_id = $1",
        category_id,
    )
    return [
        TagWithParent(
            id=r["id"],
            name=r["name"],
            category_id=r["category_id"],
            exposed=r["exposed"],
            parent_id=r["parent_id"],
        )
        for r in rows
    ]


@router.post("/tags", response_model=TagRead)
async def add_tag_for(
    category_id: int, tag: TagCreateUpdate, conn: Connection = Depends(get_db)
):
    result = await conn.fetchrow(
        "INSERT INTO tags (name, category_id, exposed) VALUES ($1, $2, $3) RETURNING id",
        tag.name,
        category_id,
        tag.exposed,
    )
    if result is None:
        raise Exception("Failed to add tag")
    return TagRead(
        id=result["id"], name=tag.name, category_id=category_id, exposed=tag.exposed
    )


@router.post("/tags/search", response_model=list[TagExposed])
async def search_tag_relationships(tag_ids: list[int], conn: Connection=Depends(get_db)):
    rows = await conn.fetch(
        "SELECT id, name, parent_id FROM tags WHERE id=ANY($1)", tag_ids
    )
    return [
        TagExposed(id=r["id"], name=r["name"], parent_id=r["parent_id"])
        for r in rows
    ]


@router.delete("/tags/{tag_id}")
async def delete_tag(tag_id: int, conn: Connection = Depends(get_db)):
    await conn.execute("DELETE FROM tags WHERE id=$1", tag_id)


@router.patch("/tags/{tag_id}")
async def modify_tag(
    tag_id: int, tag: TagCreateUpdate, conn: Connection = Depends(get_db)
):
    await conn.execute(
        "UPDATE tags SET name=$1, exposed=$2 WHERE id=$3", tag.name, tag.exposed, tag_id
    )


@router.patch("/tags/{tag_id}/parent")
async def set_tag_parent(
    tag_id: int, parent_id: int | None, conn: Connection = Depends(get_db)
):
    if parent_id is not None and parent_id == tag_id:
        return
    await conn.execute(
        "UPDATE tags SET parent_id=$1 WHERE id=$2", parent_id, tag_id
    )


@router.get("/tags/{tag_id}/children", response_model=list[int])
async def get_tag_children(tag_id: int, conn: Connection = Depends(get_db)):
    rows = await conn.fetch(
        "SELECT id FROM tags WHERE parent_id=$1", tag_id
    )
    return [r["id"] for r in rows]


@router.get("/tags/{tag_id}/descendants", response_model=list[TagDescendant])
async def get_tag_descendants(tag_id: int, conn: Connection = Depends(get_db)):
    rows = await conn.fetch(
        """
        WITH RECURSIVE descendants AS (
            SELECT id, name, parent_id, 1 AS depth
            FROM tags
            WHERE parent_id = $1
            UNION ALL
            SELECT t.id, t.name, t.parent_id, d.depth + 1
            FROM tags t
            JOIN descendants d ON t.parent_id = d.id
            WHERE d.depth < 100
        )
        SELECT DISTINCT id, name, parent_id FROM descendants ORDER BY id
        """,
        tag_id,
    )
    return [
        TagDescendant(
            id=r["id"],
            name=r["name"],
            parent_id=r["parent_id"],
        )
        for r in rows
    ]


@router.get("/tags/exposed", response_model=list[TagRead])
async def get_exposed_tags(
    category_id: int | None = Query(None),
    conn: Connection = Depends(get_db),
):
    if category_id is not None:
        rows = await conn.fetch(
            "SELECT id, name, exposed, category_id FROM tags "
            "WHERE exposed=TRUE AND category_id=$1",
            category_id,
        )
    else:
        rows = await conn.fetch(
            "SELECT id, name, exposed, category_id FROM tags WHERE exposed=TRUE"
        )
    return [
        TagRead(
            id=r["id"],
            name=r["name"],
            category_id=r["category_id"],
            exposed=r["exposed"],
        )
        for r in rows
    ]


@router.post("/search/expand", response_model=list[int])
async def expand_tag_ids(
    tag_ids: list[int] = Body(...),
    conn: Connection = Depends(get_db),
):
    if not tag_ids:
        return []
    rows = await conn.fetch(
        """
        WITH RECURSIVE descendants AS (
            SELECT id, parent_id FROM tags WHERE parent_id = ANY($1)
            UNION ALL
            SELECT t.id, t.parent_id FROM tags t
            JOIN descendants d ON t.parent_id = d.id
        )
        SELECT DISTINCT id FROM descendants
        UNION
        SELECT unnest($1::int[])
        """,
        tag_ids,
    )
    return sorted(r["id"] for r in rows)


@router.post("/search/deep", response_model=DeepSearchResult)
async def deep_search(
    search: DeepSearchRequest,
    conn: Connection = Depends(get_db),
):
    expanded_tag_ids = list(search.tag_ids)

    if search.include_descendants:
        rows = await conn.fetch(
            """
            WITH RECURSIVE descendants AS (
                SELECT id, parent_id FROM tags WHERE parent_id = ANY($1)
                UNION ALL
                SELECT t.id, t.parent_id FROM tags t
                JOIN descendants d ON t.parent_id = d.id
            )
            SELECT DISTINCT id FROM descendants
            UNION
            SELECT unnest($1::int[])
            """,
            search.tag_ids,
        )
        expanded_tag_ids = sorted(set(r["id"] for r in rows))

    bound_node_ids = []

    if search.include_bound_nodes:
        bound_rows = await conn.fetch(
            """
            SELECT rn.tag_id, rn.client_id, rn.client_node_id, rn.node_tag_ids, rn.params,
                   c.host AS client_host
            FROM registered_nodes rn
            JOIN clients c ON c.id = rn.client_id
            WHERE rn.node_tag_ids && $1::int[]
            """,
            expanded_tag_ids,
        )
        for br in bound_rows:
            bound_node_ids.append({
                "tag_id": br["tag_id"],
                "client_id": br["client_id"],
                "client_host": br["client_host"],
                "client_node_id": str(br["client_node_id"]),
                "node_tag_ids": br["node_tag_ids"] or [],
                "params": br["params"] or {},
            })

    return DeepSearchResult(
        expanded_tag_ids=expanded_tag_ids,
        bound_node_ids=bound_node_ids,
    )


@router.post("/search/deep/nodes")
async def search_deep_nodes(
    search: DeepSearchRequest,
    conn: Connection = Depends(get_db),
):
    expanded_tag_ids = list(search.tag_ids)

    if search.include_descendants:
        rows = await conn.fetch(
            """
            WITH RECURSIVE descendants AS (
                SELECT id, parent_id FROM tags WHERE parent_id = ANY($1)
                UNION ALL
                SELECT t.id, t.parent_id FROM tags t
                JOIN descendants d ON t.parent_id = d.id
            )
            SELECT DISTINCT id FROM descendants
            UNION
            SELECT unnest($1::int[])
            """,
            search.tag_ids,
        )
        expanded_tag_ids = sorted(set(r["id"] for r in rows))

    bound_nodes = {}
    if search.include_bound_nodes:
        bound_rows = await conn.fetch(
            """
            SELECT rn.tag_id, rn.client_id, rn.client_node_id, rn.node_tag_ids, rn.params,
                   c.host AS client_host
            FROM registered_nodes rn
            JOIN clients c ON c.id = rn.client_id
            WHERE rn.node_tag_ids && $1::int[]
            """,
            expanded_tag_ids,
        )
        for br in bound_rows:
            host = br["client_host"]
            if host and host not in bound_nodes:
                nodes = await fetch_tc_nodes_by_tags(
                    host, expanded_tag_ids, mode="exact"
                )
                bound_nodes[host] = nodes

    tc_results = {}
    clients = await conn.fetch("SELECT id, host FROM clients WHERE host IS NOT NULL")
    for client in clients:
        host = client["host"]
        if host:
            nodes = await fetch_tc_nodes_by_tags(
                host, expanded_tag_ids, mode="exact"
            )
            if nodes:
                tc_results[host] = nodes

    return {
        "expanded_tag_ids": expanded_tag_ids,
        "tc_results": tc_results,
        "bound_nodes": bound_nodes,
    }
