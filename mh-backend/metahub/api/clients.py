from fastapi import APIRouter, Depends
from asyncpg.connection import Connection
from metahub.models.clients import Category, Client
from metahub.db.connection import get_db

router = APIRouter()

@router.post("/clients", response_model=Client)
async def register_client(client: Client, conn: Connection=Depends(get_db)):
    result = await conn.execute("INSERT INTO clients (name) VALUES ($1)", client.id)

@router.get("/clients", response_model=list[Client])
async def get_clients(conn: Connection=Depends(get_db)):
    rows = await conn.fetchmany("SELECT id, name FROM clients")
    return [Client(id=r.id, name=r.name) for r in rows]

@router.delete("/clients/{client_id}")
async def delete_client(client: Client, conn: Connection=Depends(get_db)):
    pass

@router.post("/clients/{client_id}/categories")
async def register_category(client: Client, category: Category, conn: Connection=Depends(get_db)):
    result = await conn.execute("INSERT INTO categories (name, client_id) VALUES ($1, $2)", category.name, client.id)

@router.get("/clients/{client_id}/categories", response_model=list[Category])
async def get_categories_of(client: Client, conn: Connection=Depends(get_db)):
    rows = await conn.fetchmany("SELECT id, name, client_id FROM categories WHERE client_id=$1", (client.id,))
    return [Category(id=r.id, name=r.name, client=r.client_id) for r in rows]

@router.delete("/clients/{client_id}/categories/{category_id}")
async def delete_category(client: Client, category: Category, conn: Connection=Depends(get_db)):
    pass

@router.patch("/clients/{client_id}/categories/{category_id}")
async def modify_category(client: Client, category: Category, conn: Connection=Depends(get_db)):
    pass