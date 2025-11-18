from fastapi import APIRouter, Depends
from asyncpg.connection import Connection
from metahub.models.clients import Category, Client
from metahub.db.connection import get_db

router = APIRouter()

async def register_client(client: Client, conn: Connection=Depends(get_db)):
    ...

async def get_clients(conn: Connection=Depends(get_db)):
    ...

async def register_category(client: Client, conn: Connection=Depends(get_db)):
    ...

async def get_categories_of(client: Client, conn: Connection=Depends(get_db)):
    ...
