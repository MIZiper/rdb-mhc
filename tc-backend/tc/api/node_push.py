from uuid import UUID
import hashlib
import secrets
from fastapi import APIRouter, Depends, HTTPException, Body
from asyncpg.connection import Connection
from tc.db.connection import get_db

router = APIRouter(prefix="/nodes")


def calc_accesskey(credentials: list[str], validate_key: str) -> str:
    combined = "|".join(credentials) + validate_key
    return hashlib.sha256(combined.encode()).hexdigest()[:12]


def generate_validate_key() -> str:
    return secrets.token_hex(10)


def hash_credentials(credentials: list[str]) -> str:
    combined = "|".join(credentials)
    return hashlib.sha256(combined.encode()).hexdigest()[:20]


@router.put("/{node_id}/push/data")
async def push_to_node(
    node_id: UUID,
    credentials: list[str] = Body(...),
    access_key: str = Body(...),
    data: dict = Body(...),
    mode: str = Body("w"),
    conn: Connection = Depends(get_db),
):
    node = await conn.fetchrow(
        "SELECT id, creator_signature, frozen, validate_key, content FROM nodes WHERE id=$1",
        node_id,
    )
    if node is None:
        raise HTTPException(status_code=404, detail="Node not found")

    creator_signature = node["creator_signature"]
    if creator_signature:
        cred_hash = hash_credentials(credentials)
        if cred_hash != creator_signature:
            raise HTTPException(
                status_code=403,
                detail="You are not authorized to push to this node.",
            )

    if node["frozen"]:
        raise HTTPException(status_code=409, detail="Node is frozen, cannot be changed.")

    validate_key = node["validate_key"]
    if not validate_key:
        raise HTTPException(
            status_code=400,
            detail="validate_key is not set for this node. Reset the key first.",
        )

    expected = calc_accesskey(credentials, validate_key)
    if access_key != expected:
        raise HTTPException(status_code=403, detail="access_key failed to validate.")

    if mode == "w":
        await conn.execute(
            "UPDATE nodes SET content=$1, content_type=$2, updated_at=NOW() WHERE id=$3",
            data,
            data.get("type"),
            node_id,
        )
    elif mode == "a":
        existing = node["content"] or {}
        if isinstance(existing, dict) and isinstance(data, dict):
            merged = {**existing, **data}
        elif isinstance(existing, list) and isinstance(data, list):
            merged = existing + data
        else:
            merged = data
        await conn.execute(
            "UPDATE nodes SET content=$1, content_type=$2, updated_at=NOW() WHERE id=$3",
            merged,
            data.get("type"),
            node_id,
        )
    else:
        raise HTTPException(status_code=400, detail="Unknown push mode. Use 'w' or 'a'.")

    return {"status": "ok", "node_id": str(node_id)}


@router.post("/{node_id}/push/valkey")
async def reset_validate_key(
    node_id: UUID, conn: Connection = Depends(get_db)
):
    new_key = generate_validate_key()
    result = await conn.execute(
        "UPDATE nodes SET validate_key=$1 WHERE id=$2",
        new_key,
        node_id,
    )
    if result == "UPDATE 0":
        raise HTTPException(status_code=404, detail="Node not found")
    return {"validate_key": new_key}
