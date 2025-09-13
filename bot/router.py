import logging

from aiogram import Dispatcher, html, F
from aiogram.enums import ChatType
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, ChatMemberUpdated, ChatMemberLeft, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from bot import BotWrapper
from bot.middlewares import DbSessionMiddleware
from db.database import session_maker
from db.models import ChannelType
from db.repo import create_post_from_message, add_new_channel_or_group, remove_channel_or_group, \
    find_channel_by_username_or_id, add_channel_mapping, update_post_schedule, find_post_with_target_channels
from post_schedule_service import schedule_message

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


def get_time_table_kb(post_id: int):
    builder = InlineKeyboardBuilder()
    for i, v in time_table.items():
        builder.button(text=i, callback_data=f"schedule:{post_id}-{v}")
    builder.adjust(3)
    return builder.as_markup()


dp = Dispatcher()
dp.message.middleware(DbSessionMiddleware(session_maker=session_maker))
dp.callback_query.middleware(DbSessionMiddleware(session_maker=session_maker))
dp.chat_member.middleware(DbSessionMiddleware(session_maker=session_maker))
dp.my_chat_member.middleware(DbSessionMiddleware(session_maker=session_maker))


@dp.message(Command('register'))
async def register_new_channel(message: Message, session: AsyncSession):
    if message.chat.type == ChatType.PRIVATE:
        # TODO channel name is hardcoded
        await add_new_channel_or_group(session, message.chat.id, 'direct message', ChannelType.PRIVATE)
        await message.answer(
            "Please note, registering channel directly from this chat will allow you to manage only one channel")
    args = message.text.split(' ')
    if len(args) < 2:
        return await message.reply("Format should be like /register <channel_name> or /register <channel_id>")
    else:
        channel_name_or_id = args[1].strip().replace('@', '').lower()
        existing_channel = await find_channel_by_username_or_id(session, channel_name_or_id)
        if existing_channel is not None:
            # TODO add deeplinking verification
            await add_channel_mapping(session, message.chat.id, existing_channel.id)
            return await message.reply(
                f"Channel {channel_name_or_id} has been mapped to this chat. You can send your posts here")
        else:
            return await message.reply("Please add Bot to admins first to the target channel.")


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """
    This handler receives messages with `/start` command
    """
    # Most event objects have aliases for API methods that can be called in events' context
    # For example if you want to answer to incoming message you can use `message.answer(...)` alias
    # and the target chat will be passed to :ref:`aiogram.methods.send_message.SendMessage`
    # method automatically or call API method directly via
    # Bot instance: `bot.send_message(chat_id=message.chat.id, ...)`
    await message.answer(f"Hello, {html.bold(message.from_user.full_name)}!")


@dp.my_chat_member()
async def register_new_chat(event: ChatMemberUpdated, session: AsyncSession):
    print(event)
    if event.bot.id == event.new_chat_member.user.id:
        chat_type = ChannelType.OTHER
        match event.chat.type:
            case ChannelType.GROUP:
                chat_type = ChannelType.GROUP
            case ChannelType.CHANNEL:
                chat_type = ChannelType.CHANNEL
            case _:
                chat_type = ChannelType.OTHER

        match event.new_chat_member:
            case ChatMemberLeft():
                logging.info(f"Bot removed from chat {event.chat.title} ({event.chat.id}) - {chat_type})")
                await remove_channel_or_group(session, event.chat.id)
            case _:
                logging.info(f"Detected adding to chat {event.chat.title} ({event.chat.id}) - {chat_type}")
                await add_new_channel_or_group(session, event.chat.id, event.chat.title, chat_type, event.chat.username)


# @dp.channel_post()
# async def on_channel_post_handler(message: Message) -> None:
#     print(message)

@dp.message()
async def save_message(message: Message, session: AsyncSession) -> None:
    created_post = await create_post_from_message(session, source_message_id=message.message_id,
                                                  source_chat_id=message.chat.id)
    logging.info(f"Created new post: {created_post} from {message.chat.title} ({message.chat.id})")
    await message.answer("Post saved. What time do you want to post it? Default is next hour",
                         reply_markup=get_time_table_kb(created_post.id))


@dp.callback_query(F.data.startswith('schedule'))
async def handle_schedule_update(callback_data: CallbackQuery, session: AsyncSession, bot_wrapper: BotWrapper) -> None:
    try:
        data = callback_data.data.split(':')[-1]
        if data is not None:
            post_id, delta = data.split('-')
            if post_id is not None and delta is not None:
                updated_post = await update_post_schedule(session, int(post_id), float(delta))
                await session.commit()
                if updated_post is not None:
                    await schedule_message(bot_wrapper, updated_post.id)
                    logging.info(f"Scheduled post {post_id} to {updated_post.scheduled_at}")
                    await callback_data.message.answer(f"Scheduled post will be posted in the next {delta} hours")
    except Exception as e:
        logging.error(f"Error during schedule callback handling: {e}")
        logging.exception(e)
        await callback_data.message.answer(f"Something went wrong.")
