from fastapi import APIRouter, Depends
from asyncpg.connection import Connection
from metahub.db.connection import get_db
from metahub.models.tags import TagCreateUpdate, TagRead
from metahub.models.clients import CategoryRead

router = APIRouter()

@router.get("/tags", response_model=list[TagRead])
async def get_tags_of(category_id: int, conn: Connection=Depends(get_db)):
    rows = await conn.fetch("SELECT id, name, exposed, category_id FROM tags WHERE category_id=$1", category_id)
    return [TagRead(id=r['id'], name=r['name'], category_id=r['category_id'], exposed=r['exposed']) for r in rows]

@router.post("/tags", response_model=TagRead)
async def add_tag_for(category_id: int, tag: TagCreateUpdate, conn: Connection=Depends(get_db)):
    result = await conn.fetchrow("INSERT INTO tags (name, category_id, exposed) VALUES ($1, $2, $3) RETURNING id", tag.name, category_id, tag.exposed)
    if result is None:
        raise Exception("Failed to add tag")
    return TagRead(id=result["id"], name=tag.name, category_id=category_id, exposed=tag.exposed)

@router.delete("/tags/{tag_id}")
async def delete_tag(tag_id: int, conn: Connection=Depends(get_db)):
    await conn.execute("DELETE FROM tags WHERE id=$1", tag_id)

@router.patch("/tags/{tag_id}")
async def modify_tag(tag_id: int, tag: TagCreateUpdate, conn: Connection=Depends(get_db)):
    await conn.execute("UPDATE tags SET name=$1, exposed=$2 WHERE id=$3", tag.name, tag.exposed, tag_id)

@router.patch("/tags/{tag_id}/dependencies")
async def set_tag_dependencies(tag_id: int, parent_tag_id: int, dependents_ids: list[int], conn: Connection=Depends(get_db)):
    raise NotImplementedError("Tag dependencies not implemented yet")

@router.get("/tags/{tag_id}/children", response_model=list[int])
async def get_tag_children(tag_id: int, conn: Connection=Depends(get_db)):
    rows = await conn.fetch("SELECT tag_id FROM tag_relations WHERE dependent_tag_id=$1", tag_id)
    return [r['tag_id'] for r in rows]