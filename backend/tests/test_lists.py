from app.schemas import ShowDetail

SHOW_ID = 169
OTHER_SHOW_ID = 526


def make_fake_show(show_id=SHOW_ID, name="Breaking Bad"):
    return ShowDetail(
        id=show_id,
        name=name,
        premiered="2008-01-20",
        status="Ended",
        image="https://example.test/poster.jpg",
        summary="<p>Chemistry teacher turns to crime.</p>",
        episodes=[],
    )


async def fake_get_show(show_id):
    return make_fake_show(show_id)


def create_list(client, headers, name="Favorites"):
    resp = client.post("/lists", json={"name": name}, headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_create_list(client, test_user):
    headers = test_user["auth_headers"]
    resp = client.post("/lists", json={"name": "Watch Later"}, headers=headers)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["name"] == "Watch Later"
    assert body["is_public"] is False
    assert "id" in body


def test_list_lists_returns_only_current_users_lists(client, test_user):
    headers = test_user["auth_headers"]
    create_list(client, headers, "Favorites")
    create_list(client, headers, "Watch Later")

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
    create_list(client, other_headers, "Other User's List")

    resp = client.get("/lists", headers=headers)
    assert resp.status_code == 200
    names = {row["name"] for row in resp.json()}
    assert names == {"Favorites", "Watch Later"}


def test_rename_list(client, test_user):
    headers = test_user["auth_headers"]
    show_list = create_list(client, headers, "Favorites")

    resp = client.put(
        f"/lists/{show_list['id']}", json={"name": "Comfort Rewatches"}, headers=headers
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Comfort Rewatches"


def test_rename_nonexistent_list_returns_404(client, test_user):
    headers = test_user["auth_headers"]
    resp = client.put("/lists/999", json={"name": "X"}, headers=headers)
    assert resp.status_code == 404


def test_delete_list(client, test_user):
    headers = test_user["auth_headers"]
    show_list = create_list(client, headers)

    resp = client.delete(f"/lists/{show_list['id']}", headers=headers)
    assert resp.status_code == 204

    resp = client.get("/lists", headers=headers)
    assert resp.json() == []


def test_cannot_rename_or_delete_another_users_list(client, test_user):
    headers = test_user["auth_headers"]
    show_list = create_list(client, headers)

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
        f"/lists/{show_list['id']}", json={"name": "Hijacked"}, headers=other_headers
    )
    assert resp.status_code == 404

    resp = client.delete(f"/lists/{show_list['id']}", headers=other_headers)
    assert resp.status_code == 404


def test_add_show_to_list(client, test_user, mocker):
    mocker.patch("app.routers.lists.tvmaze.get_show", side_effect=fake_get_show)
    headers = test_user["auth_headers"]
    show_list = create_list(client, headers)

    resp = client.post(
        f"/lists/{show_list['id']}/shows",
        json={"tvmaze_show_id": SHOW_ID},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text

    detail = client.get(f"/lists/{show_list['id']}", headers=headers)
    assert detail.status_code == 200
    shows = detail.json()["shows"]
    assert len(shows) == 1
    assert shows[0]["tvmaze_show_id"] == SHOW_ID
    assert shows[0]["name"] == "Breaking Bad"


def test_add_show_to_list_is_idempotent(client, test_user, mocker):
    mocker.patch("app.routers.lists.tvmaze.get_show", side_effect=fake_get_show)
    headers = test_user["auth_headers"]
    show_list = create_list(client, headers)

    client.post(
        f"/lists/{show_list['id']}/shows",
        json={"tvmaze_show_id": SHOW_ID},
        headers=headers,
    )
    resp = client.post(
        f"/lists/{show_list['id']}/shows",
        json={"tvmaze_show_id": SHOW_ID},
        headers=headers,
    )
    assert resp.status_code == 201

    detail = client.get(f"/lists/{show_list['id']}", headers=headers)
    assert len(detail.json()["shows"]) == 1


def test_show_can_belong_to_multiple_lists(client, test_user, mocker):
    mocker.patch("app.routers.lists.tvmaze.get_show", side_effect=fake_get_show)
    headers = test_user["auth_headers"]
    list_a = create_list(client, headers, "Favorites")
    list_b = create_list(client, headers, "Watch Later")

    client.post(
        f"/lists/{list_a['id']}/shows", json={"tvmaze_show_id": SHOW_ID}, headers=headers
    )
    client.post(
        f"/lists/{list_b['id']}/shows", json={"tvmaze_show_id": SHOW_ID}, headers=headers
    )

    detail_a = client.get(f"/lists/{list_a['id']}", headers=headers)
    detail_b = client.get(f"/lists/{list_b['id']}", headers=headers)
    assert len(detail_a.json()["shows"]) == 1
    assert len(detail_b.json()["shows"]) == 1


def test_remove_show_from_list(client, test_user, mocker):
    mocker.patch("app.routers.lists.tvmaze.get_show", side_effect=fake_get_show)
    headers = test_user["auth_headers"]
    show_list = create_list(client, headers)
    client.post(
        f"/lists/{show_list['id']}/shows", json={"tvmaze_show_id": SHOW_ID}, headers=headers
    )

    resp = client.delete(
        f"/lists/{show_list['id']}/shows/{SHOW_ID}", headers=headers
    )
    assert resp.status_code == 204

    detail = client.get(f"/lists/{show_list['id']}", headers=headers)
    assert detail.json()["shows"] == []


def test_list_with_no_shows_returns_empty_list(client, test_user):
    headers = test_user["auth_headers"]
    show_list = create_list(client, headers)

    detail = client.get(f"/lists/{show_list['id']}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["shows"] == []


def test_add_show_requires_owned_list(client, test_user):
    headers = test_user["auth_headers"]
    resp = client.post(
        "/lists/999/shows", json={"tvmaze_show_id": SHOW_ID}, headers=headers
    )
    assert resp.status_code == 404


def test_lists_require_authentication(client):
    resp = client.get("/lists")
    assert resp.status_code == 401
    resp = client.post("/lists", json={"name": "X"})
    assert resp.status_code == 401
