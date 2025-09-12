from typing import Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Asset, Post, ChannelType, Channel
from dto import AssetDto


async def create_post(session: AsyncSession, assets_dto: list[AssetDto], post_text: str = "") -> None:
    post = Post(text=post_text)
    session.add(post)
    assets = [Asset(asset_content=a.data, asset_url=a.url, post_id=post.id) for a in assets_dto]
    session.add_all(assets)


async def create_post_from_message(session: AsyncSession, source_message_id: int, source_chat_id: int) -> None:
    post = Post(source_message_id=source_message_id, source_chat_id=source_chat_id)
    session.add(post)


async def add_new_channel_or_group(session: AsyncSession, chat_id: int, channel_name: str, channel_type: ChannelType):
    result = await session.execute(select(Channel).where(Channel.id == chat_id))
    existing_channel: Optional[Channel] = result.scalars().first()
    if existing_channel is not None:
        existing_channel.name = channel_name
    else:
        channel = Channel(id=chat_id, name=channel_name, channel_type=channel_type)
        session.add(channel)


async def remove_channel_or_group(session: AsyncSession, chat_id: int) -> int:
    sql = delete(Channel).where(Channel.id == chat_id)
    result = await session.execute(sql)
    return result.rowcount
