"""Daily poll job that records in-app notifications for upcoming episodes.

Runs in-process via APScheduler — no separate worker process or external
cron needed, which fits this project's single-uvicorn-process dev setup.
Real-time delivery is explicitly out of scope for v1 (see issue #8).
"""

import logging
from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session

from .db import SessionLocal
from .models import PendingNotification, TrackedShow
from .services import tvmaze

logger = logging.getLogger(__name__)

POLL_INTERVAL_HOURS = 24


async def poll_upcoming_episodes(db: Session | None = None) -> None:
    """Record a PendingNotification for every upcoming episode of every
    tracked show that doesn't already have one.

    Accepts an optional session so tests can inject an isolated in-memory
    DB instead of hitting the real SessionLocal/dev database.
    """
    owns_session = db is None
    if db is None:
        db = SessionLocal()
    now = datetime.now(timezone.utc)
    try:
        tracked = db.query(TrackedShow).all()
        for track in tracked:
            show = await tvmaze.get_show(track.tvmaze_show_id)
            upcoming = [
                ep
                for ep in show.episodes
                if ep.airstamp and datetime.fromisoformat(ep.airstamp) > now
            ]
            for ep in upcoming:
                existing = (
                    db.query(PendingNotification)
                    .filter_by(user_id=track.user_id, tvmaze_episode_id=ep.id)
                    .first()
                )
                if existing:
                    continue
                db.add(
                    PendingNotification(
                        user_id=track.user_id,
                        tvmaze_show_id=track.tvmaze_show_id,
                        tvmaze_episode_id=ep.id,
                        air_date=ep.airdate or "",
                    )
                )
            db.commit()
    finally:
        if owns_session:
            db.close()


def start_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        lambda: _run_async(poll_upcoming_episodes()),
        "interval",
        hours=POLL_INTERVAL_HOURS,
        id="poll_upcoming_episodes",
        next_run_time=datetime.now(),
    )
    scheduler.start()
    return scheduler


def _run_async(coro):
    import asyncio

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    if loop.is_running():
        # BackgroundScheduler runs jobs in worker threads, not the FastAPI
        # event loop, so there's never a running loop here in practice —
        # this branch only guards against being called from async code.
        asyncio.ensure_future(coro)
    else:
        loop.run_until_complete(coro)
