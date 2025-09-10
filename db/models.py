from enum import Enum
from typing import Optional

from sqlalchemy import ForeignKey, BigInteger
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class AssetType(Enum):
    VIDEO = 0,
    IMAGE = 1,
    ANIMATION = 2,


class Base(DeclarativeBase):
    pass


class Channel(Base):
    __tablename__ = "channel"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()


class User(Base):
    __tablename__ = "user"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()
    handle: Mapped[str] = mapped_column()


class Chat(Base):
    __tablename__ = "chat"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()


class Post(Base):
    __tablename__ = "post"
    id: Mapped[int] = mapped_column(primary_key=True)
    source_chat_id: Mapped[int] = mapped_column(BigInteger)
    source_message_id: Mapped[int] = mapped_column(BigInteger)
    text: Mapped[Optional[str]] = mapped_column()
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
