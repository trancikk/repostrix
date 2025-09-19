import logging

from aiogram import Dispatcher, html
from aiogram.enums import ChatType as ChatTypeTelegram
from aiogram.filters import CommandStart
from aiogram.types import Message, ChatMemberUpdated, ChatMemberLeft
from sqlalchemy.ext.asyncio import AsyncSession

from bot.middlewares import DbSessionMiddleware, AlbumMiddleware, SaveUserMiddleware
from db.database import session_maker
from db.models import ChatType
from db.repo import add_new_channel_or_group, remove_channel_or_group

dp = Dispatcher()

# TODO move to setup function outside
dp.message.middleware(DbSessionMiddleware(session_maker=session_maker))
dp.message.middleware(SaveUserMiddleware(session_factory=session_maker))
dp.message.middleware(AlbumMiddleware())
dp.callback_query.middleware(DbSessionMiddleware(session_maker=session_maker))
dp.callback_query.middleware(SaveUserMiddleware(session_factory=session_maker))
dp.chat_member.middleware(DbSessionMiddleware(session_maker=session_maker))
dp.my_chat_member.middleware(DbSessionMiddleware(session_maker=session_maker))


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
    print(event.chat.type)
    print(event)
    if event.bot.id == event.new_chat_member.user.id:
        chat_type = ChatType.OTHER
        match event.chat.type:
            case ChatTypeTelegram.GROUP:
                chat_type = ChatType.GROUP
            case ChatTypeTelegram.CHANNEL:
                chat_type = ChatType.CHANNEL
            case ChatTypeTelegram.PRIVATE:
                chat_type = ChatType.PRIVATE
            case _:
                chat_type = ChatType.OTHER

        match event.new_chat_member:
            case ChatMemberLeft():
                logging.info(f"Bot removed from chat {event.chat.title} ({event.chat.id}) - {chat_type})")
                await remove_channel_or_group(session, event.chat.id)
            case _:
                logging.info(f"Detected adding to chat {event.chat.title} ({event.chat.id}) - {chat_type}")
                await add_new_channel_or_group(session, event.chat.id, event.chat.title, chat_type, event.chat.username)
                if chat_type == ChatType.GROUP:
                    return await event.answer(
                        "To register (connect) a new channel linked to this group, type in /register &lt;channel_name&gt; or /register &lt;channel_id&gt;")
    return None

# async def on_channel_post_handler(message: Message) -> None:
#     print(message)
