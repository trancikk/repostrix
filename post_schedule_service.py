import asyncio
import logging
from datetime import timezone

from scheduler.asyncio import Scheduler
from sqlalchemy.ext.asyncio import AsyncSession

from bot import BotWrapper
from db.database import session_maker
from db.models import PostStatus
from db.repo import find_post_with_target_channels, update_post_status, find_expired_posts

scheduler = None | Scheduler


async def send_post(session: AsyncSession, bot_wrapper: BotWrapper, post):
    await bot_wrapper.copy_message(post.source_message_id, post.source_chat_id,
                                   post.target_chat_id)
    await update_post_status(session, post.post_id, PostStatus.POSTED)
    await session.commit()


async def schedule_message(bot_wrapper: BotWrapper, post_id: int):
    # TODO kludge for scheduler creation as it needs a running event loop and connot be created during import
    global scheduler
    async with session_maker() as session:
        existing_post = await find_post_with_target_channels(session, post_id)
        if existing_post is not None and len(existing_post) > 0:
            for post in existing_post:
                logging.info(f"Scheduling post {post.post_id} to be sent at {post.scheduled_at}")
                scheduler.once(post.scheduled_at, send_post, args=(session, bot_wrapper, post))


async def run_schedule_service(bot_wrapper: BotWrapper):
    global scheduler
    scheduler = Scheduler(tzinfo=timezone.utc)
    # def run_loop():
    #     while True:
    #         scheduler.
    #         time.sleep(1)

    # t = Thread(target=run_loop, daemon=True)
    # t.start()
    # TODO kludge to wait for bot to start
    await asyncio.sleep(3)
    logging.info("Checking expired posts...")
    async with session_maker() as session:
        expired_posts = await find_expired_posts(session)
        logging.info(f"Found {len(expired_posts)} expired posts")
        for post in expired_posts:
            await send_post(session, bot_wrapper, post)
