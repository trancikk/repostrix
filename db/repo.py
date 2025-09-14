from typing import Optional, Sequence

from sqlalchemy import delete, select, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased
from sqlalchemy.sql.functions import now

from db.models import Asset, Post, ChannelType, Channel, ChannelMapping, PostStatus
from dto import AssetDto
from utils import get_next_n_hours

SourceChannel = aliased(Channel)
TargetChannel = aliased(Channel)


async def create_post(session: AsyncSession, assets_dto: list[AssetDto], post_text: str = "") -> None:
    post = Post(text=post_text)
    session.add(post)
    assets = [Asset(asset_content=a.data, asset_url=a.url, post_id=post.id) for a in assets_dto]
    session.add_all(assets)


async def find_post(session: AsyncSession, post_id: int) -> Optional[Post]:
    existing_post_result = await session.execute(select(Post).where(Post.id == post_id))
    return existing_post_result.scalars().first()


def query_posts_with_target_channels():
    return (select(Post.id.label("post_id"), Post.source_message_id, Post.source_chat_id,
                   Post.scheduled_at,
                   TargetChannel.id.label("target_chat_id")
                   )
            .join(ChannelMapping, ChannelMapping.c.source_chat_id == Post.source_chat_id)
            .join(TargetChannel,
                  ChannelMapping.c.target_chat_id == TargetChannel.id))


async def find_post_with_target_channels(session: AsyncSession, post_id: int):
    q = (query_posts_with_target_channels()
    .where(
        Post.id == post_id))
    query_result = await session.execute(q)
    return query_result.all()


async def find_expired_posts(session: AsyncSession):
    q = (query_posts_with_target_channels().
         where(and_(Post.scheduled_at < now(), Post.status == PostStatus.PENDING)))
    results = await session.execute(q)
    return results.all()


async def update_post_status(session: AsyncSession, post_id: int, post_status: PostStatus):
    post = await find_post(session, post_id)
    post.status = post_status
    return post


async def create_post_from_message(session: AsyncSession, source_message_id: int, source_chat_id: int, text: str = "",
                                   files: Optional[list[str]] = None, is_album=False) -> Post:
    post = Post(source_message_id=source_message_id, source_chat_id=source_chat_id, text=text, is_album=is_album)
    session.add(post)
    await session.flush()
    if files is not None and len(files) > 0:
        for file in files:
            asset = Asset(file_id=file, post_id=post.id)
            session.add(asset)
        await session.flush()
        await session.refresh(post)
    return post


async def update_post_schedule(session: AsyncSession, post_id: int, delta: float) -> Optional[Post]:
    existing_post_result = await session.execute(select(Post).where(Post.id == post_id))
    existing_post = existing_post_result.scalar_one_or_none()
    if existing_post is not None:
        existing_post.scheduled_at = get_next_n_hours(delta)
        return existing_post
    return None


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
