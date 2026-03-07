import os
import asyncpg
import asyncio

'''
1) Establish connection to the database
2) Take environmental variables from .env file located on the server and use 
these values as credentials
3) Wrap the connection parameters into GET_CONNECTION function for reiteration
'''
async def get_connection():
    return await asyncpg.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", 5432)),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS")
    )

# Асинхронный fetch всех результатов
async def fetch_all(query, *params):
    conn = await get_connection()
    try:
        return await conn.fetch(query, *params)
    finally:
        await conn.close()

# Асинхронный execute для вставки/обновления
async def execute(query, *params):
    conn = await get_connection()
    try:
        await conn.execute(query, *params)
    finally:
        await conn.close()

# Пример батч-вставки
async def execute_batch(query, list_of_params):
    conn = await get_connection()
    try:
        # asyncpg поддерживает executemany
        await conn.executemany(query, list_of_params)
    finally:
        await conn.close()