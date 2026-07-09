from fastapi import APIRouter, HTTPException
import httpx

from ..schemas import ShowDetail, ShowSummary
from ..services import tvmaze

router = APIRouter(prefix="/shows", tags=["shows"])


@router.get("/search", response_model=list[ShowSummary])
async def search_shows(q: str):
    if not q.strip():
        return []
    return await tvmaze.search_shows(q)


@router.get("/{show_id}", response_model=ShowDetail)
async def get_show(show_id: int):
    try:
        return await tvmaze.get_show(show_id)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Show not found")
        raise HTTPException(status_code=502, detail="Upstream TVMaze error")
