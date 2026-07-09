SHOW_ID = 169  # Breaking Bad on TVMaze


def mark_watched(client, headers, episode_id, show_id=SHOW_ID):
    resp = client.post(
        "/tracking/episodes",
        json={"tvmaze_show_id": show_id, "tvmaze_episode_id": episode_id},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    return resp


def get_watched_ids(client, headers):
    resp = client.get("/tracking/episodes/watched", headers=headers)
    assert resp.status_code == 200
    return {row["tvmaze_episode_id"] for row in resp.json()}


def test_bulk_mark_watched_creates_all_episodes(client, test_user):
    headers = test_user["auth_headers"]
    resp = client.post(
        "/tracking/episodes/bulk",
        json={"tvmaze_show_id": SHOW_ID, "tvmaze_episode_ids": [1, 2, 3]},
        headers=headers,
    )
    assert resp.status_code == 201
    assert get_watched_ids(client, headers) == {1, 2, 3}


def test_bulk_mark_watched_is_idempotent(client, test_user):
    headers = test_user["auth_headers"]
    mark_watched(client, headers, 1)

    resp = client.post(
        "/tracking/episodes/bulk",
        json={"tvmaze_show_id": SHOW_ID, "tvmaze_episode_ids": [1, 2, 3]},
        headers=headers,
    )
    assert resp.status_code == 201
    assert get_watched_ids(client, headers) == {1, 2, 3}


def test_bulk_unmark_deletes_only_requested_episodes(client, test_user):
    headers = test_user["auth_headers"]
    for episode_id in (1, 2, 3):
        mark_watched(client, headers, episode_id)

    resp = client.post(
        "/tracking/episodes/bulk-unmark",
        json={"tvmaze_episode_ids": [1, 2]},
        headers=headers,
    )
    assert resp.status_code == 204
    assert get_watched_ids(client, headers) == {3}


def test_bulk_unmark_is_idempotent(client, test_user):
    headers = test_user["auth_headers"]
    mark_watched(client, headers, 1)

    first = client.post(
        "/tracking/episodes/bulk-unmark",
        json={"tvmaze_episode_ids": [1]},
        headers=headers,
    )
    assert first.status_code == 204

    second = client.post(
        "/tracking/episodes/bulk-unmark",
        json={"tvmaze_episode_ids": [1]},
        headers=headers,
    )
    assert second.status_code == 204
    assert get_watched_ids(client, headers) == set()


def test_bulk_unmark_with_empty_list_is_a_noop(client, test_user):
    headers = test_user["auth_headers"]
    mark_watched(client, headers, 1)

    resp = client.post(
        "/tracking/episodes/bulk-unmark",
        json={"tvmaze_episode_ids": []},
        headers=headers,
    )
    assert resp.status_code == 204
    assert get_watched_ids(client, headers) == {1}


def test_bulk_unmark_does_not_affect_other_users(client, test_user):
    headers = test_user["auth_headers"]
    mark_watched(client, headers, 1)

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
    mark_watched(client, other_headers, 1)

    client.post(
        "/tracking/episodes/bulk-unmark",
        json={"tvmaze_episode_ids": [1]},
        headers=headers,
    )

    assert get_watched_ids(client, headers) == set()
    assert get_watched_ids(client, other_headers) == {1}


def test_bulk_unmark_requires_authentication(client):
    resp = client.post(
        "/tracking/episodes/bulk-unmark",
        json={"tvmaze_episode_ids": [1]},
    )
    assert resp.status_code == 401
