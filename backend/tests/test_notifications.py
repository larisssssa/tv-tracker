import asyncio
from datetime import datetime, timedelta, timezone

from app.models import PendingNotification
from app.scheduler import poll_upcoming_episodes
from app.schemas import Episode, ShowDetail

SHOW_ID = 169

FUTURE = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()
PAST = (datetime.now(timezone.utc) - timedelta(days=3)).isoformat()


def make_show_with_episodes(episodes):
    return ShowDetail(
        id=SHOW_ID,
        name="Breaking Bad",
        premiered="2008-01-20",
        status="Running",
        image=None,
        summary=None,
        episodes=episodes,
    )


def ep(id_, airstamp, airdate="2099-01-01"):
    return Episode(
        id=id_, season=1, number=id_, name=f"Episode {id_}", airdate=airdate, airstamp=airstamp
    )


def test_poll_creates_notification_for_upcoming_episode(client, test_user, db_session, mocker):
    headers = test_user["auth_headers"]
    client.post("/tracking/shows", json={"tvmaze_show_id": SHOW_ID}, headers=headers)

    show = make_show_with_episodes([ep(1, PAST), ep(2, FUTURE)])

    async def fake_get_show(show_id):
        return show

    mocker.patch("app.scheduler.tvmaze.get_show", side_effect=fake_get_show)

    asyncio.run(poll_upcoming_episodes(db=db_session))

    notifications = db_session.query(PendingNotification).all()
    assert len(notifications) == 1
    assert notifications[0].tvmaze_episode_id == 2


def test_poll_does_not_notify_for_aired_episodes(client, test_user, db_session, mocker):
    headers = test_user["auth_headers"]
    client.post("/tracking/shows", json={"tvmaze_show_id": SHOW_ID}, headers=headers)

    show = make_show_with_episodes([ep(1, PAST)])

    async def fake_get_show(show_id):
        return show

    mocker.patch("app.scheduler.tvmaze.get_show", side_effect=fake_get_show)

    asyncio.run(poll_upcoming_episodes(db=db_session))

    assert db_session.query(PendingNotification).count() == 0


def test_poll_does_not_duplicate_existing_notifications(client, test_user, db_session, mocker):
    headers = test_user["auth_headers"]
    client.post("/tracking/shows", json={"tvmaze_show_id": SHOW_ID}, headers=headers)

    show = make_show_with_episodes([ep(2, FUTURE)])

    async def fake_get_show(show_id):
        return show

    mocker.patch("app.scheduler.tvmaze.get_show", side_effect=fake_get_show)

    asyncio.run(poll_upcoming_episodes(db=db_session))
    asyncio.run(poll_upcoming_episodes(db=db_session))

    assert db_session.query(PendingNotification).count() == 1


def test_poll_covers_multiple_tracked_shows(client, test_user, db_session, mocker):
    headers = test_user["auth_headers"]
    client.post("/tracking/shows", json={"tvmaze_show_id": SHOW_ID}, headers=headers)
    client.post("/tracking/shows", json={"tvmaze_show_id": 526}, headers=headers)

    async def fake_get_show(show_id):
        return make_show_with_episodes([ep(show_id * 100 + 1, FUTURE)])

    mocker.patch("app.scheduler.tvmaze.get_show", side_effect=fake_get_show)

    asyncio.run(poll_upcoming_episodes(db=db_session))

    assert db_session.query(PendingNotification).count() == 2


def _seed_notification(db_session, user_id, episode_id=2, air_date="2099-01-05"):
    notification = PendingNotification(
        user_id=user_id,
        tvmaze_show_id=SHOW_ID,
        tvmaze_episode_id=episode_id,
        air_date=air_date,
    )
    db_session.add(notification)
    db_session.commit()
    db_session.refresh(notification)
    return notification


def test_list_notifications_returns_unread_ordered_by_air_date(client, test_user, db_session):
    user_id = test_user["id"]
    _seed_notification(db_session, user_id, episode_id=1, air_date="2099-02-01")
    _seed_notification(db_session, user_id, episode_id=2, air_date="2099-01-01")

    resp = client.get("/notifications", headers=test_user["auth_headers"])
    assert resp.status_code == 200
    body = resp.json()
    assert [n["tvmaze_episode_id"] for n in body] == [2, 1]


def test_list_notifications_excludes_read(client, test_user, db_session):
    user_id = test_user["id"]
    notification = _seed_notification(db_session, user_id)
    notification.read_at = datetime.now(timezone.utc)
    db_session.commit()

    resp = client.get("/notifications", headers=test_user["auth_headers"])
    assert resp.json() == []


def test_mark_notification_read(client, test_user, db_session):
    notification = _seed_notification(db_session, test_user["id"])

    resp = client.post(
        f"/notifications/{notification.id}/read", headers=test_user["auth_headers"]
    )
    assert resp.status_code == 200
    assert resp.json()["read_at"] is not None

    resp = client.get("/notifications", headers=test_user["auth_headers"])
    assert resp.json() == []


def test_mark_notification_read_requires_ownership(client, test_user, db_session):
    notification = _seed_notification(db_session, test_user["id"])

    other_register = client.post(
        "/auth/register",
        json={"email": "other-user@example.com", "password": "somepassword123"},
    )
    assert other_register.status_code == 201
    other_login = client.post(
        "/auth/login",
        data={"username": "other-user@example.com", "password": "somepassword123"},
    )
    other_headers = {"Authorization": f"Bearer {other_login.json()['access_token']}"}

    resp = client.post(f"/notifications/{notification.id}/read", headers=other_headers)
    assert resp.status_code == 404


def test_mark_nonexistent_notification_returns_404(client, test_user):
    resp = client.post("/notifications/999/read", headers=test_user["auth_headers"])
    assert resp.status_code == 404


def test_notifications_do_not_leak_across_users(client, test_user, db_session):
    _seed_notification(db_session, test_user["id"])

    other_register = client.post(
        "/auth/register",
        json={"email": "other-user@example.com", "password": "somepassword123"},
    )
    assert other_register.status_code == 201
    other_login = client.post(
        "/auth/login",
        data={"username": "other-user@example.com", "password": "somepassword123"},
    )
    other_headers = {"Authorization": f"Bearer {other_login.json()['access_token']}"}

    resp = client.get("/notifications", headers=other_headers)
    assert resp.json() == []


def test_notifications_require_authentication(client):
    resp = client.get("/notifications")
    assert resp.status_code == 401
    resp = client.post("/notifications/1/read")
    assert resp.status_code == 401
