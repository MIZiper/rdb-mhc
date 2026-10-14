"""Type descriptor endpoints.

Descriptors are seeded from code into the ``data_types`` table on startup;
this router serves them to the frontend so it can build its renderer registry
and know which fields are searchable/aggregatable.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from asyncpg.connection import Connection

from tc.db.connection import get_db
from tc.types.registry import all_descriptors, get_descriptor

router = APIRouter(prefix="/types")

_COLUMNS = '"type", display_name, version, "schema", fields, preview, ui, enabled'


def _row_to_dict(row) -> dict:
    return {
        "type": row["type"],
        "display_name": row["display_name"],
        "version": row["version"],
        "schema": row["schema"],
        "fields": row["fields"],
        "preview": row["preview"],
        "ui": row["ui"],
        "enabled": row["enabled"],
    }


@router.get("")
async def list_types(conn: Connection = Depends(get_db)):
    try:
        rows = await conn.fetch(
            f'SELECT {_COLUMNS} FROM data_types WHERE enabled ORDER BY "type"'
        )
    except Exception:  # noqa: BLE001 - table may not be migrated yet
        rows = []
    if not rows:
        return [d.to_dict() for d in all_descriptors()]
    return [_row_to_dict(r) for r in rows]


@router.get("/{type_name}")
async def get_type(type_name: str, conn: Connection = Depends(get_db)):
    try:
        row = await conn.fetchrow(
            f'SELECT {_COLUMNS} FROM data_types WHERE "type"=$1', type_name
        )
    except Exception:  # noqa: BLE001
        row = None
    if row is not None:
        return _row_to_dict(row)
    descriptor = get_descriptor(type_name)
    if descriptor is None:
        raise HTTPException(status_code=404, detail="Unknown data type")
    return descriptor.to_dict()
