"""
Handle push actions from clients.
"""

from uuid import UUID
from fastapi import APIRouter, Depends
from asyncpg.connection import Connection
from tc.db.connection import get_db

router = APIRouter(prefix="/nodes")

"""
What are the keys
-----------------
    credentials : list[str]
        The identifier of a user, can be:
        - ("local", user_id)
        - ("keycloak", user_id)
        - creator_signature

    access_key : str
        The key used by client to authorize himself.
        However, this key is public, shown in configuration.
        Then why is the key needed, instead of just verify credentials?

        (not so reasonable but)
        Assuming user will copy previous work as template for current work.
        The access_key will be automatically reset while copying.
        And if user doesn't fill in correct access_key, the push will fail.

    validate_key : str
        Validate key is auto generated in backend for each resource.
        And only shown to user once.

        hash(credentials + validate_key) => access_key
"""

def calc_accesskey(credentials: list[str], validate_key: str) -> str:
    return "calc-access-key"

@router.put("/{node_id}/push/data")
async def push2node(node_id: UUID, credentials: list[str], access_key: str, data: object, mode: str):
    creator_signature = "xxxx"
    if hash(credentials)!=creator_signature:
        raise Exception("You are not authorized to push to this node.")
    if is_frozen(node_id):
        raise Exception("Node is frozen, cannot be changed.")
    if not (validate_key := fetch_valkey(node_id)):
        raise Exception("`validate_key` is not set for this node.")
    if access_key!=calc_accesskey(credentials, validate_key):
        raise Exception("`access_key` failed to validate.")
    
    if mode=="w":
        overwrite(node_id, data)
    elif mode=="a":
        append(node_id, data)
    else:
        raise Exception("Unknown push mode.")
    
    return 200

@router.post("/{node_id}/push/valkey")
async def reset_valkey(node_id: UUID) -> str:
    return "new-validate-key"