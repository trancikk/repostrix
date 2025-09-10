import asyncio

from sqlalchemy import text

from db.database import engine


async def test():
    async with engine.connect() as conn:
        result = await conn.execute(text("select now()"))
        for row in result:
            print(row)

asyncio.run(test())