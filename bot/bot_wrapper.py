from aiogram import Bot, Router, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import MediaUnion, ChatIdUnion

from bot.middlewares import BotWrapperMiddleware
from config import settings


class BotWrapper:
    def __init__(self):
        self.bot = Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    async def start_bot(self, dp: Dispatcher) -> None:
        dp.callback_query.middleware(BotWrapperMiddleware(self))
        dp.message.middleware(BotWrapperMiddleware(self))
        await dp.start_polling(self.bot)

    async def copy_message(self, source_message_id: int, source_chat_id: int | str, target_chat_id: int) -> None:
        await self.bot.copy_message(message_id=source_message_id, chat_id=target_chat_id, from_chat_id=source_chat_id)

    async def send_media_group(self, chat_id: ChatIdUnion, media: list[MediaUnion]):
        await self.bot.send_media_group(chat_id=chat_id, media=media)