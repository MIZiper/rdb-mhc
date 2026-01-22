"""
Handle push actions from clients.
"""

from fastapi import APIRouter, Depends
from asyncpg.connection import Connection
from tc.db.connection import get_db

router = APIRouter(prefix="/nodes")

def calc_accesskey(credentials: list[str], validate_key: str) -> str:
    return "calc-access-key"

@router.put("/{node_id}/push/data")
async def push2node(node_id: int, credentials: list[str], access_key: str, data: object, mode: str):
    creator_signature = "xxxx"
    return [
        "You are not authorized to push to this node",
        "Node is frozen, cannot be changed",
        "`validate_key` for node is not set",
        "`access_key` failed to validate",
    ]

@router.post("/{node_id}/push/valkey")
async def reset_valkey(node_id: int) -> str:
    return "new-validate-key"