import asyncio
import logging
from collections import defaultdict
from datetime import timezone, datetime, timedelta

from aiogram.utils.media_group import MediaGroupBuilder
from scheduler.asyncio import Scheduler
from sqlalchemy.ext.asyncio import AsyncSession

from bot import BotWrapper
from db.database import session_maker
from db.models import PostStatus, Post
from db.repo import find_post_with_target_channels, update_post_status, find_expired_posts
from utils import every_minute_at_0

scheduler = None | Scheduler
jobs = defaultdict(list)


async def send_post(session: AsyncSession, bot_wrapper: BotWrapper, post: Post):
    if post.is_album:
        media_group_bd = MediaGroupBuilder(caption=post.text)
        for asset in post.assets:
            # TODO handle different types of content video\photo\etc
            media_group_bd.add(type='photo', media=asset.file_id)
        for chat in post.target_chats:
            await bot_wrapper.send_media_group(chat_id=chat.id, media=media_group_bd.build())
    else:
        for chat in post.target_chats:
            await bot_wrapper.copy_message(post.source_message_id, post.source_chat_id,
                                           chat.id)
    await update_post_status(session, post.id, PostStatus.POSTED)
    await session.commit()


async def schedule_message(bot_wrapper: BotWrapper, post_id: int):
    # TODO kludge for scheduler creation as it needs a running event loop and connot be created during import
    global scheduler
    async with session_maker() as session:
        existing_post = await find_post_with_target_channels(session, post_id)
        if existing_post is not None and len(existing_post) > 0 and scheduler is not None:
            for post in existing_post:
                logging.info(f"Scheduling post {post.post_id} to be sent at {post.scheduled_at}")
                pending_jobs = jobs[post.post_id]
                if pending_jobs is not None:
                    logging.info(f"Found pending jobs for post {post.post_id}, rescheduling...")
                    for job in pending_jobs:
                        scheduler.cancel(job)
                job = scheduler.once(post.scheduled_at, send_post, args=(session, bot_wrapper, post))
                jobs[post.post_id].append(job)


async def run_schedule_service(bot_wrapper: BotWrapper):
    async def run_service():
        logging.info("Checking expired posts...")
        async with session_maker() as session:
            expired_posts = await find_expired_posts(session)
            logging.info(f"Found {len(expired_posts)} expired posts")
            for post in expired_posts:
                await send_post(session, bot_wrapper, post)

    while True:
        now = datetime.now()
        next_minute = (now.replace(second=0, microsecond=0) + timedelta(minutes=1))
        await asyncio.sleep((next_minute - now).total_seconds())
        await run_service()
# global scheduler
# scheduler = Scheduler(tzinfo=timezone.utc)
# def run_loop():
#     while True:
#         scheduler.
#         time.sleep(1)

# t = Thread(target=run_loop, daemon=True)
# t.start()
# TODO kludge to wait for bot to start
# await asyncio.sleep(3)
