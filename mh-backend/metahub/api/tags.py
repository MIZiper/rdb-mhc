from fastapi import APIRouter, Depends
from asyncpg.connection import Connection
from metahub.db.connection import get_db
from metahub.models.tags import Tag
from metahub.models.clients import Category

router = APIRouter()

async def get_tags_of(category: Category, conn: Connection=Depends(get_db)):
    pass

async def add_tag_for(category: Category, conn: Connection=Depends(get_db)):
    ...

async def modify_tag(tag: Tag, conn: Connection=Depends(get_db)):
    ...