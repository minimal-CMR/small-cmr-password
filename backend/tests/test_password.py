def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "service": "password"}


def test_update_me_nome(client, user_headers, test_user):
    resp = client.put("/api/users/me", json={"nome": "Luigi"}, headers=user_headers)
    assert resp.status_code == 200
    assert resp.json()["nome"] == "Luigi"


def test_update_me_cognome(client, user_headers):
    resp = client.put("/api/users/me", json={"cognome": "Verdi"}, headers=user_headers)
    assert resp.status_code == 200
    assert resp.json()["cognome"] == "Verdi"


def test_change_password_success(client, user_headers, user_password):
    resp = client.put(
        "/api/users/me",
        json={"password_attuale": user_password, "nuova_password": "newpass456"},
        headers=user_headers,
    )
    assert resp.status_code == 200


def test_change_password_wrong_current(client, user_headers):
    resp = client.put(
        "/api/users/me",
        json={"password_attuale": "sbagliata", "nuova_password": "newpass456"},
        headers=user_headers,
    )
    assert resp.status_code == 400
    assert "attuale" in resp.json()["detail"].lower()


def test_change_password_missing_current(client, user_headers):
    resp = client.put(
        "/api/users/me",
        json={"nuova_password": "newpass456"},
        headers=user_headers,
    )
    assert resp.status_code == 400


def test_unauthenticated(client):
    resp = client.put("/api/users/me", json={"nome": "X"})
    assert resp.status_code == 401
