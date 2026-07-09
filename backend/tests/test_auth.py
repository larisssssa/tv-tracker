def test_register_returns_user(client):
    resp = client.post(
        "/auth/register",
        json={"email": "new@example.com", "password": "somepassword"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "new@example.com"
    assert "id" in body
    assert "password" not in body


def test_register_rejects_duplicate_email(client):
    payload = {"email": "dupe@example.com", "password": "somepassword"}
    first = client.post("/auth/register", json=payload)
    assert first.status_code == 201

    second = client.post("/auth/register", json=payload)
    assert second.status_code == 400


def test_login_rejects_wrong_password(client):
    client.post(
        "/auth/register",
        json={"email": "wrongpass@example.com", "password": "correct-password"},
    )
    resp = client.post(
        "/auth/login",
        data={"username": "wrongpass@example.com", "password": "incorrect"},
    )
    assert resp.status_code == 401


def test_test_user_fixture_is_authenticated(test_user, client):
    resp = client.get(
        "/tracking/shows", headers=test_user["auth_headers"]
    )
    assert resp.status_code == 200
    assert resp.json() == []


def test_unauthenticated_request_is_rejected(client):
    resp = client.get("/tracking/shows")
    assert resp.status_code == 401
