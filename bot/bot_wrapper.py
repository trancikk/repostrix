from aiogram import Bot, Router, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import MediaUnion, ChatIdUnion, BotCommand, BotCommandScopeDefault, \
    BotCommandScopeAllChatAdministrators, BotCommandScopeAllGroupChats
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bot.middlewares import BotWrapperMiddleware, DbSessionMiddleware, SaveUserMiddleware, AlbumMiddleware
from bot.routes import all_routes, all_commands
from config import settings


class BotWrapper:
    def __init__(self):
        self.bot = Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    async def start_bot(self, dp: Dispatcher, session_maker:  async_sessionmaker[AsyncSession]) -> None:
        dp.callback_query.middleware(BotWrapperMiddleware(self))
        dp.message.middleware(BotWrapperMiddleware(self))
        dp.message.middleware(DbSessionMiddleware(session_maker=session_maker))
        dp.message.middleware(SaveUserMiddleware(session_factory=session_maker))
        dp.message.middleware(AlbumMiddleware())
        dp.edited_message.middleware(DbSessionMiddleware(session_maker=session_maker))
        dp.edited_message.middleware(SaveUserMiddleware(session_factory=session_maker))
        dp.edited_message.middleware(AlbumMiddleware())
        dp.callback_query.middleware(DbSessionMiddleware(session_maker=session_maker))
        dp.callback_query.middleware(SaveUserMiddleware(session_factory=session_maker))
        dp.chat_member.middleware(DbSessionMiddleware(session_maker=session_maker))
        dp.my_chat_member.middleware(DbSessionMiddleware(session_maker=session_maker))
        for route in all_routes:
            dp.include_router(route)
        await self.setup_bot_commands()
        await dp.start_polling(self.bot)

    async def get_chat_admins(self, chat_id: int):
        return await self.bot.get_chat_administrators(chat_id)

    async def copy_message(self, source_message_id: int, source_chat_id: int | str, target_chat_id: int) -> None:
        await self.bot.copy_message(message_id=source_message_id, chat_id=target_chat_id, from_chat_id=source_chat_id)

    async def send_media_group(self, chat_id: ChatIdUnion, media: list[MediaUnion]):
        await self.bot.send_media_group(chat_id=chat_id, media=media)

    async def setup_bot_commands(self):
        commands = [
            BotCommand(command="start", description="Start the bot"),
            BotCommand(command="help", description="Help info"),
            BotCommand(command="settings", description="Adjust preferences"),
            BotCommand(command="register", description="Register new channel"),
        ]
        commands.extend(all_commands)
        await self.bot.set_my_commands(commands, scope=BotCommandScopeDefault())
        await self.bot.set_my_commands(commands, scope=BotCommandScopeAllChatAdministrators())
        await self.bot.set_my_commands(commands, scope=BotCommandScopeAllGroupChats())
