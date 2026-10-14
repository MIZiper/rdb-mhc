"""Apply the consolidated SQL schema."""

from __future__ import annotations

import logging
from pathlib import Path

from asyncpg.connection import Connection

logger = logging.getLogger(__name__)

_SCHEMA_FILE = Path(__file__).resolve().parent / "schema.sql"


async def ensure_schema(conn: Connection) -> None:
    """Apply ``schema.sql`` (idempotent).

    Tolerant of a read-only database: logs and returns instead of breaking
    startup.
    """
    try:
        await conn.execute(_SCHEMA_FILE.read_text())
    except Exception as exc:  # noqa: BLE001 - startup must not crash
        logger.warning("Could not ensure database schema: %s", exc)
