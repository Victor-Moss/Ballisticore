"""
Guard sign-in accounts + electronic signature at issue.

Covers:
  - operator creates/sets a guard account (explicit + generated password)
  - a guard WITH an account must sign (correct password) to be issued
  - a guard WITHOUT an account is issued unsigned
  - operator password reset invalidates the old password
  - WhatsApp OTP reset flow (service-level) + self-service endpoints
  - permission gating (require_change_passwords)
"""
import pytest
from datetime import datetime, timedelta

from app.services import guard_auth
from app.services import whatsapp as wa
from tests.conftest import make_user, make_guard, make_firearm, make_permission, auth_headers


@pytest.fixture(autouse=True)
def no_whatsapp(monkeypatch):
    """Never hit Twilio during tests, regardless of .env credentials."""
    monkeypatch.setattr(wa, "send_permit_whatsapp", lambda *a, **k: True)
    monkeypatch.setattr(wa, "send_guard_otp", lambda *a, **k: True)
    monkeypatch.setattr(wa, "send_guard_username", lambda *a, **k: True)
    monkeypatch.setattr(wa, "_send_text", lambda *a, **k: True)


@pytest.fixture
def setup(db):
    """(user, guard, firearm, headers) with permission set; guard has a cell."""
    user = make_user(db)
    guard = make_guard(db)
    guard.cell_phone = "0821234567"
    db.commit()
    firearm = make_firearm(db)
    make_permission(db, guard.id, firearm.id)
    return user, guard, firearm, auth_headers(user.id)


def set_account(client, guard_id, headers, username="jsmith", password="guardpass"):
    return client.post(f"/api/guards/{guard_id}/account",
                       json={"username": username, "password": password}, headers=headers)


def issue(client, guard_id, firearm_id, user_id, headers, guard_password=None):
    # The issuing operator's e-signature is always required. make_user()'s default
    # password is "testpass"; the guard's own signature (guard_password) is only
    # supplied by tests that exercise the guard-account signing path.
    payload = {"guard_id": guard_id, "firearm_id": firearm_id, "issued_by": user_id,
               "issuer_password": "testpass"}
    if guard_password is not None:
        payload["guard_password"] = guard_password
    return client.post("/api/register/issue", json=payload, headers=headers)


# --- Account management ------------------------------------------------------

class TestAccountManagement:
    def test_set_account_with_explicit_password(self, client, db, setup):
        _, guard, _, headers = setup
        res = set_account(client, guard.id, headers)
        assert res.status_code == 200
        body = res.json()
        assert body["username"] == "jsmith"
        assert body["has_account"] is True
        assert body["must_change_password"] is False
        assert body["temp_password"] is None

    def test_set_account_generates_temp_password(self, client, db, setup):
        _, guard, _, headers = setup
        res = client.post(f"/api/guards/{guard.id}/account",
                          json={"username": "jsmith"}, headers=headers)
        assert res.status_code == 200
        body = res.json()
        assert body["must_change_password"] is True
        assert body["temp_password"] and len(body["temp_password"]) >= 8

    def test_duplicate_username_rejected(self, client, db, setup):
        user, guard, _, headers = setup
        guard2 = make_guard(db, first_name="A", last_name="B", id_number="2222222222222")
        set_account(client, guard.id, headers, username="dup")
        res = set_account(client, guard2.id, headers, username="dup")
        assert res.status_code == 409

    def test_guard_out_exposes_account_flag_not_password(self, client, db, setup):
        _, guard, _, headers = setup
        set_account(client, guard.id, headers)
        res = client.get(f"/api/guards/{guard.id}", headers=headers)
        body = res.json()
        assert body["has_account"] is True
        assert body["username"] == "jsmith"
        assert "hashed_password" not in body

    def test_non_privileged_user_cannot_manage_accounts(self, client, db, setup):
        _, guard, _, _ = setup
        weak = make_user(db, username="weak", is_admin=False)
        res = set_account(client, guard.id, auth_headers(weak.id))
        assert res.status_code == 403

    def test_create_guard_with_account_in_one_step(self, client, db):
        user = make_user(db)
        headers = auth_headers(user.id)
        res = client.post("/api/guards/", json={
            "first_name": "New", "last_name": "Hire", "id_number": "8888888888888",
            "username": "nhire", "password": "letmein1",
        }, headers=headers)
        assert res.status_code == 201
        body = res.json()
        assert body["has_account"] is True
        assert body["username"] == "nhire"
        # the account password works for signing
        guard = guard_auth.get_by_username(db, "nhire")
        assert guard_auth.verify_guard_password(guard, "letmein1") is True

    def test_create_guard_with_taken_username_409_no_orphan(self, client, db):
        user = make_user(db)
        headers = auth_headers(user.id)
        existing = make_guard(db, id_number="1212121212121")
        guard_auth.set_account(db, existing, "taken", "pw")
        res = client.post("/api/guards/", json={
            "first_name": "Clash", "last_name": "User", "id_number": "1313131313131",
            "username": "taken", "password": "letmein1",
        }, headers=headers)
        assert res.status_code == 409
        # the clashing guard must NOT have been created
        all_guards = client.get("/api/guards/?include_inactive=true", headers=headers).json()
        assert not any(g["id_number"] == "1313131313131" for g in all_guards)


# --- Signing at issue --------------------------------------------------------

class TestSigningAtIssue:
    def test_guard_without_account_issued_unsigned(self, client, db, setup):
        user, guard, firearm, headers = setup
        res = issue(client, guard.id, firearm.id, user.id, headers)
        assert res.status_code == 200
        assert res.json()["guard_signed"] is False

    def test_guard_with_account_requires_password(self, client, db, setup):
        user, guard, firearm, headers = setup
        set_account(client, guard.id, headers)
        res = issue(client, guard.id, firearm.id, user.id, headers)  # no password
        assert res.status_code == 400

    def test_wrong_password_blocks_issue(self, client, db, setup):
        user, guard, firearm, headers = setup
        set_account(client, guard.id, headers)
        res = issue(client, guard.id, firearm.id, user.id, headers, guard_password="wrong")
        assert res.status_code == 403
        # firearm must NOT have been issued
        reg = client.get("/api/register/", headers=headers).json()
        assert reg == []

    def test_correct_password_signs_and_issues(self, client, db, setup):
        user, guard, firearm, headers = setup
        set_account(client, guard.id, headers)
        res = issue(client, guard.id, firearm.id, user.id, headers, guard_password="guardpass")
        assert res.status_code == 200
        body = res.json()
        assert body["guard_signed"] is True
        assert body["guard_signed_at"] is not None

    def test_operator_reset_invalidates_old_password(self, client, db, setup):
        user, guard, firearm, headers = setup
        set_account(client, guard.id, headers)
        reset = client.put(f"/api/guards/{guard.id}/account/reset-password", headers=headers)
        assert reset.status_code == 200
        new_temp = reset.json()["temp_password"]
        # old password rejected
        assert issue(client, guard.id, firearm.id, user.id, headers,
                     guard_password="guardpass").status_code == 403
        # new temp password works
        assert issue(client, guard.id, firearm.id, user.id, headers,
                     guard_password=new_temp).status_code == 200


# --- OTP reset (service level) ----------------------------------------------

class TestOtpReset:
    def test_otp_happy_path(self, db):
        guard = make_guard(db, id_number="3333333333333")
        guard.cell_phone = "0820000000"
        guard_auth.set_account(db, guard, "otpuser", "oldpass")
        otp = guard_auth.start_otp_reset(db, guard)
        ok, _ = guard_auth.verify_otp_and_set_password(db, guard, otp, "brandnew")
        assert ok is True
        assert guard_auth.verify_guard_password(guard, "brandnew") is True
        assert guard_auth.verify_guard_password(guard, "oldpass") is False

    def test_wrong_otp_rejected_and_counts(self, db):
        guard = make_guard(db, id_number="4444444444444")
        guard_auth.set_account(db, guard, "otpuser2", "oldpass")
        guard_auth.start_otp_reset(db, guard)
        ok, _ = guard_auth.verify_otp_and_set_password(db, guard, "000000", "brandnew")
        assert ok is False
        assert guard.reset_otp_attempts == 1
        assert guard_auth.verify_guard_password(guard, "oldpass") is True

    def test_expired_otp_rejected(self, db):
        guard = make_guard(db, id_number="5555555555555")
        guard_auth.set_account(db, guard, "otpuser3", "oldpass")
        otp = guard_auth.start_otp_reset(db, guard)
        guard.reset_otp_expires_at = datetime.utcnow() - timedelta(minutes=1)
        db.commit()
        ok, msg = guard_auth.verify_otp_and_set_password(db, guard, otp, "brandnew")
        assert ok is False
        assert "expired" in msg.lower()

    def test_attempts_lockout(self, db):
        guard = make_guard(db, id_number="6666666666666")
        guard_auth.set_account(db, guard, "otpuser4", "oldpass")
        otp = guard_auth.start_otp_reset(db, guard)
        for _ in range(guard_auth.OTP_MAX_ATTEMPTS):
            guard_auth.verify_otp_and_set_password(db, guard, "000000", "x")
        # even the correct OTP now fails because the lock tripped / otp cleared
        ok, _ = guard_auth.verify_otp_and_set_password(db, guard, otp, "brandnew")
        assert ok is False


# --- Self-service endpoints (public) ----------------------------------------

class TestSelfServiceEndpoints:
    def test_request_reset_is_generic(self, client, db):
        # unknown username still returns generic 200 (no enumeration)
        res = client.post("/api/guard-account/request-reset", json={"username": "ghost"})
        assert res.status_code == 200

    def test_forgot_username_requires_identifier(self, client, db):
        res = client.post("/api/guard-account/forgot-username", json={})
        assert res.status_code == 400

    def test_reset_password_with_endpoint(self, client, db):
        guard = make_guard(db, id_number="7777777777777")
        guard.cell_phone = "0820000001"
        guard_auth.set_account(db, guard, "enduser", "oldpass")
        otp = guard_auth.start_otp_reset(db, guard)
        res = client.post("/api/guard-account/reset-password",
                          json={"username": "enduser", "otp": otp, "new_password": "freshpass"})
        assert res.status_code == 200
        assert guard_auth.verify_guard_password(guard, "freshpass") is True

    def test_reset_password_unknown_user_generic_400(self, client, db):
        res = client.post("/api/guard-account/reset-password",
                          json={"username": "nobody", "otp": "123456", "new_password": "freshpass"})
        assert res.status_code == 400
