# TV Tracker

A TV Time-style episode tracker: search shows, track them, mark episodes
watched (individually or in bulk), and see what to watch next across
everything you track.

## Architecture

```
backend/    FastAPI + SQLite
  app/
    main.py           app entrypoint, CORS, router registration, /health
    models.py         SQLAlchemy models: User, TrackedShow, WatchedEpisode
    schemas.py         Pydantic request/response shapes
    security.py        password hashing (bcrypt) + JWT auth
    db.py               SQLite engine/session setup
    routers/
      auth.py           register / login
      shows.py          search + show detail (proxies TVMaze)
      tracking.py       track/untrack shows, mark/unmark episodes
                          (single + bulk), "my shows" with next-up
    services/
      tvmaze.py          all TVMaze HTTP calls live here
  tests/                pytest suite (see Testing below)

frontend/   React + TypeScript + Vite
  src/
    pages/
      AuthPage.tsx        login / register
      UpNextPage.tsx      home page — next episode across all tracked shows
      MyShowsPage.tsx     tracked shows with watch progress
      SearchPage.tsx      live show search
      ShowDetailPage.tsx  season/episode list, bulk watch actions
    api/client.ts        typed fetch wrapper, one function per endpoint
    context/AuthContext.tsx
    types.ts
    index.css, App.css   design system tokens + component styles
```

Show and episode metadata (titles, images, air dates) is never stored
in our own database — it's fetched live from the
[TVMaze API](https://www.tvmaze.com/api) on every request. Our database
only stores *your* tracking state: which TVMaze show IDs you've added,
and which TVMaze episode IDs you've watched. This keeps our data model
simple and means we never go stale relative to TVMaze's catalog.

## Features

- **Search** — debounced live search (300ms) against TVMaze, no need to hit enter.
- **Track shows** — add any show to "My Shows" from search or its detail page.
- **Up Next** — the home page: one row per tracked show showing the next
  episode to watch, sorted soonest-first. Shows that are fully caught up
  but have a future episode scheduled still appear, tagged "Upcoming",
  so you can see what's coming without it needing an action yet.
- **Mark episodes watched** — per-episode checkboxes, per-season bulk
  mark/unmark ("Mark season watched" / "Undo"), or whole-show bulk
  mark/unmark, all reflected immediately in watch-progress counts.
- **Collapsible seasons** — the show detail page auto-expands the season
  containing your next unwatched episode and collapses the rest, so long
  shows (many seasons/episodes) don't turn into an endless scroll.
- **Status badges** — shows are tagged Running/Ended/etc. from TVMaze;
  Up Next also tags not-yet-aired episodes as Upcoming.

## Design system

The UI follows the token set in `plan/DESIGN.md` (not shipped/tracked in
git — a local design reference): an aurora-gradient light canvas, a single
magenta/navy accent, pill-shaped buttons, and a three-layer soft shadow on
floating cards. The actual CSS custom properties live in
`frontend/src/index.css`, consumed throughout `frontend/src/App.css`.

## API reference

All `/tracking/*` routes require `Authorization: Bearer <token>` (obtained
from `/auth/login`). `/shows/*` routes are unauthenticated proxies to TVMaze.

| Method | Path | Notes |
| --- | --- | --- |
| POST | `/auth/register` | `{email, password}` → 201 + user (no password in response) |
| POST | `/auth/login` | OAuth2 form fields (`username`/`password`) → 200 + JWT bearer token |
| GET | `/shows/search?q=` | Search TVMaze; empty query returns `[]` |
| GET | `/shows/{show_id}` | Show detail + full episode list |
| GET | `/tracking/shows` | "My Shows" — each show enriched with `next_episode`, `next_unaired_episode`, watch counts |
| POST | `/tracking/shows` | Track a show; idempotent |
| DELETE | `/tracking/shows/{tvmaze_show_id}` | Untrack a show |
| POST | `/tracking/episodes` | Mark one episode watched; idempotent |
| DELETE | `/tracking/episodes/{tvmaze_episode_id}` | Unmark one episode |
| POST | `/tracking/episodes/bulk` | Mark many episodes watched at once; idempotent per-episode |
| POST | `/tracking/episodes/bulk-unmark` | Unmark many episodes at once |
| GET | `/tracking/episodes/watched` | All of the current user's watched episodes |
| GET | `/health` | `{"status": "ok"}` |

Interactive docs (Swagger UI) are available at http://localhost:8000/docs
once the backend is running.

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

This creates `tv_tracker.db` (SQLite) on first run.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173.

## Testing

Backend has a pytest suite in `backend/tests/` (15 tests): auth flows,
bulk mark/unmark correctness and idempotency, cross-user isolation, and
the "my shows" next-episode/next-unaired-episode computation (using
`pytest-mock` to stub TVMaze responses so tests don't hit the network).

```bash
cd backend
source .venv/bin/activate
python -m pytest
```

Each test runs against an isolated in-memory SQLite database — the real
dev database (`tv_tracker.db`) is never touched by the test suite.

There is no frontend test suite yet.

## Known limitations

- Auth is minimal: JWT with a hardcoded dev secret in `security.py` —
  fine for local use, not production-ready (secret must move to an
  env var before deploying anywhere real).
- `GET /tracking/shows` fetches each tracked show's full episode list
  from TVMaze on every request (no local caching). Fine for a handful
  of shows; would get slow if a user tracks hundreds of shows.
- No password reset, no social features, no notifications/calendar —
  see open GitHub issues for planned follow-ups.
