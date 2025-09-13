from typing import Callable, Dict, Awaitable, Any

from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession


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
