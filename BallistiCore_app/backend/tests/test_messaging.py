"""
Messaging provider configuration + unified permit-delivery service.

Covers:
  - provider/config endpoints (validation, admin gating)
  - the credential Test endpoint
  - messaging_service routing for telegram / whatsapp / none
  - delivery-target resolution by company type + provider, and the named errors
    raised when the required contact detail is missing
  - the import template's contact column following the active provider
"""
import uuid
from datetime import datetime

import pytest

from app.routers import permits as permits_router
from app.services import messaging_service
from app.services import imports as import_svc
from app.routers import messaging as messaging_router
from tests.conftest import make_user, make_guard, make_firearm, auth_headers


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


# ── Delivery target: company type × provider ─────────────────────────────────
def _configure(monkeypatch, provider, cit):
    monkeypatch.setattr(messaging_service, "get_provider", lambda: provider)
    monkeypatch.setattr(messaging_service, "is_cit_company", lambda: cit)


def _make_permit(db, guard, cit_cell_route=None):
    from app.models.permit import Permit
    fa = make_firearm(db, serial_number=f"S-{uuid.uuid4().hex[:6]}")
    permit = Permit(
        id=str(uuid.uuid4()),
        permit_number=f"BC-{uuid.uuid4().hex[:6]}",
        guard_id=guard.id,
        firearm_id=fa.id,
        issued_by=make_user(db, username=f"iss-{uuid.uuid4().hex[:6]}").id,
        issued_at=datetime.utcnow(),
        cit_cell_route=cit_cell_route,
    )
    db.add(permit)
    db.commit()
    return permit


def _add_route(db, guard, route_name, cell_phone=None):
    from app.models.guard import GuardCITRoute
    route = GuardCITRoute(id=str(uuid.uuid4()), guard_id=guard.id,
                          route_name=route_name, cell_phone=cell_phone)
    db.add(route)
    db.commit()
    return route


def test_target_security_telegram_is_guard_chat_id(db, monkeypatch):
    _configure(monkeypatch, "telegram", cit=False)
    guard = make_guard(db)
    guard.telegram_chat_id = "555"
    guard.cell_phone = "0820000000"  # present, but Telegram must not use it
    db.commit()
    permit = _make_permit(db, guard)

    assert messaging_service.resolve_delivery_target(db, permit, guard) == "555"


def test_target_security_whatsapp_is_guard_cell_number(db, monkeypatch):
    _configure(monkeypatch, "whatsapp", cit=False)
    guard = make_guard(db)
    guard.cell_phone = "0821234567"
    db.commit()
    permit = _make_permit(db, guard)

    assert messaging_service.resolve_delivery_target(db, permit, guard) == "0821234567"


def test_target_security_telegram_without_chat_id_names_the_field(db, monkeypatch):
    _configure(monkeypatch, "telegram", cit=False)
    guard = make_guard(db)
    permit = _make_permit(db, guard)

    with pytest.raises(messaging_service.DeliveryTargetError) as exc:
        messaging_service.resolve_delivery_target(db, permit, guard)
    assert str(exc.value) == "No Telegram Chat ID configured for this guard"


def test_target_security_whatsapp_without_cell_number_names_the_field(db, monkeypatch):
    _configure(monkeypatch, "whatsapp", cit=False)
    guard = make_guard(db)
    permit = _make_permit(db, guard)

    with pytest.raises(messaging_service.DeliveryTargetError) as exc:
        messaging_service.resolve_delivery_target(db, permit, guard)
    assert str(exc.value) == "No cell number configured for this guard"


def test_target_cit_whatsapp_uses_route_not_guard(db, monkeypatch):
    _configure(monkeypatch, "whatsapp", cit=True)
    guard = make_guard(db)
    guard.cell_phone = "0829999999"  # the guard's own number must be ignored
    db.commit()
    _add_route(db, guard, "CBD Route 1", "0831111111")
    _add_route(db, guard, "Harbour Route", "0832222222")
    permit = _make_permit(db, guard, cit_cell_route="Harbour Route")

    assert messaging_service.resolve_delivery_target(db, permit, guard) == "0832222222"


def test_target_cit_falls_back_to_the_only_route(db, monkeypatch):
    _configure(monkeypatch, "whatsapp", cit=True)
    guard = make_guard(db)
    _add_route(db, guard, "CBD Route 1", "0831111111")
    permit = _make_permit(db, guard)  # permit names no route

    assert messaging_service.resolve_delivery_target(db, permit, guard) == "0831111111"


def test_target_cit_route_without_cell_number_names_the_field(db, monkeypatch):
    _configure(monkeypatch, "whatsapp", cit=True)
    guard = make_guard(db)
    _add_route(db, guard, "CBD Route 1", None)
    permit = _make_permit(db, guard, cit_cell_route="CBD Route 1")

    with pytest.raises(messaging_service.DeliveryTargetError) as exc:
        messaging_service.resolve_delivery_target(db, permit, guard)
    assert str(exc.value) == "No cell number configured for this route"


def test_target_cit_with_no_routes_at_all_errors(db, monkeypatch):
    _configure(monkeypatch, "whatsapp", cit=True)
    guard = make_guard(db)
    guard.cell_phone = "0829999999"
    db.commit()
    permit = _make_permit(db, guard)

    with pytest.raises(messaging_service.DeliveryTargetError) as exc:
        messaging_service.resolve_delivery_target(db, permit, guard)
    assert str(exc.value) == "No cell number configured for this route"


def test_target_cit_ambiguous_route_name_errors(db, monkeypatch):
    """A permit naming a route that no longer exists must not silently pick another."""
    _configure(monkeypatch, "whatsapp", cit=True)
    guard = make_guard(db)
    _add_route(db, guard, "CBD Route 1", "0831111111")
    _add_route(db, guard, "Harbour Route", "0832222222")
    permit = _make_permit(db, guard, cit_cell_route="Retired Route")

    with pytest.raises(messaging_service.DeliveryTargetError):
        messaging_service.resolve_delivery_target(db, permit, guard)


def test_target_cit_telegram_is_not_a_valid_combination(db, monkeypatch):
    _configure(monkeypatch, "telegram", cit=True)
    guard = make_guard(db)
    guard.telegram_chat_id = "555"
    db.commit()
    _add_route(db, guard, "CBD Route 1", "0831111111")
    permit = _make_permit(db, guard, cit_cell_route="CBD Route 1")

    with pytest.raises(messaging_service.DeliveryTargetError) as exc:
        messaging_service.resolve_delivery_target(db, permit, guard)
    assert "CIT" in str(exc.value)


def test_send_permit_cit_telegram_refuses_even_with_override(db, monkeypatch):
    _configure(monkeypatch, "telegram", cit=True)
    monkeypatch.setattr(messaging_service, "get_messaging", lambda: {"telegram_bot_token": "tok"})
    monkeypatch.setattr(messaging_service, "_telegram_send_message",
                        lambda *a, **k: pytest.fail("must not send"))
    guard = make_guard(db)
    permit = _make_permit(db, guard)

    assert messaging_service.send_permit(db, permit, guard, None, recipient_override="555") is False


def test_send_permit_cit_whatsapp_delivers_to_route(db, monkeypatch):
    _configure(monkeypatch, "whatsapp", cit=True)
    sent = {}
    monkeypatch.setattr(messaging_service.wa, "send_permit_whatsapp",
                        lambda **kw: (sent.update(to=kw["recipient_number"]) or True))
    guard = make_guard(db)
    guard.cell_phone = "0829999999"
    db.commit()
    _add_route(db, guard, "CBD Route 1", "0831111111")
    permit = _make_permit(db, guard, cit_cell_route="CBD Route 1")

    assert messaging_service.send_permit(db, permit, guard, None) is True
    assert sent["to"] == "0831111111"


# ── Resend surfaces the named error ──────────────────────────────────────────
def test_resend_without_chat_id_returns_named_error(client, db, monkeypatch):
    monkeypatch.setattr(permits_router, "get_provider", lambda: "telegram")
    _configure(monkeypatch, "telegram", cit=False)
    admin = make_user(db, username="boss", is_admin=True)
    guard = make_guard(db)  # no telegram_chat_id
    permit = _make_permit(db, guard)

    res = client.post(f"/api/permits/{permit.id}/resend-whatsapp",
                      headers=auth_headers(admin.id), json={})
    assert res.status_code == 400
    assert res.json()["detail"] == "No Telegram Chat ID configured for this guard"


def test_resend_without_route_number_returns_named_error(client, db, monkeypatch):
    monkeypatch.setattr(permits_router, "get_provider", lambda: "whatsapp")
    _configure(monkeypatch, "whatsapp", cit=True)
    admin = make_user(db, username="boss", is_admin=True)
    guard = make_guard(db)
    _add_route(db, guard, "CBD Route 1", None)
    permit = _make_permit(db, guard, cit_cell_route="CBD Route 1")

    res = client.post(f"/api/permits/{permit.id}/resend-whatsapp",
                      headers=auth_headers(admin.id), json={})
    assert res.status_code == 400
    assert res.json()["detail"] == "No cell number configured for this route"


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
