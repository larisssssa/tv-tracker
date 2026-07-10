from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import TrackedShow, User, WatchedEpisode
from ..schemas import (
    BulkMarkWatchedRequest,
    BulkUnmarkWatchedRequest,
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

        aired_episodes = []
        unaired_episodes = []
        for ep in show.episodes:
            if ep.airstamp and datetime.fromisoformat(ep.airstamp) <= now:
                aired_episodes.append(ep)
            else:
                unaired_episodes.append(ep)

        aired_episodes.sort(key=lambda ep: (ep.season, ep.number))
        unaired_episodes.sort(key=lambda ep: (ep.season, ep.number))

        next_episode = next(
            (ep for ep in aired_episodes if ep.id not in watched_ids), None
        )
        next_unaired_episode = unaired_episodes[0] if unaired_episodes else None
        watched_count = sum(1 for ep in aired_episodes if ep.id in watched_ids)

        results.append(
            MyShowOut(
                tvmaze_show_id=show.id,
                name=show.name,
                image=show.image,
                status=show.status,
                next_episode=next_episode,
                next_unaired_episode=next_unaired_episode,
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


@router.post("/episodes/bulk", response_model=list[WatchedEpisodeOut], status_code=201)
def mark_episodes_watched_bulk(
    payload: BulkMarkWatchedRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    requested_ids = set(payload.tvmaze_episode_ids)
    if not requested_ids:
        return []

    already_watched = (
        db.query(WatchedEpisode)
        .filter(
            WatchedEpisode.user_id == user.id,
            WatchedEpisode.tvmaze_episode_id.in_(requested_ids),
        )
        .all()
    )
    already_watched_ids = {w.tvmaze_episode_id for w in already_watched}

    new_rows = [
        WatchedEpisode(
            user_id=user.id,
            tvmaze_show_id=payload.tvmaze_show_id,
            tvmaze_episode_id=episode_id,
        )
        for episode_id in requested_ids
        if episode_id not in already_watched_ids
    ]
    db.add_all(new_rows)
    db.commit()
    for row in new_rows:
        db.refresh(row)

    return already_watched + new_rows


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


@router.post("/episodes/bulk-unmark", status_code=204)
def unmark_episodes_watched_bulk(
    payload: BulkUnmarkWatchedRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    requested_ids = set(payload.tvmaze_episode_ids)
    if not requested_ids:
        return

    db.query(WatchedEpisode).filter(
        WatchedEpisode.user_id == user.id,
        WatchedEpisode.tvmaze_episode_id.in_(requested_ids),
    ).delete(synchronize_session=False)
    db.commit()


@router.get("/episodes/watched", response_model=list[WatchedEpisodeOut])
def list_watched_episodes(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    return db.query(WatchedEpisode).filter_by(user_id=user.id).all()
