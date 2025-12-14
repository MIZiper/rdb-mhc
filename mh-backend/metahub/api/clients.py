from fastapi import APIRouter, Depends
from asyncpg.connection import Connection
from metahub.models.clients import CategoryRead, ClientCreateUpdate, ClientRead, CategoryCreateUpdate
from metahub.db.connection import get_db

router = APIRouter()

@router.post("/clients", response_model=ClientRead)
async def register_client(client: ClientCreateUpdate, conn: Connection=Depends(get_db)):
    result = await conn.fetchrow("INSERT INTO clients (name, host) VALUES ($1, $2) RETURNING id", client.name, client.host)
    if result is None:
        raise Exception("Failed to register client")
    return ClientRead(id=result["id"], name=client.name, host=client.host)

@router.get("/clients", response_model=list[ClientRead])
async def get_clients(conn: Connection=Depends(get_db)):
    rows = await conn.fetch("SELECT id, name, host FROM clients")
    return [ClientRead(id=r['id'], name=r['name'], host=r['host']) for r in rows]

@router.delete("/clients/{client_id}")
async def delete_client(client_id: int, conn: Connection=Depends(get_db)):
    await conn.execute("DELETE FROM clients WHERE id=$1", client_id)

@router.post("/clients/{client_id}/categories", response_model=CategoryRead)
async def register_category(client_id: int, category: CategoryCreateUpdate, conn: Connection=Depends(get_db)):
    result = await conn.fetchrow("INSERT INTO categories (name, client_id) VALUES ($1, $2) RETURNING id", category.name, client_id)
    if result is None:
        raise Exception("Failed to register category")
    return CategoryRead(id=result["id"], name=category.name, client_id=client_id)

@router.get("/clients/all/categories", response_model=list[CategoryRead])
async def get_all_categories(conn: Connection=Depends(get_db)):
    rows = await conn.fetch("SELECT id, name, client_id FROM categories")
    return [CategoryRead(id=r['id'], name=r['name'], client_id=r['client_id']) for r in rows]

@router.get("/clients/{client_id}/categories", response_model=list[CategoryRead])
async def get_categories_of(client_id: int, conn: Connection=Depends(get_db)):
    rows = await conn.fetch("SELECT id, name, client_id FROM categories WHERE client_id=$1", client_id)
    return [CategoryRead(id=r['id'], name=r['name'], client_id=r['client_id']) for r in rows]

@router.delete("/clients/{client_id}/categories/{category_id}")
async def delete_category(client_id: int, category_id: int, conn: Connection=Depends(get_db)):
    await conn.execute("DELETE FROM categories WHERE id=$1 AND client_id=$2", category_id, client_id)

@router.patch("/clients/{client_id}/categories/{category_id}")
async def modify_category(client_id: int, category_id: int, category: CategoryCreateUpdate, conn: Connection=Depends(get_db)):
    await conn.execute("UPDATE categories SET name=$1 WHERE id=$2 AND client_id=$3", category.name, category_id, client_id)