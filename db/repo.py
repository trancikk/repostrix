from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Asset, Post
from dto import AssetDto


async def create_post(session: AsyncSession, assets_dto: list[AssetDto], post_text: str = "") -> None:
    post = Post(text=post_text)
    session.add(post)
    assets = [Asset(asset_content=a.data, asset_url=a.url, post_id=post.id) for a in assets_dto]
    session.add_all(assets)

async def create_post_from_message(session: AsyncSession, source_message_id: int, source_chat_id: int) -> None:
    post = Post(source_message_id=source_message_id, source_chat_id=source_chat_id)
    session.add(post)
