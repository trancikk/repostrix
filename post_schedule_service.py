import asyncio
import logging
from datetime import datetime, timedelta

from aiogram.utils.media_group import MediaGroupBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from bot import BotWrapper
from db.database import session_maker
from db.models import PostStatus, Post
from db.repo import find_expired_posts
from utils import get_now, nvl


async def send_post(session: AsyncSession, bot_wrapper: BotWrapper, post: Post):
    # TODO might be time delay due to sending latency, to think if that might be an issue
    now = get_now()
    post_is_sent = False
    logging.info("About to send post.id: %s", post.id)
    if post.is_album:
        media_group_bd = MediaGroupBuilder(caption=post.text)
        for asset in post.assets:
            # TODO handle different types of content video\photo\etc
            media_group_bd.add(type='photo', media=asset.file_id)

        for chat in post.target_chats:
            next_fire_dt = nvl(now, chat.next_fire_time, post.source_chat.next_fire_time)
            if next_fire_dt > now:
                continue
            logging.info("Sending album post.id %s to channel.id %s, fire time was %s", post.id, chat.id, next_fire_dt)
            await bot_wrapper.send_media_group(chat_id=chat.id, media=media_group_bd.build())
            chat.last_posted_at = now
            post_is_sent = True
    else:
        for chat in post.target_chats:
            next_fire_dt = nvl(now, chat.next_fire_time, post.source_chat.next_fire_time)
            if next_fire_dt > now:
                continue
            logging.info("Sending post %s to channel %s, fire time was %s", post.id, chat.id, next_fire_dt)
            await bot_wrapper.copy_message(post.source_message_id, post.source_chat_id,
                                           chat.id)
            chat.last_posted_at = get_now()
            post_is_sent = True
    # TODO post should be 'posted' if it was posted at least to some channels (currently its updated even if its not posted)
    # TODO fixed with a flag kludge for now
    if post_is_sent:
        logging.info("Sent post.id %s, updating statuses...", post.id)
        post.status = PostStatus.POSTED
        post.posted_at = now
        post.source_chat.last_posted_at = now
    await session.commit()


async def run_schedule_service(bot_wrapper: BotWrapper):
    async def run_service():
        logging.info("Checking expired posts...")
        async with session_maker() as session:
            expired_posts = await find_expired_posts(session)
            logging.info(f"Found {len(expired_posts)} expired posts")
            # TODO make it parallel
            for post in expired_posts:
                await send_post(session, bot_wrapper, post)

    while True:
        now = datetime.now()
        next_minute = (now.replace(second=0, microsecond=0) + timedelta(minutes=1))
        await asyncio.sleep((next_minute - now).total_seconds())
        await run_service()
