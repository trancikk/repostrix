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