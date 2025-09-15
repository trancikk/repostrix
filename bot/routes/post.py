import logging

from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from db.repo import create_post_from_message, update_post_schedule
from utils import get_not_empty_string

time_table = {
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


def get_time_table_kb(post_id: int):
    builder = InlineKeyboardBuilder()
    for i, v in time_table.items():
        builder.button(text=i, callback_data=f"schedule_post:{post_id}-{v}")
    builder.adjust(2)
    return builder.as_markup()


@post_router.message(F.text | F.video | F.audio | F.photo | F.caption | F.media_group_id)
async def save_message(message: Message, session: AsyncSession, album: list[Message]) -> None:
    photos = [item.photo[-1].file_id for item in album]
    # TODO store user info to determine whether they are still admin when post is about to be sent
    text = get_not_empty_string(message.html_text, message.caption)
    created_post = await create_post_from_message(session, source_message_id=message.message_id,
                                                  source_chat_id=message.chat.id, text=text, files=photos,
                                                  is_album=len(photos) > 0)
    logging.info(f"Created new post: {created_post} from {message.chat.title} ({message.chat.id})")
    await message.answer("Post saved. What time do you want to post it? Default is next hour",
                         reply_markup=get_time_table_kb(created_post.id))


@post_router.callback_query(F.data.startswith('schedule_post'))
async def handle_schedule_update(callback_data: CallbackQuery, session: AsyncSession) -> None:
    try:
        data = callback_data.data.split(':')[-1]
        if data is not None:
            post_id, delta = data.split('-')
            if post_id is not None and delta is not None:
                updated_post = await update_post_schedule(session, int(post_id), float(delta))
                await session.commit()
                if updated_post is not None:
                    # await schedule_message(bot_wrapper, updated_post.id)
                    logging.info(f"Scheduled post {post_id} to {updated_post.scheduled_at}")
                    await callback_data.message.answer(f"Scheduled post will be posted in the next {delta} hours")
    except Exception as e:
        logging.error(f"Error during schedule callback handling: {e}")
        logging.exception(e)
        await callback_data.message.answer(f"Something went wrong.")
