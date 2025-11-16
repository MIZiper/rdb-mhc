from fastapi import APIRouter, Depends
from metahub.db.connection import get_db

router = APIRouter()

@router.get("/tags")
async def get_tags():
    pass