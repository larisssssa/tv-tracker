SHOW_ID = 169  # Breaking Bad on TVMaze


def mark_watched(client, headers, episode_id, show_id=SHOW_ID):
    resp = client.post(
        "/tracking/episodes",
        json={"tvmaze_show_id": show_id, "tvmaze_episode_id": episode_id},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    return resp


def track_show(client, headers, show_id=SHOW_ID):
    resp = client.post(
        "/tracking/shows", json={"tvmaze_show_id": show_id}, headers=headers
    )
    assert resp.status_code == 201, resp.text
    return resp


def test_rate_episode_sets_rating(client, test_user):
    headers = test_user["auth_headers"]
    mark_watched(client, headers, 1)

    resp = client.put(
        "/tracking/episodes/1/rating", json={"rating": 4}, headers=headers
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["rating"] == 4

    watched = client.get("/tracking/episodes/watched", headers=headers).json()
    assert next(w for w in watched if w["tvmaze_episode_id"] == 1)["rating"] == 4


def test_rate_episode_can_be_updated(client, test_user):
    headers = test_user["auth_headers"]
    mark_watched(client, headers, 1)

    client.put("/tracking/episodes/1/rating", json={"rating": 2}, headers=headers)
    resp = client.put(
        "/tracking/episodes/1/rating", json={"rating": 5}, headers=headers
    )
    assert resp.status_code == 200
    assert resp.json()["rating"] == 5


def test_rate_episode_requires_episode_to_be_watched(client, test_user):
    headers = test_user["auth_headers"]
    resp = client.put(
        "/tracking/episodes/1/rating", json={"rating": 3}, headers=headers
    )
    assert resp.status_code == 404


def test_rate_episode_rejects_out_of_range_rating(client, test_user):
    headers = test_user["auth_headers"]
    mark_watched(client, headers, 1)

    resp = client.put(
        "/tracking/episodes/1/rating", json={"rating": 6}, headers=headers
    )
    assert resp.status_code == 422

    resp = client.put(
        "/tracking/episodes/1/rating", json={"rating": 0}, headers=headers
    )
    assert resp.status_code == 422


def test_rate_episode_requires_authentication(client):
    resp = client.put("/tracking/episodes/1/rating", json={"rating": 3})
    assert resp.status_code == 401


def test_rate_show_sets_rating(client, test_user):
    headers = test_user["auth_headers"]
    track_show(client, headers)

    resp = client.put(
        f"/tracking/shows/{SHOW_ID}/rating", json={"rating": 5}, headers=headers
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["rating"] == 5


def test_rate_show_requires_show_to_be_tracked(client, test_user):
    headers = test_user["auth_headers"]
    resp = client.put(
        f"/tracking/shows/{SHOW_ID}/rating", json={"rating": 3}, headers=headers
    )
    assert resp.status_code == 404


def test_rate_show_rejects_out_of_range_rating(client, test_user):
    headers = test_user["auth_headers"]
    track_show(client, headers)

    resp = client.put(
        f"/tracking/shows/{SHOW_ID}/rating", json={"rating": 6}, headers=headers
    )
    assert resp.status_code == 422


def test_rate_show_requires_authentication(client):
    resp = client.put(f"/tracking/shows/{SHOW_ID}/rating", json={"rating": 3})
    assert resp.status_code == 401


def test_rate_show_does_not_affect_other_users(client, test_user):
    headers = test_user["auth_headers"]
    track_show(client, headers)
    client.put(
        f"/tracking/shows/{SHOW_ID}/rating", json={"rating": 5}, headers=headers
    )

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

    resp = client.put(
        f"/tracking/shows/{SHOW_ID}/rating", json={"rating": 1}, headers=other_headers
    )
    assert resp.status_code == 404
