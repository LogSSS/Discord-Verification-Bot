import asyncpg


async def create_db_pool():
    return await asyncpg.create_pool(
        user='postgres',
        password='1231',
        database='postgres',
        host='localhost'
    )
