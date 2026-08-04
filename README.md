# TV Tracker

A TV Time-style episode tracker: search shows, track them, mark episodes
watched (individually or in bulk), and see what to watch next across
everything you track.

## Screenshots

| Up Next | My Shows |
| --- | --- |
| ![Up Next — next episode per tracked show](docs/screenshots/up-next.png) | ![My Shows — watch progress and star ratings](docs/screenshots/my-shows.png) |

| Search | Show detail |
| --- | --- |
| ![Search — live TVMaze search results](docs/screenshots/search.png) | ![Show detail — collapsible seasons, episode ratings](docs/screenshots/show-detail.png) |

<details>
<summary>Login</summary>

![Login page](docs/screenshots/auth.png)

</details>

## Architecture

```
backend/    FastAPI + SQLite
  app/
    main.py           app entrypoint, CORS, router registration, /health
    models.py         SQLAlchemy models: User, TrackedShow, WatchedEpisode,
                        ShowList, ShowListItem
                        (TrackedShow and WatchedEpisode each carry an
                        optional 1-5 `rating` field, set independently)
    schemas.py         Pydantic request/response shapes
    security.py        password hashing (bcrypt) + JWT auth
    db.py               SQLite engine/session setup
    routers/
      auth.py           register / login / me / me/stats
      shows.py          search + show detail (proxies TVMaze)
      tracking.py       track/untrack shows, mark/unmark episodes
                          (single + bulk), "my shows" with next-up
      lists.py          custom show lists (create/rename/delete,
                          add/remove shows) — independent of TrackedShow
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
      ListsPage.tsx       manage custom lists; view/edit one list's shows
      ProfilePage.tsx     email, member-since date, stat cards, and a
                            read-only summary of My Shows + custom lists
    components/
      StarRating.tsx      shared 1-5 star rating control (editable or
                            read-only, via the `readOnly` prop)
      ShowCard.tsx        poster + name + read-only rating, used on the
                            Profile page's My Shows / Lists summaries
      AddToListPicker.tsx modal: toggle a show's membership across lists
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

Removing a show from "My Shows" only deletes its `TrackedShow` row —
your `WatchedEpisode` history for that show is kept. Re-adding the same
show later restores your watched progress instead of starting over.

Custom lists (`ShowList`/`ShowListItem`) are a separate, purely
organizational concept from "My Shows" (`TrackedShow`). A show can be in
a list without being tracked, tracked without being in any list, or both
at once — being in a list carries no watch-progress meaning.

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
- **Ratings** — a 1-5 star rating on any watched episode (on the show
  detail page) and a separate 1-5 star rating on the show itself (on
  "My Shows"). The two are independent: a show's rating is not an
  average of its episode ratings.
- **Custom lists** — organize shows into named lists (e.g. "Favorites",
  "Watch Later") from the "Lists" nav page, or via an "Add to list"
  picker on the search and show detail pages. A show can belong to
  multiple lists, and lists work independently of "My Shows" — a show
  doesn't need to be tracked to be added to a list.
- **Profile** — a read-only page showing your email, member-since date,
  and two stat cards: total shows tracked and total episodes watched.
  The episode count is all-time (it doesn't drop if you later untrack a
  show, since watch history is never deleted on untrack). Below the
  stats, a "My Shows" section shows your 5 most recently tracked shows
  as show cards (poster, name, view-only star rating), plus a "View all
  my shows" link; a "Your Lists" section shows the same card layout for
  each custom list's 5 most recently added shows, plus a "View list"
  link per list. Both sections are read-only summaries — managing shows
  and lists still happens on the My Shows and Lists pages.

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
| GET | `/auth/me` | The current user (`id`, `email`, `created_at`) |
| GET | `/auth/me/stats` | `shows_tracked`, `episodes_watched` (all-time), `member_since` |
| GET | `/shows/search?q=` | Search TVMaze; empty query returns `[]` |
| GET | `/shows/{show_id}` | Show detail + full episode list |
| GET | `/tracking/shows` | "My Shows" — each show enriched with `next_episode`, `next_unaired_episode`, watch counts, `rating` |
| POST | `/tracking/shows` | Track a show; idempotent |
| DELETE | `/tracking/shows/{tvmaze_show_id}` | Untrack a show |
| PUT | `/tracking/shows/{tvmaze_show_id}/rating` | Set/update the show's own 1-5 rating; 404 if not tracked |
| POST | `/tracking/episodes` | Mark one episode watched; idempotent |
| DELETE | `/tracking/episodes/{tvmaze_episode_id}` | Unmark one episode |
| PUT | `/tracking/episodes/{tvmaze_episode_id}/rating` | Set/update a watched episode's 1-5 rating; 404 if not watched |
| POST | `/tracking/episodes/bulk` | Mark many episodes watched at once; idempotent per-episode |
| POST | `/tracking/episodes/bulk-unmark` | Unmark many episodes at once |
| GET | `/tracking/episodes/watched` | All of the current user's watched episodes, each with `rating` |
| POST | `/lists` | Create a list; `{name}` → 201 + the new list |
| GET | `/lists` | List the current user's lists (metadata only, no shows — cheap, no TVMaze calls) |
| GET | `/lists/{list_id}` | One list's detail, with its shows enriched from TVMaze; 404 if not owned |
| PUT | `/lists/{list_id}` | Rename a list; 404 if not owned |
| DELETE | `/lists/{list_id}` | Delete a list (does not affect `TrackedShow`/watch history for its shows) |
| POST | `/lists/{list_id}/shows` | Add a show to a list; idempotent; 404 if list not owned |
| DELETE | `/lists/{list_id}/shows/{tvmaze_show_id}` | Remove a show from a list |
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

Backend has a pytest suite in `backend/tests/` (45 tests): auth flows,
bulk mark/unmark correctness and idempotency, cross-user isolation, the
"my shows" next-episode/next-unaired-episode computation (using
`pytest-mock` to stub TVMaze responses so tests don't hit the network),
episode/show rating validation and persistence, custom list
CRUD/membership operations and cross-user isolation, and profile stats
correctness (including that stats survive untracking a show).

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
