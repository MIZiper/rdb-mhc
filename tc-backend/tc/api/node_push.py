from uuid import UUID
import hashlib
import secrets
from fastapi import APIRouter, Depends, HTTPException, Body, status
from asyncpg.connection import Connection
from tc.db.connection import get_db
from tc.auth.keycloak import get_current_user, get_optional_user

router = APIRouter(prefix="/nodes")


def generate_validate_key() -> str:
    return secrets.token_hex(10)


@router.put("/{node_id}/push/data")
async def push_to_node(
    node_id: UUID,
    data: dict = Body(...),
    mode: str = Body("w"),
    conn: Connection = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    node = await conn.fetchrow(
        """SELECT id, creator_sub, frozen, validate_key, content
           FROM nodes WHERE id=$1""",
        node_id,
    )
    if node is None:
        raise HTTPException(status_code=404, detail="Node not found")

    creator_sub = node["creator_sub"]
    if creator_sub:
        if creator_sub != user["sub"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to push to this node.",
            )

    if node["frozen"]:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Node is frozen, cannot be changed.",
        )

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
    node_id: UUID,
    conn: Connection = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    existing = await conn.fetchrow(
        "SELECT id, creator_sub FROM nodes WHERE id=$1", node_id
    )
    if existing is None:
        raise HTTPException(status_code=404, detail="Node not found")

    if existing["creator_sub"] is not None and existing["creator_sub"] != user["sub"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the creator can reset the validate key",
        )

    new_key = generate_validate_key()
    result = await conn.execute(
        "UPDATE nodes SET validate_key=$1 WHERE id=$2",
        new_key,
        node_id,
    )
    if result == "UPDATE 0":
        raise HTTPException(status_code=404, detail="Node not found")
    return {"validate_key": new_key}
