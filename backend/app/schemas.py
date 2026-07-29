from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


# --- Auth ---

class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    email: EmailStr

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# --- Shows (proxied from TVMaze, shaped for our frontend) ---

class ShowSummary(BaseModel):
    id: int
    name: str
    premiered: str | None = None
    status: str | None = None
    image: str | None = None
    summary: str | None = None


class Episode(BaseModel):
    id: int
    season: int
    number: int
    name: str
    airdate: str | None = None
    airstamp: str | None = None
    image: str | None = None


class ShowDetail(ShowSummary):
    episodes: list[Episode] = []


# --- Tracking ---

class TrackShowRequest(BaseModel):
    tvmaze_show_id: int


class TrackedShowOut(BaseModel):
    tvmaze_show_id: int
    added_at: datetime
    rating: int | None = None

    class Config:
        from_attributes = True


class RateShowRequest(BaseModel):
    rating: int = Field(ge=1, le=5)


class MarkWatchedRequest(BaseModel):
    tvmaze_show_id: int
    tvmaze_episode_id: int


class BulkMarkWatchedRequest(BaseModel):
    tvmaze_show_id: int
    tvmaze_episode_ids: list[int]


class BulkUnmarkWatchedRequest(BaseModel):
    tvmaze_episode_ids: list[int]


class WatchedEpisodeOut(BaseModel):
    tvmaze_episode_id: int
    watched_at: datetime
    rating: int | None = None

    class Config:
        from_attributes = True


class RateEpisodeRequest(BaseModel):
    rating: int = Field(ge=1, le=5)


class MyShowOut(BaseModel):
    """A tracked show enriched with metadata + the next unwatched episode."""

    tvmaze_show_id: int
    name: str
    image: str | None = None
    status: str | None = None
    next_episode: Episode | None = None
    next_unaired_episode: Episode | None = None
    watched_count: int
    total_aired_count: int
    rating: int | None = None


# --- Show lists ---

class CreateListRequest(BaseModel):
    name: str


class RenameListRequest(BaseModel):
    name: str


class AddShowToListRequest(BaseModel):
    tvmaze_show_id: int


class ShowListOut(BaseModel):
    """A list's own metadata, with no show data (cheap — no TVMaze calls)."""

    id: int
    name: str
    created_at: datetime
    is_public: bool

    class Config:
        from_attributes = True


class ListedShow(BaseModel):
    """A show as it appears inside a list — enriched with TVMaze metadata,
    but no watch-progress fields (lists are purely organizational)."""

    tvmaze_show_id: int
    name: str
    image: str | None = None
    status: str | None = None
    added_at: datetime


class ShowListDetailOut(BaseModel):
    """A list with its full, TVMaze-enriched show contents."""

    id: int
    name: str
    created_at: datetime
    is_public: bool
    shows: list[ListedShow]
