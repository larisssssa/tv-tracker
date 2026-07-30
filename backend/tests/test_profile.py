from app.schemas import ShowDetail

SHOW_ID = 169


async def fake_get_show(show_id):
    return ShowDetail(
        id=show_id,
        name="Breaking Bad",
        premiered="2008-01-20",
        status="Ended",
        image=None,
        summary=None,
        episodes=[],
    )


def test_get_me_returns_current_user(client, test_user):
    headers = test_user["auth_headers"]
    resp = client.get("/auth/me", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == test_user["email"]
    assert body["id"] == test_user["id"]
    assert "created_at" in body
    assert "password" not in body
    assert "hashed_password" not in body


def test_get_me_requires_authentication(client):
    resp = client.get("/auth/me")
    assert resp.status_code == 401


def test_stats_are_zero_for_new_user(client, test_user):
    headers = test_user["auth_headers"]
    resp = client.get("/auth/me/stats", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["shows_tracked"] == 0
    assert body["episodes_watched"] == 0
    assert "member_since" in body


def test_stats_reflect_tracked_shows_and_watched_episodes(client, test_user, mocker):
    mocker.patch("app.routers.tracking.tvmaze.get_show", side_effect=fake_get_show)
    headers = test_user["auth_headers"]

    client.post("/tracking/shows", json={"tvmaze_show_id": SHOW_ID}, headers=headers)
    client.post("/tracking/shows", json={"tvmaze_show_id": 526}, headers=headers)
    client.post(
        "/tracking/episodes/bulk",
        json={"tvmaze_show_id": SHOW_ID, "tvmaze_episode_ids": [1, 2, 3]},
        headers=headers,
    )

    resp = client.get("/auth/me/stats", headers=headers)
    body = resp.json()
    assert body["shows_tracked"] == 2
    assert body["episodes_watched"] == 3


def test_stats_survive_untracking_a_show(client, test_user, mocker):
    """Untracking never deletes WatchedEpisode rows (see issue #6), so the
    episodes_watched stat should not drop when a show is removed."""
    mocker.patch("app.routers.tracking.tvmaze.get_show", side_effect=fake_get_show)
    headers = test_user["auth_headers"]

    client.post("/tracking/shows", json={"tvmaze_show_id": SHOW_ID}, headers=headers)
    client.post(
        "/tracking/episodes/bulk",
        json={"tvmaze_show_id": SHOW_ID, "tvmaze_episode_ids": [1, 2]},
        headers=headers,
    )
    client.delete(f"/tracking/shows/{SHOW_ID}", headers=headers)

    resp = client.get("/auth/me/stats", headers=headers)
    body = resp.json()
    assert body["shows_tracked"] == 0
    assert body["episodes_watched"] == 2


def test_stats_do_not_include_other_users_data(client, test_user, mocker):
    mocker.patch("app.routers.tracking.tvmaze.get_show", side_effect=fake_get_show)
    headers = test_user["auth_headers"]
    client.post("/tracking/shows", json={"tvmaze_show_id": SHOW_ID}, headers=headers)

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

    resp = client.get("/auth/me/stats", headers=other_headers)
    body = resp.json()
    assert body["shows_tracked"] == 0
    assert body["episodes_watched"] == 0


def test_stats_require_authentication(client):
    resp = client.get("/auth/me/stats")
    assert resp.status_code == 401
