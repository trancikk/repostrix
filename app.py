import asyncio
import logging
import sys

from sqlalchemy import text

from config import settings
from db.database import engine, get_session
from bot import BotWrapper
from db.repo import create_post
from dto import AssetDto

if settings.dev_mode:
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s - [%(levelname)s] - %(filename)s:%(lineno)d - %(funcName)s() - PID: %(process)d - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        stream=sys.stdout)

else:
    logging.basicConfig(filename='logs/chastify.log', filemode='a',
                        level=logging.DEBUG,
                        format='%(asctime)s - [%(levelname)s] - %(filename)s:%(lineno)d - %(funcName)s() - PID: %(process)d - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')


async def test():
    async with engine.connect() as conn:
        result = await conn.execute(text("select now()"))
        for row in result:
            print(row)

async def test_bot():
    bot = BotWrapper()
    await bot.start_bot()

async def test3():
    async with get_session() as session:
        assets = [AssetDto(url = "test")]
        await create_post(session, [])
        await session.commit()
asyncio.run(test_bot())