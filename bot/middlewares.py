import asyncio
from typing import Callable, Any, Awaitable, Dict, List

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject, User as TgUser
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from db.models import User  # your SQLAlchemy User model
from db.repo import find_user


class DbSessionMiddleware:
    def __init__(self, session_maker: async_sessionmaker[AsyncSession]):
        self.session_maker = session_maker

    async def __call__(
            self,
            handler: Callable[[Dict[str, Any], Any], Awaitable[Any]],
            event: Any,
            data: Dict[str, Any]
    ) -> Any:
        async with self.session_maker() as session:
            try:
                data["session"] = session  # inject into context
                result = await handler(event, data)
                await session.commit()
                return result
            except Exception:
                await session.rollback()
                raise


class BotWrapperMiddleware:
    def __init__(self, bot_wrap):
        self.bot_wrapper = bot_wrap

    async def __call__(
            self,
            handler: Callable[[Dict[str, Any], Any], Awaitable[Any]],
            event: Any,
            data: Dict[str, Any]
    ) -> Any:
        data["bot_wrapper"] = self.bot_wrapper  # inject into context
        return await handler(event, data)


# album_middleware.py


class AlbumMiddleware(BaseMiddleware):
    """Collect messages belonging to the same media_group_id and pass them
    to handler as 'album' (list[Message]). Register with router.message.middleware(...)."""

    def __init__(self, latency: float = 1.0):
        self.latency = latency
        self._albums: Dict[str, List[Message]] = {}

    async def __call__(
            self,
            handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Message,
            data: Dict[str, Any],
    ) -> Any:
        mgid = event.media_group_id
        # not part of an album -> normal processing
        if not mgid:
            data["album"] = []
            return await handler(event, data)

        # first message for this media_group_id
        if mgid not in self._albums:
            self._albums[mgid] = [event]
            # wait small time for rest of album to arrive
            await asyncio.sleep(self.latency)
            album = self._albums.pop(mgid, [])
            # put album into handler data so handler can accept `album` param
            data["album"] = album
            # call handler once using the first message as "representative"
            return await handler(album[0], data)

        # subsequent parts: just append and don't call handler now
        self._albums[mgid].append(event)
        return None  # swallow - handler will be called by the first message after sleep


# TODO to think if i want to use it. GPT generated
class SaveUserMiddleware(BaseMiddleware):
    """
    Middleware that ensures the Telegram user exists in the DB.
    """

    def __init__(self, session_factory):
        # session_factory: a callable that returns AsyncSession (e.g. sessionmaker)
        self.session_factory = session_factory

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]
    ) -> Any:
        tg_user: TgUser | None = data.get("event_from_user")
        if tg_user:
            async with self.session_factory() as session:
                # check if user exists
                db_user = await find_user(session, tg_user.id)

                if not db_user:
                    db_user = User(
                        id=tg_user.id,
                        name=tg_user.first_name,
                        handle=tg_user.username,
                    )
                    session.add(db_user)
                    await session.commit()

                # put the db_user into handler context
                data["db_user"] = db_user

        return await handler(event, data)
