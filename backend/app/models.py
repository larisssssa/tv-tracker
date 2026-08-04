from datetime import datetime, timezone

from sqlalchemy import Boolean, String, Integer, DateTime, ForeignKey, UniqueConstraint
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
    show_lists: Mapped[list["ShowList"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    notifications: Mapped[list["PendingNotification"]] = relationship(
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
    # User's own rating of the show as a whole — independent of any
    # episode ratings, not an average of them.
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)

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
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)

    user: Mapped["User"] = relationship(back_populates="watched_episodes")


class ShowList(Base):
    """A user-created, named group of shows (e.g. "Favorites", "Watch Later").

    Purely organizational: independent of TrackedShow/watch-progress. A show
    can be tracked without being in any list, and can be in a list without
    being tracked.
    """

    __tablename__ = "show_lists"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    # Reserved for future shareable/public lists. No public-viewing endpoint
    # exists yet — this column just avoids a breaking-change migration later.
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped["User"] = relationship(back_populates="show_lists")
    items: Mapped[list["ShowListItem"]] = relationship(
        back_populates="show_list", cascade="all, delete-orphan"
    )


class ShowListItem(Base):
    """A single show's membership in a ShowList. A show can belong to
    multiple lists at once (one row per list/show pair)."""

    __tablename__ = "show_list_items"
    __table_args__ = (UniqueConstraint("list_id", "tvmaze_show_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    list_id: Mapped[int] = mapped_column(ForeignKey("show_lists.id"))
    tvmaze_show_id: Mapped[int] = mapped_column(Integer, index=True)
    added_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    show_list: Mapped["ShowList"] = relationship(back_populates="items")


class PendingNotification(Base):
    """A recorded 'this user should be notified about this upcoming episode'
    event. In-app only for v1 — no email/push delivery.

    One row per (user, episode): the daily poll job skips episodes that
    already have a row, so re-polling never creates duplicates.
    """

    __tablename__ = "pending_notifications"
    __table_args__ = (UniqueConstraint("user_id", "tvmaze_episode_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    tvmaze_show_id: Mapped[int] = mapped_column(Integer, index=True)
    tvmaze_episode_id: Mapped[int] = mapped_column(Integer, index=True)
    air_date: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    read_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    user: Mapped["User"] = relationship(back_populates="notifications")
