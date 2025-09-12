import logging

from aiogram import Dispatcher, html
from aiogram.enums import ChatType
from aiogram.filters import CommandStart, ChatMemberUpdatedFilter, IS_NOT_MEMBER, IS_MEMBER, JOIN_TRANSITION, Command
from aiogram.types import Message, ChatMemberUpdated, Update, ChatMemberLeft
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.util import await_only

from bot.middlewares import DbSessionMiddleware
from db.database import session_maker
from db.models import ChannelType
from db.repo import create_post_from_message, add_new_channel_or_group, remove_channel_or_group, \
    find_channel_by_username_or_id, add_channel_mapping

dp = Dispatcher()
dp.message.middleware(DbSessionMiddleware(session_maker=session_maker))
dp.chat_member.middleware(DbSessionMiddleware(session_maker=session_maker))
dp.my_chat_member.middleware(DbSessionMiddleware(session_maker=session_maker))


@dp.message(Command('register'))
async def register_new_channel(message: Message, session: AsyncSession):
    print(message.chat.type)
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
            # TODO bot chat is not registered, to think about handling such cases
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

# @dp.message()
# async def save_message(message: Message, session: AsyncSession) -> None:
#     print(message)
#     await create_post_from_message(session, source_message_id=message.message_id, source_chat_id=message.chat.id)
#     await session.commit()
