"""Stored file operations.

Bytes live on disk (``tc.services.files``), metadata in the ``files`` table.
Access follows the visibility of the node a file is linked to.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from asyncpg.connection import Connection

from tc.auth.permissions import ROLE_READ_ALL, can_see_node, check_edit_node
from tc.auth.provider import get_current_user, get_optional_user
from tc.db.connection import get_db
from tc.models.file import FileRead
from tc.services import files as store

router = APIRouter(prefix="/files")

_FILE_COLUMNS = """id, node_id, data_type, original_name, mime_type, size_bytes,
                   width, height, stored_path, thumb_path, creator_name,
                   creator_sub, created_at"""


def _to_read(row) -> FileRead:
    return FileRead(
        id=row["id"],
        node_id=row["node_id"],
        data_type=row["data_type"],
        original_name=row["original_name"],
        mime_type=row["mime_type"],
        size_bytes=row["size_bytes"],
        width=row["width"],
        height=row["height"],
        url=f"/api/files/{row['id']}",
        thumb_url=f"/api/files/{row['id']}/thumb",
        creator_name=row["creator_name"],
        creator_sub=row["creator_sub"],
        created_at=row["created_at"],
    )


async def _can_read(row, conn: Connection, user: Optional[dict]) -> bool:
    if user is None:
        if row["node_id"] is None:
            return False
        visibility = await conn.fetchval(
            "SELECT visibility FROM nodes WHERE id=$1", row["node_id"]
        )
        return visibility == "public"

    roles = user.get("roles", [])
    if ROLE_READ_ALL in roles:
        return True
    if row["creator_sub"] is not None and row["creator_sub"] == user["sub"]:
        return True
    if row["node_id"] is not None:
        node = await conn.fetchrow(
            "SELECT visibility, creator_sub FROM nodes WHERE id=$1", row["node_id"]
        )
        if node and can_see_node(
            roles, node["visibility"], node["creator_sub"], user["sub"]
        ):
            return True
    return False


async def _get_visible_row(file_id: UUID, conn: Connection, user: Optional[dict]):
    row = await conn.fetchrow(f"SELECT {_FILE_COLUMNS} FROM files WHERE id=$1", file_id)
    if row is None or not await _can_read(row, conn, user):
        raise HTTPException(status_code=404, detail="File not found")
    return row


@router.post("", response_model=FileRead)
async def upload_file(
    data_type: str = Query("Image.v00", description="Content type id / storage subfolder"),
    file: UploadFile = File(...),
    conn: Connection = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    if not (file.content_type or "").startswith("image/"):
        raise HTTPException(status_code=415, detail="Only image uploads are supported")

    file_id = uuid4()
    try:
        meta = await store.save_upload(file, data_type, file_id)
    except store.UploadTooLarge as e:
        raise HTTPException(status_code=413, detail=str(e))

    row = await conn.fetchrow(
        f"""INSERT INTO files (id, data_type, original_name, mime_type, size_bytes,
                               width, height, stored_path, thumb_path,
                               creator_sub, creator_name)
           VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)
           RETURNING {_FILE_COLUMNS}""",
        file_id,
        data_type,
        file.filename,
        meta["mime_type"],
        meta["size_bytes"],
        meta["width"],
        meta["height"],
        meta["stored_path"],
        meta["thumb_path"],
        user["sub"],
        user["name"],
    )
    return _to_read(row)


@router.get("/{file_id}")
async def get_file(
    file_id: UUID,
    conn: Connection = Depends(get_db),
    user=Depends(get_optional_user),
):
    row = await _get_visible_row(file_id, conn, user)
    path = store.absolute_path(row["stored_path"])
    if path is None:
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(
        path,
        media_type=row["mime_type"],
        filename=row["original_name"] or None,
        headers={"Cache-Control": "private, max-age=86400"},
    )


@router.get("/{file_id}/thumb")
async def get_file_thumb(
    file_id: UUID,
    conn: Connection = Depends(get_db),
    user=Depends(get_optional_user),
):
    row = await _get_visible_row(file_id, conn, user)
    path = store.absolute_path(row["thumb_path"]) if row["thumb_path"] else None
    if path is None:
        path = store.absolute_path(row["stored_path"])
    if path is None:
        raise HTTPException(status_code=404, detail="File not found")

    suffix = path.suffix.lower()
    if suffix == ".png":
        media_type = "image/png"
    elif suffix in (".jpg", ".jpeg"):
        media_type = "image/jpeg"
    else:
        media_type = row["mime_type"]
    return FileResponse(
        path,
        media_type=media_type,
        headers={"Cache-Control": "private, max-age=86400"},
    )


@router.delete("/{file_id}")
async def delete_file(
    file_id: UUID,
    conn: Connection = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    row = await conn.fetchrow(
        "SELECT id, creator_sub, stored_path, thumb_path FROM files WHERE id=$1",
        file_id,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="File not found")
    check_edit_node(user, row["creator_sub"])

    await conn.execute("DELETE FROM files WHERE id=$1", file_id)
    store.delete_paths(row["stored_path"], row["thumb_path"])
    return {"status": "ok", "id": str(file_id)}
