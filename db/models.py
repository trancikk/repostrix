from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Optional

from sqlalchemy import ForeignKey, BigInteger, Table, Column, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, foreign

from utils import get_now, get_next_n_hours


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
    source_chats: Mapped[list['Chat']] = relationship("Chat",
                                                      uselist=True,
                                                      secondary=ChatMapping,
                                                      primaryjoin=id == ChatMapping.c.source_chat_id,
                                                      secondaryjoin=id == ChatMapping.c.target_chat_id,
                                                      backref="target_chats",
                                                      lazy="noload"
                                                      )
    # target_Chats: Mapped['list[Chat]'] = relationship(secondary=Chat_mapping, back_populates='source_chats',
    #                                                         primaryjoin="Chat.id==Chat.target_chat_id",
    #                                                         secondaryjoin="Chat.id==Chat.source_chat_id")


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
    status: Mapped[PostStatus] = mapped_column(default=PostStatus.PENDING)
    is_album: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: get_now())
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True,
                                                             default=lambda: get_next_n_hours(1))
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
