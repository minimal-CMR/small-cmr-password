"""Test del router passwords (vault CRUD + share + reveal + unlock)."""
import pytest
from auth import hash_password, create_access_token
from models import User, Team, TeamMember, Password, PasswordShare


# ── Helpers / Fixtures ──────────────────────────────────────────

def _make_user(db, *, email, nome="N", cognome="C", ruolo="opts", password="pw123", ditta_id=None):
    u = User(nome=nome, cognome=cognome, email=email,
             password_hash=hash_password(password), ruolo=ruolo, ditta_id=ditta_id)
    db.add(u); db.commit(); db.refresh(u)
    return u


def _headers(user):
    tok = create_access_token({"sub": str(user.id)})
    return {"Authorization": f"Bearer {tok}"}


@pytest.fixture
def owner(db):
    u = _make_user(db, email="owner@v.test", nome="Owen", cognome="Owner",
                   password="ownerpwd")
    yield u
    db.query(User).filter(User.id == u.id).delete()
    db.commit()


@pytest.fixture
def owner_headers(owner):
    return _headers(owner)


@pytest.fixture
def other_user(db):
    u = _make_user(db, email="other@v.test", nome="O", cognome="Other",
                   password="otherpwd")
    yield u
    db.query(User).filter(User.id == u.id).delete()
    db.commit()


@pytest.fixture
def other_headers(other_user):
    return _headers(other_user)


@pytest.fixture
def admin_user(db):
    u = _make_user(db, email="admin@v.test", nome="A", cognome="Admin",
                   ruolo="admin", password="adminpwd")
    yield u
    db.query(User).filter(User.id == u.id).delete()
    db.commit()


@pytest.fixture
def admin_headers(admin_user):
    return _headers(admin_user)


@pytest.fixture
def saved_password(client, owner_headers):
    r = client.post("/api/passwords", json={
        "service": "Gmail", "account_username": "owen@gmail.com",
        "password": "supersecret", "description": "personale",
        "url": "https://mail.google.com",
    }, headers=owner_headers)
    assert r.status_code == 201, r.text
    return r.json()


# ── Vault unlock ────────────────────────────────────────────────

def test_unlock_vault_correct_password(client, owner_headers):
    r = client.post("/api/passwords/vault/unlock",
                     json={"user_password": "ownerpwd"},
                     headers=owner_headers)
    assert r.status_code == 204


def test_unlock_vault_wrong_password(client, owner_headers):
    r = client.post("/api/passwords/vault/unlock",
                     json={"user_password": "wrong"},
                     headers=owner_headers)
    assert r.status_code == 403


def test_unlock_vault_requires_auth(client):
    r = client.post("/api/passwords/vault/unlock",
                     json={"user_password": "anything"})
    assert r.status_code == 401


# ── Create ──────────────────────────────────────────────────────

def test_create_password(client, owner_headers):
    r = client.post("/api/passwords", json={
        "service": "AWS", "account_username": "admin@example.com",
        "password": "topsecret", "description": "prod",
    }, headers=owner_headers)
    assert r.status_code == 201
    body = r.json()
    assert body["service"] == "AWS"
    assert body["account_username"] == "admin@example.com"
    assert "password" not in body  # mai esposta nel list item
    assert body["owner"]["email"] == "owner@v.test"


def test_create_password_requires_auth(client):
    r = client.post("/api/passwords", json={
        "service": "X", "account_username": "y", "password": "z",
    })
    assert r.status_code == 401


# ── List + filters ──────────────────────────────────────────────

def test_list_own_passwords(client, owner_headers, saved_password):
    r = client.get("/api/passwords", headers=owner_headers)
    assert r.status_code == 200
    items = r.json()
    assert any(p["id"] == saved_password["id"] for p in items)


def test_list_excludes_others(client, owner_headers, other_headers):
    client.post("/api/passwords", json={
        "service": "OtherSvc", "account_username": "o@o", "password": "p",
    }, headers=other_headers)
    items = client.get("/api/passwords", headers=owner_headers).json()
    assert all(p["owner"]["email"] != "other@v.test" for p in items)


def test_list_search_by_service(client, owner_headers, saved_password):
    r = client.get("/api/passwords?service=gmai", headers=owner_headers)
    items = r.json()
    assert all("gmai" in p["service"].lower() for p in items)
    assert any(p["id"] == saved_password["id"] for p in items)


def test_list_search_by_account(client, owner_headers, saved_password):
    r = client.get("/api/passwords?account_username=owen", headers=owner_headers)
    assert any(p["id"] == saved_password["id"] for p in r.json())


def test_list_admin_sees_all(client, admin_headers, owner, saved_password):
    r = client.get("/api/passwords", headers=admin_headers)
    items = r.json()
    assert any(p["id"] == saved_password["id"] for p in items)


def test_list_filter_by_owner_email_admin(client, admin_headers, saved_password):
    r = client.get("/api/passwords?owner_email=owner@v.test", headers=admin_headers)
    assert all(p["owner"]["email"] == "owner@v.test" for p in r.json())


# ── Get one ─────────────────────────────────────────────────────

def test_get_password_owner(client, owner_headers, saved_password):
    r = client.get(f"/api/passwords/{saved_password['id']}", headers=owner_headers)
    assert r.status_code == 200
    assert r.json()["id"] == saved_password["id"]


def test_get_password_other_forbidden(client, other_headers, saved_password):
    r = client.get(f"/api/passwords/{saved_password['id']}", headers=other_headers)
    assert r.status_code == 403


def test_get_password_admin_allowed(client, admin_headers, saved_password):
    r = client.get(f"/api/passwords/{saved_password['id']}", headers=admin_headers)
    assert r.status_code == 200


def test_get_password_not_found(client, owner_headers):
    r = client.get("/api/passwords/999999", headers=owner_headers)
    assert r.status_code == 404


# ── Reveal ──────────────────────────────────────────────────────

def test_reveal_password_correct_pwd(client, owner_headers, saved_password):
    r = client.post(f"/api/passwords/{saved_password['id']}/reveal",
                     json={"user_password": "ownerpwd"}, headers=owner_headers)
    assert r.status_code == 200
    assert r.json()["password"] == "supersecret"


def test_reveal_password_wrong_pwd(client, owner_headers, saved_password):
    r = client.post(f"/api/passwords/{saved_password['id']}/reveal",
                     json={"user_password": "wrong"}, headers=owner_headers)
    assert r.status_code == 403


def test_reveal_password_no_permission(client, other_headers, saved_password):
    r = client.post(f"/api/passwords/{saved_password['id']}/reveal",
                     json={"user_password": "otherpwd"}, headers=other_headers)
    # Prima fallisce sulla password (auth re-check OK), poi su _can_access -> 403
    assert r.status_code == 403


# ── Update ──────────────────────────────────────────────────────

def test_update_password_owner(client, owner_headers, saved_password):
    r = client.put(f"/api/passwords/{saved_password['id']}",
                    json={"description": "nuova desc"}, headers=owner_headers)
    assert r.status_code == 200
    assert r.json()["description"] == "nuova desc"


def test_update_password_change_pwd(client, owner_headers, saved_password):
    r = client.put(f"/api/passwords/{saved_password['id']}",
                    json={"password": "newpw"}, headers=owner_headers)
    assert r.status_code == 200
    # Verifica che il reveal restituisca la nuova
    rev = client.post(f"/api/passwords/{saved_password['id']}/reveal",
                       json={"user_password": "ownerpwd"}, headers=owner_headers)
    assert rev.json()["password"] == "newpw"


def test_update_password_other_forbidden(client, other_headers, saved_password):
    r = client.put(f"/api/passwords/{saved_password['id']}",
                    json={"description": "x"}, headers=other_headers)
    assert r.status_code == 403


# ── Delete ──────────────────────────────────────────────────────

def test_delete_password_owner(client, owner_headers, saved_password):
    r = client.delete(f"/api/passwords/{saved_password['id']}", headers=owner_headers)
    assert r.status_code == 204
    g = client.get(f"/api/passwords/{saved_password['id']}", headers=owner_headers)
    assert g.status_code == 404


def test_delete_password_other_forbidden(client, other_headers, saved_password):
    r = client.delete(f"/api/passwords/{saved_password['id']}", headers=other_headers)
    assert r.status_code == 403


def test_delete_password_admin(client, admin_headers, saved_password):
    r = client.delete(f"/api/passwords/{saved_password['id']}", headers=admin_headers)
    assert r.status_code == 204


# ── Sharing: list / add user / revoke ───────────────────────────

def test_list_shares_empty(client, owner_headers, saved_password):
    r = client.get(f"/api/passwords/{saved_password['id']}/shares", headers=owner_headers)
    assert r.status_code == 200
    assert r.json() == []


def test_share_with_user_read(client, owner_headers, saved_password, other_user):
    r = client.post(f"/api/passwords/{saved_password['id']}/shares",
                     json={"recipients": [{"user_id": other_user.id, "permission": "read"}]},
                     headers=owner_headers)
    assert r.status_code == 201
    shares = r.json()
    assert len(shares) == 1
    assert shares[0]["recipient"]["id"] == other_user.id
    assert shares[0]["permission"] == "read"


def test_shared_user_can_get(client, owner_headers, other_headers, saved_password, other_user):
    client.post(f"/api/passwords/{saved_password['id']}/shares",
                 json={"recipients": [{"user_id": other_user.id, "permission": "read"}]},
                 headers=owner_headers)
    r = client.get(f"/api/passwords/{saved_password['id']}", headers=other_headers)
    assert r.status_code == 200


def test_shared_read_cannot_update(client, owner_headers, other_headers, saved_password, other_user):
    client.post(f"/api/passwords/{saved_password['id']}/shares",
                 json={"recipients": [{"user_id": other_user.id, "permission": "read"}]},
                 headers=owner_headers)
    r = client.put(f"/api/passwords/{saved_password['id']}",
                    json={"description": "hack"}, headers=other_headers)
    assert r.status_code == 403


def test_shared_write_can_update(client, owner_headers, other_headers, saved_password, other_user):
    client.post(f"/api/passwords/{saved_password['id']}/shares",
                 json={"recipients": [{"user_id": other_user.id, "permission": "write"}]},
                 headers=owner_headers)
    r = client.put(f"/api/passwords/{saved_password['id']}",
                    json={"description": "shared edit"}, headers=other_headers)
    assert r.status_code == 200


def test_share_change_permission(client, owner_headers, saved_password, other_user):
    # Prima read, poi write
    client.post(f"/api/passwords/{saved_password['id']}/shares",
                 json={"recipients": [{"user_id": other_user.id, "permission": "read"}]},
                 headers=owner_headers)
    r = client.post(f"/api/passwords/{saved_password['id']}/shares",
                     json={"recipients": [{"user_id": other_user.id, "permission": "write"}]},
                     headers=owner_headers)
    assert r.status_code == 201
    assert r.json()[0]["permission"] == "write"


def test_revoke_share(client, owner_headers, saved_password, other_user, other_headers):
    client.post(f"/api/passwords/{saved_password['id']}/shares",
                 json={"recipients": [{"user_id": other_user.id, "permission": "read"}]},
                 headers=owner_headers)
    r = client.delete(f"/api/passwords/{saved_password['id']}/shares/{other_user.id}",
                       headers=owner_headers)
    assert r.status_code == 204
    # Other non vede più
    g = client.get(f"/api/passwords/{saved_password['id']}", headers=other_headers)
    assert g.status_code == 403


def test_share_non_owner_forbidden(client, other_headers, saved_password, db):
    third = _make_user(db, email="third@v.test", nome="T", cognome="3")
    try:
        r = client.post(f"/api/passwords/{saved_password['id']}/shares",
                         json={"recipients": [{"user_id": third.id, "permission": "read"}]},
                         headers=other_headers)
        assert r.status_code == 403
    finally:
        db.query(User).filter(User.id == third.id).delete()
        db.commit()


# ── Sharing: with team ──────────────────────────────────────────

def test_share_with_team(client, owner_headers, saved_password, db):
    u1 = _make_user(db, email="t1@v.test", nome="T", cognome="1")
    u2 = _make_user(db, email="t2@v.test", nome="T", cognome="2")
    team = Team(name="Dev Team", is_active=1)
    db.add(team); db.commit(); db.refresh(team)
    db.add_all([TeamMember(team_id=team.id, user_id=u1.id),
                 TeamMember(team_id=team.id, user_id=u2.id)])
    db.commit()
    try:
        r = client.post(f"/api/passwords/{saved_password['id']}/shares/team/{team.id}?permission=read",
                         headers=owner_headers)
        assert r.status_code == 201
        recipient_ids = sorted(s["recipient"]["id"] for s in r.json())
        assert recipient_ids == sorted([u1.id, u2.id])
    finally:
        db.query(TeamMember).filter(TeamMember.team_id == team.id).delete()
        db.query(Team).filter(Team.id == team.id).delete()
        db.query(User).filter(User.id.in_([u1.id, u2.id])).delete()
        db.commit()


def test_share_with_team_not_found(client, owner_headers, saved_password):
    r = client.post(f"/api/passwords/{saved_password['id']}/shares/team/999999?permission=read",
                     headers=owner_headers)
    assert r.status_code == 404


# ── Sharing: with ditta ─────────────────────────────────────────

def test_share_with_ditta(client, owner_headers, saved_password, db):
    u1 = _make_user(db, email="d1@v.test", nome="D", cognome="1", ditta_id=42)
    u2 = _make_user(db, email="d2@v.test", nome="D", cognome="2", ditta_id=42)
    u3 = _make_user(db, email="d3@v.test", nome="D", cognome="3", ditta_id=99)  # altra ditta
    try:
        r = client.post(f"/api/passwords/{saved_password['id']}/shares/ditta/42?permission=read",
                         headers=owner_headers)
        assert r.status_code == 201
        recipient_ids = sorted(s["recipient"]["id"] for s in r.json())
        assert recipient_ids == sorted([u1.id, u2.id])
        assert u3.id not in recipient_ids
    finally:
        db.query(User).filter(User.id.in_([u1.id, u2.id, u3.id])).delete()
        db.commit()
