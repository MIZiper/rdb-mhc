"""Uploaded-file storage and node linking.

Bytes live under ``TC_STORAGE_ROOT`` in a per-type subfolder; the ``files``
table holds metadata. Node content references files through ``file_id`` /
``file_ids`` fields at any depth.
"""

from __future__ import annotations

import mimetypes
import re
from pathlib import Path
from typing import Any, Iterator, Optional
from uuid import UUID

from asyncpg.connection import Connection
from fastapi import UploadFile
from fastapi.concurrency import run_in_threadpool
from PIL import Image, ImageOps

from tc.settings import settings

STORAGE_ROOT = Path(settings.storage_root).resolve()
MAX_UPLOAD_BYTES = settings.max_upload_bytes
THUMB_MAX = 480

_UNSAFE = re.compile(r"[^A-Za-z0-9._-]+")
_UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)


class UploadTooLarge(ValueError):
    pass


def _module_dir(data_type: str) -> str:
    safe = _UNSAFE.sub("_", data_type or "misc").strip("._")
    return safe or "misc"


def _abs(rel_path: str) -> Path:
    return (STORAGE_ROOT / rel_path).resolve()


def _is_within_root(path: Path) -> bool:
    try:
        path.relative_to(STORAGE_ROOT)
        return True
    except ValueError:
        return False


def _ext_from(upload: UploadFile) -> str:
    ext = Path(upload.filename or "").suffix.lower()
    if ext and len(ext) <= 10 and re.fullmatch(r"\.[a-z0-9]+", ext):
        return ext
    guessed = mimetypes.guess_extension(upload.content_type or "")
    return guessed or ".bin"


def _save_stream(fileobj, dest: Path, max_bytes: int) -> int:
    dest.parent.mkdir(parents=True, exist_ok=True)
    size = 0
    try:
        with dest.open("wb") as out:
            while True:
                chunk = fileobj.read(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if size > max_bytes:
                    raise UploadTooLarge(
                        f"File exceeds maximum size of {max_bytes // (1024 * 1024)}MB"
                    )
                out.write(chunk)
    except Exception:
        dest.unlink(missing_ok=True)
        raise
    return size


def _process_image(
    dest: Path, thumb_stem: Path
) -> tuple[Optional[int], Optional[int], Optional[str]]:
    try:
        with Image.open(dest) as im:
            im = ImageOps.exif_transpose(im)
            width, height = im.size
            thumb = im.copy()
            thumb.thumbnail((THUMB_MAX, THUMB_MAX))
            thumb_stem.parent.mkdir(parents=True, exist_ok=True)
            if thumb.mode in ("RGBA", "LA", "P"):
                out = thumb_stem.with_suffix(".png")
                thumb.convert("RGBA").save(out, format="PNG")
            else:
                out = thumb_stem.with_suffix(".jpg")
                thumb.convert("RGB").save(out, format="JPEG", quality=82)
        return width, height, str(out.relative_to(STORAGE_ROOT))
    except Exception:
        return None, None, None


async def save_upload(upload: UploadFile, data_type: str, file_id: UUID) -> dict:
    """Persist an uploaded file plus its thumbnail; return metadata."""
    sub = _module_dir(data_type)
    rel_path = f"{sub}/{file_id}{_ext_from(upload)}"
    dest = _abs(rel_path)
    if not _is_within_root(dest):
        raise ValueError("Invalid storage path")

    size = await run_in_threadpool(_save_stream, upload.file, dest, MAX_UPLOAD_BYTES)
    width, height, thumb_rel = await run_in_threadpool(
        _process_image, dest, _abs(f"{sub}/thumbs/{file_id}")
    )
    return {
        "stored_path": rel_path,
        "thumb_path": thumb_rel,
        "size_bytes": size,
        "width": width,
        "height": height,
        "mime_type": upload.content_type or "application/octet-stream",
    }


def absolute_path(rel_path: str) -> Optional[Path]:
    path = _abs(rel_path)
    if not _is_within_root(path) or not path.is_file():
        return None
    return path


def delete_paths(*rel_paths: Optional[str]) -> None:
    for rel in rel_paths:
        if not rel:
            continue
        path = _abs(rel)
        if _is_within_root(path):
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass


def _iter_ids(value: Any) -> Iterator[UUID]:
    if isinstance(value, str):
        if _UUID_RE.match(value):
            try:
                yield UUID(value)
            except ValueError:
                return
    elif isinstance(value, list):
        for item in value:
            yield from _iter_ids(item)


def extract_file_ids(content: Any) -> list[UUID]:
    """Collect every ``file_id`` / ``file_ids`` UUID found in content."""
    found: list[UUID] = []
    seen: set[UUID] = set()

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if key in ("file_id", "file_ids"):
                    for fid in _iter_ids(value):
                        if fid not in seen:
                            seen.add(fid)
                            found.append(fid)
                else:
                    walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(content)
    return found


async def link_file_refs(conn: Connection, node_id: UUID, content: Any) -> None:
    """Associate files referenced by content to the given node."""
    ids = extract_file_ids(content)
    if not ids:
        return
    await conn.execute(
        "UPDATE files SET node_id=$1 WHERE id = ANY($2::uuid[])", node_id, ids
    )
