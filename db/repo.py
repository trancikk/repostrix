from typing import Optional

from sqlalchemy import delete, select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Asset, Post, ChannelType, Channel
from dto import AssetDto


async def create_post(session: AsyncSession, assets_dto: list[AssetDto], post_text: str = "") -> None:
    post = Post(text=post_text)
    session.add(post)
    assets = [Asset(asset_content=a.data, asset_url=a.url, post_id=post.id) for a in assets_dto]
    session.add_all(assets)


async def create_post_from_message(session: AsyncSession, source_message_id: int, source_chat_id: int) -> Post:
    post = Post(source_message_id=source_message_id, source_chat_id=source_chat_id)
    session.add(post)
    await session.flush()
    return post


async def add_new_channel_or_group(session: AsyncSession, chat_id: int, channel_name: str,
                                   channel_type: ChannelType, username: Optional[str] = None):
    result = await session.execute(select(Channel).where(Channel.id == chat_id))
    existing_channel: Optional[Channel] = result.scalars().first()
    if existing_channel is not None:
        existing_channel.name = channel_name
        existing_channel.username = username
    else:
        channel = Channel(id=chat_id, name=channel_name, channel_type=channel_type, username=username)
        session.add(channel)


async def find_channel_by_username_or_id(session: AsyncSession, username_or_id: str) -> Optional[Channel]:
    result = await session.execute(
        select(Channel).where(or_(Channel.username == username_or_id, str(Channel.id) == username_or_id)))
    return result.scalars().first()


async def find_channel_by_id(session: AsyncSession, channel_id: int) -> Optional[Channel]:
    result = await session.execute(select(Channel).where(Channel.id == channel_id))
    return result.scalars().first()


async def remove_channel_or_group(session: AsyncSession, chat_id: int) -> int:
    sql = delete(Channel).where(Channel.id == chat_id)
    result = await session.execute(sql)
    return result.rowcount


# TODO add EH
async def add_channel_mapping(session: AsyncSession, source_chat_id: int, target_chat_id: int) -> None:
    source_chat = await find_channel_by_id(session, source_chat_id)
    if source_chat is not None:
        target_chat = await find_channel_by_id(session, target_chat_id)
        if target_chat is not None:
            source_chat.source_chats.append(target_chat)
            target_chat.source_chats.append(source_chat)
