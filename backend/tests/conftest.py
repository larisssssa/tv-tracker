import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.db import Base, get_db
from app.main import app


@pytest.fixture()
def db_session():
    """A fresh in-memory SQLite DB, isolated per test."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture()
def client(db_session):
    """A TestClient wired to the isolated test DB instead of the real dev DB."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def test_user(client):
    """Registers a user via the real /auth/register + /auth/login endpoints
    and returns their credentials, id, and a ready-to-use auth header.

    Goes through the actual API rather than inserting a User row directly,
    so the fixture stays correct if registration/hashing logic ever changes.
    """
    email = "fixture-user@example.com"
    password = "fixture-password-123"

    register_resp = client.post(
        "/auth/register", json={"email": email, "password": password}
    )
    assert register_resp.status_code == 201, register_resp.text
    user_id = register_resp.json()["id"]

    login_resp = client.post(
        "/auth/login",
        data={"username": email, "password": password},
    )
    assert login_resp.status_code == 200, login_resp.text
    token = login_resp.json()["access_token"]

    return {
        "id": user_id,
        "email": email,
        "password": password,
        "token": token,
        "auth_headers": {"Authorization": f"Bearer {token}"},
    }
