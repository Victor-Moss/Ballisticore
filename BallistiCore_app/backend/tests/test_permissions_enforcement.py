"""Backend enforcement for Access Register / View History / Change Passwords.

Verifies the gaps closed in the "make every permission enforced" change: the
register and history read endpoints (direct + report exports) now require their
flag server-side, and require_change_passwords honours perm_system_admin.
"""
import uuid

from app.models.user import User
from app.models.guard import Guard
from app.services.users import hash_password
from tests.conftest import auth_headers


def _user(db, *, is_admin=False, **perms):
    u = User(
        id=str(uuid.uuid4()),
        username=f"u_{uuid.uuid4().hex[:8]}",
        hashed_password=hash_password("pw"),
        is_active=True,
        is_admin=is_admin,
        **perms,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


def _guard(db):
    g = Guard(id=str(uuid.uuid4()), first_name="Test", last_name="Guard")
    db.add(g)
    db.commit()
    db.refresh(g)
    return g


# ── Access Register (perm_access_database) ────────────────────────────────────

def test_register_read_denied_without_flag(client, db):
    u = _user(db)
    assert client.get("/api/register/", headers=auth_headers(u.id)).status_code == 403
    assert client.get("/api/reports/register", headers=auth_headers(u.id)).status_code == 403


def test_register_read_allowed_with_flag(client, db):
    u = _user(db, perm_access_database=True)
    assert client.get("/api/register/", headers=auth_headers(u.id)).status_code == 200
    assert client.get("/api/reports/register", headers=auth_headers(u.id)).status_code == 200


def test_register_read_allowed_for_super_admin(client, db):
    u = _user(db, is_admin=True)  # super admin bypasses the gate
    assert client.get("/api/register/", headers=auth_headers(u.id)).status_code == 200


# ── View History (perm_view_register_history) ─────────────────────────────────

def test_history_read_denied_without_flag(client, db):
    u = _user(db)
    assert client.get("/api/register/history", headers=auth_headers(u.id)).status_code == 403
    assert client.get("/api/reports/history", headers=auth_headers(u.id)).status_code == 403
    g = _guard(db)
    # Permission is checked before the body runs, so even a real guard → 403.
    assert client.get(f"/api/reports/guard/{g.id}", headers=auth_headers(u.id)).status_code == 403


def test_history_read_allowed_with_flag(client, db):
    u = _user(db, perm_view_register_history=True)
    assert client.get("/api/register/history", headers=auth_headers(u.id)).status_code == 200
    assert client.get("/api/reports/history", headers=auth_headers(u.id)).status_code == 200


def test_access_register_flag_does_not_grant_history(client, db):
    # Flags are independent — Access Register must not leak History access.
    u = _user(db, perm_access_database=True)
    assert client.get("/api/register/history", headers=auth_headers(u.id)).status_code == 403


# ── require_change_passwords honours perm_system_admin ────────────────────────

def test_change_passwords_allows_system_admin_without_is_admin(client, db):
    # Elevated only via perm_system_admin (is_admin=False) — must still pass.
    u = _user(db, perm_system_admin=True)
    g = _guard(db)
    res = client.post(f"/api/guards/{g.id}/account",
                      headers=auth_headers(u.id),
                      json={"username": "newlogin", "password": "secret12"})
    assert res.status_code == 200


def test_change_passwords_denied_without_flag(client, db):
    u = _user(db)
    g = _guard(db)
    res = client.post(f"/api/guards/{g.id}/account",
                      headers=auth_headers(u.id),
                      json={"username": "newlogin", "password": "secret12"})
    assert res.status_code == 403
