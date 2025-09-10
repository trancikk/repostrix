import asyncio
import logging
import sys

from sqlalchemy import text

from config import settings
from db.database import engine
from bot import start_bot


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
    await start_bot()

asyncio.run(test_bot())