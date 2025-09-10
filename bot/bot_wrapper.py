from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.router import dp
from config import settings


class BotWrapper:
    def __init__(self):
        self.bot = Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    async def start_bot(self) -> None:
        await dp.start_polling(self.bot)

    async def copy_message(self, source_message_id: int, source_chat_id: int | str, target_chat_id: int) -> None:
        await self.bot.copy_message(message_id=source_message_id, chat_id=target_chat_id, from_chat_id=source_chat_id)
