import os
import asyncpg
from typing import List, Tuple

# Глобальный пул соединений
pool: asyncpg.pool.Pool | None = None

async def init_pool():
    """Инициализация пула соединений. Вызывать один раз при старте приложения"""
    global pool
    if pool is None:
        pool = await asyncpg.create_pool(
            host=os.getenv("DB_HOST"),
            port=int(os.getenv("DB_PORT", 5432)),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASS"),
            min_size=1,
            max_size=10
        )

async def get_connection() -> asyncpg.Connection:
    """Получить соединение из пула"""
    if pool is None:
        raise RuntimeError("Connection pool is not initialized. Call init_pool() first.")
    return await pool.acquire()

async def release_connection(conn: asyncpg.Connection):
    """Вернуть соединение в пул"""
    if pool is None:
        return
    await pool.release(conn)

# Асинхронный fetch всех результатов
async def fetch_all(query: str, *params):
    conn = await get_connection()
    try:
        return await conn.fetch(query, *params)
    finally:
        await release_connection(conn)

# Асинхронный execute для вставки/обновления
async def execute(query: str, *params):
    conn = await get_connection()
    try:
        return await conn.execute(query, *params)
    finally:
        await release_connection(conn)

# Асинхронный batch execute
async def execute_batch(query: str, list_of_params: List[Tuple]):
    conn = await get_connection()
    try:
        await conn.executemany(query, list_of_params)
    finally:
        await release_connection(conn)