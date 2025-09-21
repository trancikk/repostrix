import asyncio
import logging
import sys

from bot import BotWrapper, dp
from config import settings
from db.database import session_maker
from post_schedule_service import run_schedule_service

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


async def main():
    bot = BotWrapper()
    await asyncio.gather(bot.start_bot(dp, session_maker), run_schedule_service(bot))


asyncio.run(main())
