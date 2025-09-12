import logging

from aiogram import Dispatcher, html
from aiogram.filters import CommandStart, ChatMemberUpdatedFilter, IS_NOT_MEMBER, IS_MEMBER, JOIN_TRANSITION
from aiogram.types import Message, ChatMemberUpdated, Update
from sqlalchemy.ext.asyncio import AsyncSession

from bot.middlewares import DbSessionMiddleware
from db.database import session_maker
from db.models import ChannelType
from db.repo import create_post_from_message, add_new_channel_or_group

dp = Dispatcher()
dp.message.middleware(DbSessionMiddleware(session_maker=session_maker))
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

    # @dp.message()
    # async def echo_handler(message: Message) -> None:
    #     """
    #     Handler will forward receive a message back to the sender
    #
    #     By default, message handler will handle all message types (like a text, photo, sticker etc.)
    #     """
    #     try:
    #         logging.info(f"Received message from {message.from_user.full_name}")
    #         # print(f"Chat: {message.chat.id}, {message}")
    #         # print(message.video)
    #         # print(message.audio)
    #         for i in message.photo:
    #             print(i.file_size, i.width, i.height)
    #         print(message.photo[-1])
    #
    #         # Send a copy of the received message
    #         await message.send_copy(chat_id=message.chat.id)
    #     except TypeError:
    #         # But not all the types is supported to be copied so need to handle it
    #         await message.answer("Nice try!")


# @dp.chat_member()
# async def bot_added_to_group(event: ChatMemberUpdated):
#     bot_user_id = event.bot.id # Get your bot's user ID
#     print(event)
#     for member in event.new_chat_members:
#         if member.id == bot_user_id:
#             chat_id = event.chat.id
#             chat_title = event.chat.title
#             print(f"Bot was added to chat: {chat_title} (ID: {chat_id})")
#             # Perform actions like sending a welcome message, storing chat_id, etc.
#             await event.answer("Hello! Thanks for inviting me to this chat.")
#             break

@dp.my_chat_member()
async def register_new_channel(event: ChatMemberUpdated, session: AsyncSession):
    if event.bot.id == event.new_chat_member.user.id:
        chat_type = ChannelType.OTHER
        match event.chat.type:
            case "group":
                chat_type = ChannelType.GROUP
            case "channel":
                chat_type = ChannelType.CHANNEL
            case _:
                chat_type = ChannelType.OTHER
        await add_new_channel_or_group(session, event.chat.id, event.chat.title, chat_type)
        logging.info(f"Detected adding to chat {event.chat.title} ({event.chat.id}) - {chat_type}")

# @dp.channel_post()
# async def on_channel_post_handler(message: Message) -> None:
#     print(message)

# @dp.message()
# async def save_message(message: Message, session: AsyncSession) -> None:
#     print(message)
#     await create_post_from_message(session, source_message_id=message.message_id, source_chat_id=message.chat.id)
#     await session.commit()
