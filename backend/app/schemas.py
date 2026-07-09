from datetime import datetime

from pydantic import BaseModel, EmailStr


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

    class Config:
        from_attributes = True


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

    class Config:
        from_attributes = True


class MyShowOut(BaseModel):
    """A tracked show enriched with metadata + the next unwatched episode."""

    tvmaze_show_id: int
    name: str
    image: str | None = None
    next_episode: Episode | None = None
    watched_count: int
    total_aired_count: int
