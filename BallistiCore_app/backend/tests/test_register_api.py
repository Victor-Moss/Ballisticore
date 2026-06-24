"""
Integration tests — Register API (/api/register)
Full issuance + return flow through the HTTP layer.
"""
import pytest
from tests.conftest import make_user, make_guard, make_firearm, make_permission, auth_headers


@pytest.fixture
def setup(db):
    """Returns (user, guard, firearm, headers) with permission already set."""
    user = make_user(db)
    guard = make_guard(db)
    firearm = make_firearm(db)
    make_permission(db, guard.id, firearm.id)
    headers = auth_headers(user.id)
    return user, guard, firearm, headers


# make_user()'s default password — satisfies the mandatory issuer/staff
# e-signature on issue/return. Guards here have no sign-in account, so no guard
# password is needed.
PASSWORD = "testpass"


def issue(client, guard_id, firearm_id, user_id, headers):
    return client.post("/api/register/issue", json={
        "guard_id": guard_id,
        "firearm_id": firearm_id,
        "issued_by": user_id,
        "issuer_password": PASSWORD,
    }, headers=headers)


def ret(client, firearm_id, user_id, headers):
    return client.post("/api/register/return", json={
        "firearm_id": firearm_id,
        "actioned_by": user_id,
        "staff_password": PASSWORD,
    }, headers=headers)


class TestCurrentRegister:
    def test_empty_register(self, client, db, setup):
        _, _, _, headers = setup
        res = client.get("/api/register/", headers=headers)
        assert res.status_code == 200
        assert res.json() == []

    def test_register_shows_issued_firearm(self, client, db, setup):
        user, guard, firearm, headers = setup
        issue(client, guard.id, firearm.id, user.id, headers)
        res = client.get("/api/register/", headers=headers)
        assert res.status_code == 200
        entries = res.json()
        assert len(entries) == 1
        assert entries[0]["guard_id"] == guard.id
        assert entries[0]["firearm_id"] == firearm.id


class TestIssueEndpoint:
    def test_successful_issue(self, client, db, setup):
        user, guard, firearm, headers = setup
        res = issue(client, guard.id, firearm.id, user.id, headers)
        assert res.status_code == 200
        body = res.json()
        assert body["guard_id"] == guard.id
        assert body["firearm_id"] == firearm.id

    def test_double_booking_returns_409(self, client, db, setup):
        user, guard, firearm, headers = setup
        guard2 = make_guard(db, first_name="Guard", last_name="Two", id_number="2222222222222")
        make_permission(db, guard2.id, firearm.id)

        issue(client, guard.id, firearm.id, user.id, headers)
        res = issue(client, guard2.id, firearm.id, user.id, headers)
        assert res.status_code == 409

    def test_no_permission_returns_403(self, client, db):
        user = make_user(db)
        guard = make_guard(db)
        firearm = make_firearm(db)
        # No permission created
        headers = auth_headers(user.id)
        res = issue(client, guard.id, firearm.id, user.id, headers)
        assert res.status_code == 403

    def test_inactive_guard_returns_4xx(self, client, db):
        user = make_user(db)
        guard = make_guard(db, is_active=False)
        firearm = make_firearm(db)
        make_permission(db, guard.id, firearm.id)
        headers = auth_headers(user.id)
        res = issue(client, guard.id, firearm.id, user.id, headers)
        assert res.status_code in (400, 404)

    def test_issue_creates_permit(self, client, db, setup):
        user, guard, firearm, headers = setup
        issue(client, guard.id, firearm.id, user.id, headers)
        permits_res = client.get("/api/permits/", headers=headers)
        assert permits_res.status_code == 200
        assert len(permits_res.json()) == 1


class TestReturnEndpoint:
    def test_successful_return(self, client, db, setup):
        user, guard, firearm, headers = setup
        issue(client, guard.id, firearm.id, user.id, headers)
        res = ret(client, firearm.id, user.id, headers)
        assert res.status_code == 200

    def test_register_empty_after_return(self, client, db, setup):
        user, guard, firearm, headers = setup
        issue(client, guard.id, firearm.id, user.id, headers)
        ret(client, firearm.id, user.id, headers)
        register = client.get("/api/register/", headers=headers)
        assert register.json() == []

    def test_return_unissued_firearm_returns_404(self, client, db, setup):
        user, _, firearm, headers = setup
        res = ret(client, firearm.id, user.id, headers)
        assert res.status_code == 404


class TestHistory:
    def test_history_records_issue_and_return(self, client, db, setup):
        user, guard, firearm, headers = setup
        issue(client, guard.id, firearm.id, user.id, headers)
        ret(client, firearm.id, user.id, headers)

        res = client.get("/api/register/history", headers=headers)
        assert res.status_code == 200
        entries = res.json()
        actions = {e["action"].lower() for e in entries}
        assert "issued" in actions
        assert "returned" in actions

    def test_history_filter_by_guard(self, client, db, setup):
        user, guard, firearm, headers = setup
        guard2 = make_guard(db, first_name="X", last_name="Y", id_number="2222222222222")
        fa2 = make_firearm(db, serial_number="GUN-002")
        make_permission(db, guard2.id, fa2.id)

        issue(client, guard.id, firearm.id, user.id, headers)
        issue(client, guard2.id, fa2.id, user.id, headers)

        res = client.get(f"/api/register/history?guard_id={guard.id}", headers=headers)
        entries = res.json()
        assert all(e["guard_id"] == guard.id for e in entries)
        assert len(entries) == 1
