"""
Unit + integration tests — Authentication
"""
import pytest
from app.core.auth import create_access_token, get_current_user
from app.core.config import settings
from tests.conftest import make_user, auth_headers


class TestTokenCreation:
    def test_creates_token_string(self):
        token = create_access_token({"sub": "user-id-123"})
        assert isinstance(token, str)
        assert len(token) > 20

    def test_different_payloads_produce_different_tokens(self):
        t1 = create_access_token({"sub": "aaa"})
        t2 = create_access_token({"sub": "bbb"})
        assert t1 != t2


class TestLoginEndpoint:
    def test_login_valid_credentials(self, client, db):
        make_user(db, username="alice", password="secret123")
        res = client.post("/api/auth/login", data={"username": "alice", "password": "secret123"})
        assert res.status_code == 200
        body = res.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"

    def test_login_wrong_password(self, client, db):
        make_user(db, username="bob", password="correct")
        res = client.post("/api/auth/login", data={"username": "bob", "password": "wrong"})
        assert res.status_code == 401

    def test_login_unknown_user(self, client):
        res = client.post("/api/auth/login", data={"username": "nobody", "password": "x"})
        assert res.status_code == 401

    def test_login_returns_user_info_via_me(self, client, db):
        user = make_user(db, username="carol", password="pass1234")
        login = client.post("/api/auth/login", data={"username": "carol", "password": "pass1234"})
        token = login.json()["access_token"]
        me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me.status_code == 200
        assert me.json()["username"] == "carol"


class TestProtectedRoutes:
    def test_no_token_returns_401(self, client):
        res = client.get("/api/guards/")
        assert res.status_code == 401

    def test_bad_token_returns_401(self, client):
        res = client.get("/api/guards/", headers={"Authorization": "Bearer garbage"})
        assert res.status_code == 401

    def test_valid_token_grants_access(self, client, db):
        user = make_user(db)
        res = client.get("/api/guards/", headers=auth_headers(user.id))
        assert res.status_code == 200

    def test_health_is_public(self, client):
        res = client.get("/health")
        assert res.status_code == 200
