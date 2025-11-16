import asyncpg
from typing import AsyncGenerator

pool = None

async def init_pool():
    global pool

    pool = await asyncpg.create_pool(
        user="postgres",
        password="password",
        database="metahub",
        host="localhost",
    )

async def close_pool():
    global pool

    if pool:
        await pool.close()

async def get_db() -> AsyncGenerator[asyncpg.connection.Connection, None]:
    async with pool.acquire() as conn:
        yield conn