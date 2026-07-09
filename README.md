# TV Tracker

A minimal TV Time-style episode tracker: search shows, add them to your
list, mark episodes watched, and see what's next to watch per show.

## Architecture

```
backend/    FastAPI + SQLite
  app/
    main.py           app entrypoint, CORS, router registration
    models.py         SQLAlchemy models: User, TrackedShow, WatchedEpisode
    schemas.py         Pydantic request/response shapes
    security.py        password hashing (bcrypt) + JWT auth
    db.py               SQLite engine/session setup
    routers/
      auth.py           register / login
      shows.py          search + show detail (proxies TVMaze)
      tracking.py       add/remove show, mark/unmark episode, "my shows" + next-up
    services/
      tvmaze.py          all TVMaze HTTP calls live here

frontend/   React + TypeScript + Vite
  src/
    pages/
      AuthPage.tsx
      SearchPage.tsx
      MyShowsPage.tsx
      ShowDetailPage.tsx
    api/client.ts        typed fetch wrapper, one function per endpoint
    context/AuthContext.tsx
    types.ts
```

Show and episode metadata (titles, images, air dates) is never stored
in our own database — it's fetched live from the
[TVMaze API](https://www.tvmaze.com/api) on every request. Our database
only stores *your* tracking state: which TVMaze show IDs you've added,
and which TVMaze episode IDs you've watched. This keeps our data model
simple and means we never go stale relative to TVMaze's catalog.

## Running locally

You need two terminals — backend and frontend run as separate processes.

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

This creates `tv_tracker.db` (SQLite) on first run. API docs are at
http://localhost:8000/docs.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173.

## Known limitations (scaffold scope)

- Auth is minimal: JWT with a hardcoded dev secret in `security.py` —
  fine for local use, not production-ready (secret must move to an
  env var before deploying anywhere real).
- `GET /tracking/shows` fetches each tracked show's full episode list
  from TVMaze on every request. Fine for a handful of shows; would
  need local caching of show/episode data if a user tracks hundreds
  of shows.
- No password reset, no social features, no notifications/calendar —
  intentionally out of scope for this first pass.
