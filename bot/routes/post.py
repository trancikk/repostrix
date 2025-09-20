import logging

from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import ChatStatus, PostStatus
from db.repo import create_or_update_post_from_message, update_post_schedule, find_channel_by_id, find_post
from utils import get_not_empty_string

CANCEL_REPOSTING = 'cancel'

time_table = {
    "Cancel reposting": CANCEL_REPOSTING,
    "Next 1 mins": 1 / 60,
    "Next 5 mins": 1 / 12,
    "Next 10 mins": 1 / 6,
    "Next 30 mins": 1 / 2,
    "Next 2 hours": 2,
    "Next 3 hours": 3,
    "Next 4 hours": 4,
    "Next 6 hours": 6,
    "Next 12 hours": 12,
    "Next day": 24,
}

post_router = Router(name="post")
posts_to_save_filter = (F.text | F.video | F.audio | F.photo | F.caption | F.media_group_id) & ~F.text.startswith("/")


def get_time_table_kb(post_id: int):
    builder = InlineKeyboardBuilder()
    for i, v in time_table.items():
        builder.button(text=i, callback_data=f"schedule_post:{post_id}-{v}")
    builder.adjust(2)
    return builder.as_markup()


@post_router.message(posts_to_save_filter)
@post_router.edited_message(posts_to_save_filter)
async def save_message(message: Message, session: AsyncSession, album: list[Message]) -> None:
    source_chat = await find_channel_by_id(session, message.chat.id)
    # TODO if possible and if i need to implement a custom filter
    if source_chat is not None and source_chat.status == ChatStatus.ENABLED:
        photos = [item.photo[-1].file_id for item in album]
        text = get_not_empty_string(message.html_text, message.caption)
        created_post, is_update = await create_or_update_post_from_message(session,
                                                                           source_message_id=message.message_id,
                                                                           author_id=message.from_user.id,
                                                                           source_chat_id=message.chat.id, text=text,
                                                                           files=photos,
                                                                           is_album=len(photos) > 0)
        if is_update:
            logging.info(f"Update post.id: %s from chat.name (%s), chat.id: %s", created_post.id, message.chat.title,
                         message.chat.id)
        else:
            logging.info(f"Created post.id: %s from chat.name (%s), chat.id: %s", created_post.id, message.chat.title,
                         message.chat.id)
        await message.reply("Post saved. What time do you want to post it? Default your group or channel preferences",
                            reply_markup=get_time_table_kb(created_post.id))


@post_router.callback_query(F.data.startswith('schedule_post'))
async def handle_schedule_update(callback_data: CallbackQuery, session: AsyncSession):
    try:
        data = callback_data.data.split(':')[-1]
        await callback_data.answer('Processing...')
        if data is not None:
            post_id, delta = data.split('-')
            if post_id is not None and delta is not None:
                if delta == CANCEL_REPOSTING:
                    post = await find_post(session, int(post_id))
                    if post is not None:
                        post.status = PostStatus.CANCELLED
                        return await callback_data.message.answer('Cancelled this post',
                                                                  reply_to_message_id=post.source_message_id)
                updated_post = await update_post_schedule(session, int(post_id), float(delta))
                if updated_post is not None:
                    logging.info(f"Scheduled post {post_id} to {updated_post.scheduled_at}")
                    return await callback_data.message.answer(
                        f"Scheduled post will be posted in the next {delta} hours")
    except Exception as e:
        logging.error(f"Error during schedule callback handling: {e}")
        logging.exception(e)
        await callback_data.message.answer(f"Something went wrong.")
