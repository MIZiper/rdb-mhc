from fastapi import APIRouter, Depends
from asyncpg.connection import Connection
from tc.db.connection import get_db

router = APIRouter(prefix="nodes")


@router.get("/")
async def get_nodes(conn: Connection = Depends(get_db)):
    raise NotImplementedError
