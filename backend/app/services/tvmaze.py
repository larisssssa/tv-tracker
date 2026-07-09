"""Thin wrapper around the TVMaze API (https://www.tvmaze.com/api).

No API key required. Every place in this codebase that talks to TVMaze
goes through here, so swapping providers later only touches this file.
"""

import httpx

from ..schemas import Episode, ShowDetail, ShowSummary

BASE_URL = "https://api.tvmaze.com"


def _to_show_summary(data: dict) -> ShowSummary:
    return ShowSummary(
        id=data["id"],
        name=data["name"],
        premiered=data.get("premiered"),
        status=data.get("status"),
        image=(data.get("image") or {}).get("medium"),
        summary=data.get("summary"),
    )


def _to_episode(data: dict) -> Episode:
    return Episode(
        id=data["id"],
        season=data["season"],
        number=data["number"],
        name=data["name"],
        airdate=data.get("airdate"),
        airstamp=data.get("airstamp"),
        image=(data.get("image") or {}).get("medium"),
    )


async def search_shows(query: str) -> list[ShowSummary]:
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(f"{BASE_URL}/search/shows", params={"q": query})
        resp.raise_for_status()
        results = resp.json()
    return [_to_show_summary(r["show"]) for r in results]


async def get_show(show_id: int) -> ShowDetail:
    async with httpx.AsyncClient(timeout=10) as client:
        show_resp = await client.get(f"{BASE_URL}/shows/{show_id}")
        show_resp.raise_for_status()
        episodes_resp = await client.get(f"{BASE_URL}/shows/{show_id}/episodes")
        episodes_resp.raise_for_status()

    show_data = show_resp.json()
    episodes_data = episodes_resp.json()

    summary = _to_show_summary(show_data)
    episodes = [_to_episode(e) for e in episodes_data]
    return ShowDetail(**summary.model_dump(), episodes=episodes)


async def get_episodes(show_id: int) -> list[Episode]:
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(f"{BASE_URL}/shows/{show_id}/episodes")
        resp.raise_for_status()
        data = resp.json()
    return [_to_episode(e) for e in data]
