"""
Integration tests — Guards API (/api/guards)
"""
import pytest
from tests.conftest import make_user, make_guard, auth_headers


@pytest.fixture
def headers(db):
    user = make_user(db)
    return auth_headers(user.id)


class TestListGuards:
    def test_returns_empty_list(self, client, db, headers):
        res = client.get("/api/guards/", headers=headers)
        assert res.status_code == 200
        assert res.json() == []

    def test_returns_active_guards(self, client, db, headers):
        make_guard(db)
        res = client.get("/api/guards/", headers=headers)
        assert res.status_code == 200
        assert len(res.json()) == 1

    def test_excludes_inactive_by_default(self, client, db, headers):
        make_guard(db, is_active=True, id_number="1111111111111")
        make_guard(db, is_active=False, id_number="2222222222222")
        res = client.get("/api/guards/", headers=headers)
        assert len(res.json()) == 1

    def test_include_inactive_flag(self, client, db, headers):
        make_guard(db, is_active=True, id_number="1111111111111")
        make_guard(db, is_active=False, id_number="2222222222222")
        res = client.get("/api/guards/?include_inactive=true", headers=headers)
        assert len(res.json()) == 2


class TestCreateGuard:
    def test_create_guard_success(self, client, db, headers):
        payload = {
            "first_name": "Alice",
            "last_name": "Smith",
            "id_number": "9001015009087",
            "psira_number": "PS9999999",
        }
        res = client.post("/api/guards/", json=payload, headers=headers)
        assert res.status_code in (200, 201)
        body = res.json()
        assert body["first_name"] == "Alice"
        assert body["is_active"] is True

    def test_create_guard_missing_required_field(self, client, db, headers):
        res = client.post("/api/guards/", json={"last_name": "Smith"}, headers=headers)
        assert res.status_code == 422

    def test_duplicate_id_number_blocked(self, client, db, headers):
        make_guard(db, id_number="9001015009087")
        payload = {"first_name": "Bob", "last_name": "Jones", "id_number": "9001015009087"}
        res = client.post("/api/guards/", json=payload, headers=headers)
        assert res.status_code == 409


class TestDeactivateReactivate:
    def test_deactivate_guard(self, client, db, headers):
        guard = make_guard(db)
        res = client.put(f"/api/guards/{guard.id}/deactivate", headers=headers)
        assert res.status_code == 200
        assert res.json()["is_active"] is False

    def test_reactivate_guard(self, client, db, headers):
        guard = make_guard(db, is_active=False)
        res = client.put(f"/api/guards/{guard.id}/reactivate", headers=headers)
        assert res.status_code == 200
        assert res.json()["is_active"] is True

    def test_deactivate_nonexistent_returns_404(self, client, db, headers):
        res = client.put("/api/guards/bad-id/deactivate", headers=headers)
        assert res.status_code == 404
