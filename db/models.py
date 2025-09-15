from datetime import datetime, time
from enum import Enum
from typing import Optional
from zoneinfo import ZoneInfo

from sqlalchemy import ForeignKey, BigInteger, Table, Column, DateTime, Time, TypeDecorator, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, foreign

from utils import get_now, get_next_n_hours, next_fire_time


class ZoneInfoType(TypeDecorator):
    """Stores ZoneInfo as its key string in DB."""
    impl = String(64)  # plenty for long TZ names like "America/Argentina/Buenos_Aires"

    cache_ok = True

    def process_bind_param(self, value, dialect):
        # Python -> DB
        if isinstance(value, ZoneInfo):
            return value.key
        elif isinstance(value, str):
            return value
        elif value is None:
            return None
        raise ValueError(f"Cannot store timezone: {value!r}")

    def process_result_value(self, value, dialect):
        # DB -> Python
        if value is None:
            return None
        return ZoneInfo(value)


class AssetType(Enum):
    VIDEO = 0,
    IMAGE = 1,
    ANIMATION = 2,


class ChatType(Enum):
    CHAT = 0,
    GROUP = 1,
    CHANNEL = 2,
    PRIVATE = 3,
    OTHER = 4,


class PostStatus(Enum):
    PENDING = 0,
    POSTED = 1,
    CANCELLED = 2,


class IntervalType(Enum):
    HOUR = 0,
    DAY = 1,


class Base(DeclarativeBase):
    pass


ChatMapping = Table(
    "chat_mapping",
    Base.metadata,
    Column('id', BigInteger, primary_key=True),
    Column("source_chat_id", ForeignKey("chat.id")),
    Column("target_chat_id", ForeignKey("chat.id")),
)


class Chat(Base):
    __tablename__ = "chat"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column()
    username: Mapped[Optional[str]] = mapped_column(nullable=True)
    chat_type: Mapped[ChatType] = mapped_column()
    channel_schedule_preference: Mapped["ChannelSchedulePreference"] = relationship("ChannelSchedulePreference",
                                                                                    back_populates="channel",
                                                                                    uselist=False, lazy="noload")
    source_chats: Mapped[list['Chat']] = relationship("Chat",
                                                      uselist=True,
                                                      secondary=ChatMapping,
                                                      primaryjoin=id == ChatMapping.c.source_chat_id,
                                                      secondaryjoin=id == ChatMapping.c.target_chat_id,
                                                      backref="target_chats",
                                                      lazy="noload"
                                                      )

    @property
    def next_fire_time(self) -> datetime:
        schedule_preference = self.channel_schedule_preference
        if schedule_preference is not None:
            match schedule_preference.interval_unit:
                case IntervalType.HOUR:
                    return get_next_n_hours(schedule_preference.interval_value, floored=True)
                # TODO doesn't handle cases like '2 days' although i doubt i need it
                case IntervalType.DAY:
                    return next_fire_time(schedule_preference.time_of_day, schedule_preference.timezone)
        return get_now()

    # target_Chats: Mapped['list[Chat]'] = relationship(secondary=Chat_mapping, back_populates='source_chats',
    #                                                         primaryjoin="Chat.id==Chat.target_chat_id",
    #                                                         secondaryjoin="Chat.id==Chat.source_chat_id")


class ChannelSchedulePreference(Base):
    __tablename__ = "channel_schedule_preference"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    channel_id: Mapped[int] = mapped_column(ForeignKey("chat.id"))
    channel = relationship("Chat", foreign_keys=[channel_id], back_populates="channel_schedule_preference")
    interval_unit: Mapped[IntervalType] = mapped_column(default=IntervalType.HOUR)
    interval_value: Mapped[int] = mapped_column(default=0, nullable=True)
    time_of_day: Mapped[list[time]] = mapped_column(ARRAY(Time))
    timezone: Mapped[ZoneInfo] = mapped_column(ZoneInfoType, default=ZoneInfo('UTC'))


class User(Base):
    __tablename__ = "user"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()
    handle: Mapped[str] = mapped_column()
    timezone: Mapped[ZoneInfo] = mapped_column(ZoneInfoType, default=ZoneInfo('UTC'))


class Post(Base):
    __tablename__ = "post"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    source_chat_id: Mapped[int] = mapped_column(BigInteger)
    source_message_id: Mapped[int] = mapped_column(BigInteger)
    text: Mapped[Optional[str]] = mapped_column()
    status: Mapped[PostStatus] = mapped_column(default=PostStatus.PENDING)
    is_album: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: get_now())
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    posted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    source_chat: Mapped['Chat'] = relationship(Chat, lazy="noload",
                                               primaryjoin=Chat.id == foreign(source_chat_id))
    target_chats: Mapped[list['Chat']] = relationship(Chat,
                                                      uselist=True,
                                                      secondary=ChatMapping,
                                                      primaryjoin=ChatMapping.c.source_chat_id == foreign(
                                                          source_chat_id),
                                                      secondaryjoin=foreign(ChatMapping.c.target_chat_id) == Chat.id,
                                                      lazy="noload", )
    assets: Mapped[list["Asset"]] = relationship("Asset", back_populates="post",
                                                 uselist=True,
                                                 lazy="noload",
                                                 cascade="all, delete-orphan",
                                                 )


class Asset(Base):
    __tablename__ = "asset"
    id: Mapped[int] = mapped_column(primary_key=True)
    file_id: Mapped[Optional[str]] = mapped_column()
    asset_url: Mapped[Optional[str]] = mapped_column()
    asset_content: Mapped[Optional[bytes]] = mapped_column()
    post_id: Mapped[int] = mapped_column(ForeignKey("post.id"))
    post: Mapped["Post"] = relationship("Post",
                                        uselist=False,
                                        back_populates="assets",
                                        lazy="noload", )
