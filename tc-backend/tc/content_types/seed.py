"""Seed the code-defined content-type descriptors into the database."""

from __future__ import annotations

import logging

from asyncpg.connection import Connection

from tc.content_types.registry import all_descriptors

logger = logging.getLogger(__name__)


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
            for field in descriptor.fields:
                await conn.execute(
                    """INSERT INTO field_keys (key, kind, unit, label, comparable)
                       VALUES ($1, $2, $3, $4, $5)
                       ON CONFLICT (key) DO UPDATE SET
                           kind       = EXCLUDED.kind,
                           unit       = EXCLUDED.unit,
                           label      = EXCLUDED.label,
                           comparable = EXCLUDED.comparable""",
                    field.key,
                    field.kind,
                    field.unit,
                    field.label or field.key,
                    bool(field.comparable),
                )
    except Exception as exc:  # noqa: BLE001 - startup must not crash
        logger.warning("Skipping content-type seed: %s", exc)
