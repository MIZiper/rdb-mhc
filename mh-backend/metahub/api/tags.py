from fastapi import APIRouter, Depends
from asyncpg.connection import Connection
from metahub.db.connection import get_db
from metahub.models.tags import Tag
from metahub.models.clients import Category

router = APIRouter()

async def get_tags_of(category: Category, conn: Connection=Depends(get_db)):
    rows = await conn.fetchmany("SELECT id, name, is_exposed, category_id FROM tags WHERE category_id=$1", category.id)
    return [Tag(id=r.id, name=r.name, category=r.category_id, is_exposed=r.is_exposed) for r in rows]

async def add_tag_for(category: Category, tag: Tag, conn: Connection=Depends(get_db)):
    result = await conn.execute("INSERT INTO tags (name, category_id) VALUES ($1, $2)", tag.name, category.id)

async def modify_tag(tag: Tag, conn: Connection=Depends(get_db)):
    result = await conn.execute("UPDATE tags SET name=$1, is_exposed=$2 WHERE id=$3", tag.name, tag.is_exposed, tag.id)

async def set_tag_dependencies(tag: Tag, parent_tag: Tag, dependents: list[Tag], conn: Connection=Depends(get_db)):
    result = await conn.execute()