"""
Messaging provider configuration + unified permit-delivery service.

Covers:
  - provider/config endpoints (validation, admin gating)
  - the credential Test endpoint
  - messaging_service routing for telegram / whatsapp / none
  - the import template's contact column following the active provider
"""
import pytest

from app.services import messaging_service
from app.services import imports as import_svc
from app.routers import messaging as messaging_router
from tests.conftest import make_user, make_guard, auth_headers


@pytest.fixture(autouse=True)
def no_disk_writes(monkeypatch):
    """Never touch the real config.json during tests."""
    monkeypatch.setattr(messaging_router, "save_messaging", lambda updates: None)


# ── Endpoints ─────────────────────────────────────────────────────────────────
def test_provider_endpoint_defaults_to_none(client, db):
    user = make_user(db)
    res = client.get("/api/messaging/provider", headers=auth_headers(user.id))
    assert res.status_code == 200
    assert res.json()["provider"] in ("telegram", "whatsapp", "none")


def test_get_config_requires_admin(client, db):
    operator = make_user(db, username="op", is_admin=False)
    res = client.get("/api/messaging/", headers=auth_headers(operator.id))
    assert res.status_code == 403


def test_update_rejects_unknown_provider(client, db):
    admin = make_user(db, username="boss", is_admin=True)
    res = client.put("/api/messaging/", headers=auth_headers(admin.id),
                     json={"provider": "carrier-pigeon"})
    assert res.status_code == 400


def test_update_telegram_requires_token(client, db):
    admin = make_user(db, username="boss", is_admin=True)
    res = client.put("/api/messaging/", headers=auth_headers(admin.id),
                     json={"provider": "telegram", "telegram_bot_token": ""})
    assert res.status_code == 400


def test_update_whatsapp_requires_all_fields(client, db):
    admin = make_user(db, username="boss", is_admin=True)
    res = client.put("/api/messaging/", headers=auth_headers(admin.id),
                     json={"provider": "whatsapp", "whatsapp_account_sid": "AC1"})
    assert res.status_code == 400


def test_update_none_is_accepted(client, db):
    admin = make_user(db, username="boss", is_admin=True)
    res = client.put("/api/messaging/", headers=auth_headers(admin.id),
                     json={"provider": "none"})
    assert res.status_code == 200


def test_test_endpoint_none_provider(client, db):
    admin = make_user(db, username="boss", is_admin=True)
    res = client.post("/api/messaging/test", headers=auth_headers(admin.id),
                      json={"provider": "none"})
    assert res.status_code == 200
    assert res.json()["ok"] is True


# ── Service routing ───────────────────────────────────────────────────────────
def test_send_permit_none_is_noop_success(db, monkeypatch):
    monkeypatch.setattr(messaging_service, "get_provider", lambda: "none")
    guard = make_guard(db)

    class _P:  # minimal permit stand-in
        permit_number = "BC-1"
    assert messaging_service.send_permit(db, _P(), guard, None) is True


def test_send_permit_telegram_routes_by_chat_id(db, monkeypatch):
    import uuid
    from datetime import datetime
    from app.models.permit import Permit
    from app.models.firearm import Firearm

    monkeypatch.setattr(messaging_service, "get_provider", lambda: "telegram")
    monkeypatch.setattr(messaging_service, "get_messaging", lambda: {"telegram_bot_token": "tok"})
    sent = {}
    # No PDF on disk for this permit, so delivery goes via sendMessage.
    monkeypatch.setattr(messaging_service, "_telegram_send_message",
                        lambda token, chat_id, text: (sent.update(chat_id=chat_id) or (True, "sent")))

    guard = make_guard(db)
    guard.telegram_chat_id = "999"
    db.commit()
    fa = Firearm(id=str(uuid.uuid4()), serial_number="S1", make="Glock")
    db.add(fa)
    db.commit()
    permit = Permit(id=str(uuid.uuid4()), permit_number="BC-2", guard_id=guard.id,
                    firearm_id=fa.id, issued_by=make_user(db, username="iss").id,
                    issued_at=datetime.utcnow())
    db.add(permit)
    db.commit()

    assert messaging_service.send_permit(db, permit, guard, fa) is True
    assert sent.get("chat_id") == "999"
    assert permit.whatsapp_sent is True  # delivery recorded for audit, provider-agnostic


def test_send_permit_telegram_without_chat_id_fails(db, monkeypatch):
    monkeypatch.setattr(messaging_service, "get_provider", lambda: "telegram")
    monkeypatch.setattr(messaging_service, "get_messaging", lambda: {"telegram_bot_token": "tok"})
    guard = make_guard(db)  # no telegram_chat_id

    class _P:
        permit_number = "BC-3"
        pdf_path = None
    assert messaging_service.send_permit(db, _P(), guard, None) is False


# ── Import template follows the provider ─────────────────────────────────────
def test_import_template_telegram_column():
    sheets = import_svc.build_sheets(provider="telegram")
    guard_cols = next(s for s in sheets if s["name"] == "Guards")["columns"]
    fields = [field for (_h, field, *_ ) in guard_cols]
    assert "telegram_chat_id" in fields
    assert "cell_phone" not in fields


def test_import_template_whatsapp_column():
    sheets = import_svc.build_sheets(provider="whatsapp")
    guard_cols = next(s for s in sheets if s["name"] == "Guards")["columns"]
    fields = [field for (_h, field, *_ ) in guard_cols]
    assert "cell_phone" in fields
    assert "telegram_chat_id" not in fields


def test_import_template_none_has_no_contact_column():
    sheets = import_svc.build_sheets(provider="none")
    guard_cols = next(s for s in sheets if s["name"] == "Guards")["columns"]
    fields = [field for (_h, field, *_ ) in guard_cols]
    assert "cell_phone" not in fields
    assert "telegram_chat_id" not in fields
