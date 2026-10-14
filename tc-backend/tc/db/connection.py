"""asyncpg connection pool lifecycle."""

from __future__ import annotations

import json
from typing import AsyncGenerator

import asyncpg
from asyncpg.connection import Connection

from tc.settings import settings

pool: asyncpg.Pool | None = None


async def _init_connection(conn: Connection) -> None:
    await conn.set_type_codec(
        "jsonb",
        encoder=json.dumps,
        decoder=json.loads,
        schema="pg_catalog",
    )


async def init_pool() -> None:
    global pool
    pool = await asyncpg.create_pool(
        user=settings.postgres_user,
        password=settings.postgres_password,
        database=settings.postgres_db,
        host=settings.postgres_host,
        port=settings.postgres_port,
        init=_init_connection,
    )


async def close_pool() -> None:
    global pool
    if pool is not None:
        await pool.close()
        pool = None


async def get_db() -> AsyncGenerator[Connection, None]:
    if pool is None:
        raise RuntimeError("Database pool is not initialized")
    async with pool.acquire() as conn:
        yield conn
