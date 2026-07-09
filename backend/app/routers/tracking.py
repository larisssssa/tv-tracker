from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import TrackedShow, User, WatchedEpisode
from ..schemas import (
    MarkWatchedRequest,
    MyShowOut,
    TrackedShowOut,
    TrackShowRequest,
    WatchedEpisodeOut,
)
from ..security import get_current_user
from ..services import tvmaze

router = APIRouter(prefix="/tracking", tags=["tracking"])


@router.post("/shows", response_model=TrackedShowOut, status_code=201)
def track_show(
    payload: TrackShowRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    existing = (
        db.query(TrackedShow)
        .filter_by(user_id=user.id, tvmaze_show_id=payload.tvmaze_show_id)
        .first()
    )
    if existing:
        return existing

    tracked = TrackedShow(user_id=user.id, tvmaze_show_id=payload.tvmaze_show_id)
    db.add(tracked)
    db.commit()
    db.refresh(tracked)
    return tracked


@router.delete("/shows/{tvmaze_show_id}", status_code=204)
def untrack_show(
    tvmaze_show_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    db.query(TrackedShow).filter_by(
        user_id=user.id, tvmaze_show_id=tvmaze_show_id
    ).delete()
    db.commit()


@router.get("/shows", response_model=list[MyShowOut])
async def list_my_shows(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    tracked = db.query(TrackedShow).filter_by(user_id=user.id).all()
    watched_ids = {
        w.tvmaze_episode_id
        for w in db.query(WatchedEpisode).filter_by(user_id=user.id).all()
    }

    results: list[MyShowOut] = []
    now = datetime.now(timezone.utc)

    for track in tracked:
        show = await tvmaze.get_show(track.tvmaze_show_id)

        aired_episodes = [
            ep
            for ep in show.episodes
            if ep.airstamp and datetime.fromisoformat(ep.airstamp) <= now
        ]
        aired_episodes.sort(key=lambda ep: (ep.season, ep.number))

        next_episode = next(
            (ep for ep in aired_episodes if ep.id not in watched_ids), None
        )
        watched_count = sum(1 for ep in aired_episodes if ep.id in watched_ids)

        results.append(
            MyShowOut(
                tvmaze_show_id=show.id,
                name=show.name,
                image=show.image,
                next_episode=next_episode,
                watched_count=watched_count,
                total_aired_count=len(aired_episodes),
            )
        )

    return results


@router.post("/episodes", response_model=WatchedEpisodeOut, status_code=201)
def mark_episode_watched(
    payload: MarkWatchedRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    existing = (
        db.query(WatchedEpisode)
        .filter_by(user_id=user.id, tvmaze_episode_id=payload.tvmaze_episode_id)
        .first()
    )
    if existing:
        return existing

    watched = WatchedEpisode(
        user_id=user.id,
        tvmaze_show_id=payload.tvmaze_show_id,
        tvmaze_episode_id=payload.tvmaze_episode_id,
    )
    db.add(watched)
    db.commit()
    db.refresh(watched)
    return watched


@router.delete("/episodes/{tvmaze_episode_id}", status_code=204)
def unmark_episode_watched(
    tvmaze_episode_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    db.query(WatchedEpisode).filter_by(
        user_id=user.id, tvmaze_episode_id=tvmaze_episode_id
    ).delete()
    db.commit()


@router.get("/episodes/watched", response_model=list[WatchedEpisodeOut])
def list_watched_episodes(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    return db.query(WatchedEpisode).filter_by(user_id=user.id).all()
