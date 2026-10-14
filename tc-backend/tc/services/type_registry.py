"""Seed the code-defined type descriptors into the database."""

from __future__ import annotations

import logging
from pathlib import Path

from asyncpg.connection import Connection

from tc.types.registry import all_descriptors

logger = logging.getLogger(__name__)

_SCHEMA_FILE = Path(__file__).resolve().parent.parent / "db" / "03-index-schema.sql"


async def ensure_index_schema(conn: Connection) -> None:
    """Apply the idempotent projection-index DDL.

    Tolerant of a read-only database: logs and returns instead of breaking
    startup. The DDL uses ``IF NOT EXISTS`` throughout so it is safe to run
    on every boot.
    """
    try:
        sql = _SCHEMA_FILE.read_text()
        await conn.execute(sql)
    except Exception as exc:  # noqa: BLE001 - startup must not crash
        logger.warning("Could not ensure index schema: %s", exc)


async def seed_data_types(conn: Connection) -> None:
    """Upsert descriptors and the shared field-key vocabulary.

    Tolerant of a not-yet-migrated database: logs and returns instead of
    breaking startup.
    """
    try:
        for descriptor in all_descriptors():
            payload = descriptor.to_dict()
            await conn.execute(
                """INSERT INTO data_types
                       ("type", display_name, version, "schema", fields, preview, ui, updated_at)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())
                   ON CONFLICT ("type") DO UPDATE SET
                       display_name = EXCLUDED.display_name,
                       version      = EXCLUDED.version,
                       "schema"     = EXCLUDED."schema",
                       fields       = EXCLUDED.fields,
                       preview      = EXCLUDED.preview,
                       ui           = EXCLUDED.ui,
                       updated_at   = NOW()""",
                payload["type"],
                payload["display_name"],
                payload["version"],
                payload["schema"],
                payload["fields"],
                payload["preview"],
                payload["ui"],
            )
            for f in descriptor.fields:
                await conn.execute(
                    """INSERT INTO field_keys (key, kind, unit, label, comparable)
                       VALUES ($1, $2, $3, $4, $5)
                       ON CONFLICT (key) DO UPDATE SET
                           kind       = EXCLUDED.kind,
                           unit       = EXCLUDED.unit,
                           label      = EXCLUDED.label,
                           comparable = EXCLUDED.comparable""",
                    f.key,
                    f.kind,
                    f.unit,
                    f.label or f.key,
                    bool(f.comparable),
                )
    except Exception as exc:  # noqa: BLE001 - startup must not crash
        logger.warning("Skipping type-descriptor seed: %s", exc)
