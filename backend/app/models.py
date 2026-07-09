from datetime import datetime, timezone

from sqlalchemy import String, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    tracked_shows: Mapped[list["TrackedShow"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    watched_episodes: Mapped[list["WatchedEpisode"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class TrackedShow(Base):
    """A show a user has added to their list. Only stores the TVMaze show id —
    all title/poster/episode metadata is fetched live from TVMaze."""

    __tablename__ = "tracked_shows"
    __table_args__ = (UniqueConstraint("user_id", "tvmaze_show_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    tvmaze_show_id: Mapped[int] = mapped_column(Integer, index=True)
    added_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    user: Mapped["User"] = relationship(back_populates="tracked_shows")


class WatchedEpisode(Base):
    """Marks a single episode (identified by TVMaze episode id) as watched by a user."""

    __tablename__ = "watched_episodes"
    __table_args__ = (UniqueConstraint("user_id", "tvmaze_episode_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    tvmaze_show_id: Mapped[int] = mapped_column(Integer, index=True)
    tvmaze_episode_id: Mapped[int] = mapped_column(Integer, index=True)
    watched_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    user: Mapped["User"] = relationship(back_populates="watched_episodes")
