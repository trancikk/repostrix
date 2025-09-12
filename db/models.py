from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from sqlalchemy import ForeignKey, BigInteger, Table, Column, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class AssetType(Enum):
    VIDEO = 0,
    IMAGE = 1,
    ANIMATION = 2,


class ChannelType(Enum):
    CHANNEL = 0,
    GROUP = 1,
    PRIVATE = 2,
    OTHER = 3,


class Base(DeclarativeBase):
    pass


channel_mapping = Table(
    "Channel_mapping",
    Base.metadata,
    Column('id', BigInteger, primary_key=True),
    Column("source_chat_id", ForeignKey("Channel.id")),
    Column("target_chat_id", ForeignKey("Channel.id")),
)


class Channel(Base):
    __tablename__ = "Channel"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column()
    username: Mapped[Optional[str]] = mapped_column(nullable=True)
    channel_type: Mapped[ChannelType] = mapped_column()
    source_chats: Mapped[list['Channel']] = relationship(secondary=channel_mapping,
                                                         primaryjoin="Channel.id==Channel_mapping.c.source_chat_id",
                                                         secondaryjoin="Channel.id==Channel_mapping.c.target_chat_id",
                                                         backref="target_channels",
                                                         lazy="noload"
                                                         )
    # target_channels: Mapped['list[Channel]'] = relationship(secondary=channel_mapping, back_populates='source_chats',
    #                                                         primaryjoin="Channel.id==Channel.target_chat_id",
    #                                                         secondaryjoin="Channel.id==Channel.source_chat_id")


class User(Base):
    __tablename__ = "user"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()
    handle: Mapped[str] = mapped_column()


class Post(Base):
    __tablename__ = "post"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    source_chat_id: Mapped[int] = mapped_column(BigInteger)
    source_message_id: Mapped[int] = mapped_column(BigInteger)
    text: Mapped[Optional[str]] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    assets: Mapped["list[Asset]"] = relationship("Asset", back_populates="post",
                                                 lazy="noload",
                                                 cascade="all, delete-orphan"
                                                 )


class Asset(Base):
    __tablename__ = "asset"
    id: Mapped[int] = mapped_column(primary_key=True)
    asset_url: Mapped[Optional[str]] = mapped_column()
    asset_content: Mapped[Optional[bytes]] = mapped_column()
    post_id: Mapped[int] = mapped_column(ForeignKey("post.id"))
    post: Mapped["Post"] = relationship("Post",
                                        back_populates="assets",
                                        lazy="noload", )
