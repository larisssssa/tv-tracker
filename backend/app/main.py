import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import models
from .db import Base, engine
from .routers import auth, lists, notifications, shows, tracking
from .scheduler import start_scheduler

Base.metadata.create_all(bind=engine)

app = FastAPI(title="TV Tracker API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(shows.router)
app.include_router(tracking.router)
app.include_router(lists.router)
app.include_router(notifications.router)


@app.on_event("startup")
def on_startup():
    # Skip during pytest so tests never poll TVMaze or share scheduler state.
    if os.environ.get("PYTEST_CURRENT_TEST"):
        return
    start_scheduler()


@app.get("/health")
def health():
    return {"status": "ok"}
