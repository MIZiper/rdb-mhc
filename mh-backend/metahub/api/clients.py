from fastapi import APIRouter, Depends
from asyncpg.connection import Connection
from metahub.models.clients import Category, Client
from metahub.db.connection import get_db

router = APIRouter()

async def register_client(client: Client, conn: Connection=Depends(get_db)):
    result = await conn.execute("INSERT INTO clients (name) VALUES ($1)", client.id)

async def get_clients(conn: Connection=Depends(get_db)):
    rows = await conn.fetchmany("SELECT id, name FROM clients")
    return [Client(id=r.id, name=r.name) for r in rows]

async def register_category(client: Client, category: Category, conn: Connection=Depends(get_db)):
    result = await conn.execute("INSERT INTO categories (name, client_id) VALUES ($1, $2)", category.name, client.id)

async def get_categories_of(client: Client, conn: Connection=Depends(get_db)):
    rows = await conn.fetchmany("SELECT id, name, client_id FROM categories WHERE client_id=$1", (client.id,))
    return [Category(id=r.id, name=r.name, client=r.client_id) for r in rows]
