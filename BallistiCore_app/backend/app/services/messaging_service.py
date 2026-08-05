"""
Unified permit-delivery service.

This is the single entry point the rest of the codebase uses to deliver a permit.
It reads the configured provider from config.json (see core.messaging_config) and
routes to the right transport:

  - telegram : POST https://api.telegram.org/bot{token}/sendDocument with the
               permit PDF uploaded as a file.
  - whatsapp : existing Twilio logic (services.whatsapp), unchanged.
  - none     : no-op — permits are generated but not auto-delivered. Returns
               success silently.

WHERE a permit goes depends on the company type as well as the provider — see
resolve_delivery_target(). A security company delivers to the individual guard;
a CIT company delivers to the cell number on the CIT route record, never to the
guard's own number.

Callers (issuance, return, resend) call send_permit() and never need to know
which provider is active. Delivery attempts are logged and recorded on the permit
(permit.whatsapp_sent / whatsapp_sent_at — the generic "delivered" audit flag)
regardless of provider.
"""
from datetime import datetime
from pathlib import Path

import httpx
from sqlalchemy.orm import Session

from app.core.branding import is_cit_company
from app.core.messaging_config import (
    get_provider,
    get_messaging,
    normalise_whatsapp_from,
)
from app.models.guard import GuardCITRoute
from app.models.permit import Permit
from app.services import whatsapp as wa

_TELEGRAM_API = "https://api.telegram.org/bot{token}/{method}"
_HTTP_TIMEOUT = 30.0


# ── Telegram ──────────────────────────────────────────────────────────────────
def _telegram_send_message(token: str, chat_id: str, text: str) -> tuple[bool, str]:
    """Send a plain text Telegram message. Returns (ok, detail)."""
    try:
        resp = httpx.post(
            _TELEGRAM_API.format(token=token, method="sendMessage"),
            data={"chat_id": chat_id, "text": text},
            timeout=_HTTP_TIMEOUT,
        )
        body = resp.json()
        if resp.status_code == 200 and body.get("ok"):
            return True, "sent"
        return False, body.get("description", f"HTTP {resp.status_code}")
    except Exception as e:  # noqa: BLE001
        return False, str(e)


def _telegram_send_document(
    token: str, chat_id: str, pdf_path: str, caption: str
) -> tuple[bool, str]:
    """Upload a PDF to a Telegram chat via sendDocument. Returns (ok, detail)."""
    try:
        path = Path(pdf_path)
        with path.open("rb") as fh:
            files = {"document": (path.name, fh, "application/pdf")}
            resp = httpx.post(
                _TELEGRAM_API.format(token=token, method="sendDocument"),
                data={"chat_id": chat_id, "caption": caption},
                files=files,
                timeout=_HTTP_TIMEOUT,
            )
        body = resp.json()
        if resp.status_code == 200 and body.get("ok"):
            return True, "sent"
        return False, body.get("description", f"HTTP {resp.status_code}")
    except Exception as e:  # noqa: BLE001
        return False, str(e)


def _send_permit_telegram(
    db: Session, permit: Permit, chat_id: str, guard_name: str, firearm_serial: str
) -> bool:
    token = get_messaging().get("telegram_bot_token", "")
    if not token:
        print("Telegram: bot token not configured — skipping send")
        return False
    if not chat_id:
        print(f"Telegram: guard {guard_name} has no Chat ID — skipping send")
        return False

    caption = (
        f"BallistiCore Firearms Permit\n"
        f"Permit #: {permit.permit_number}\n"
        f"Guard: {guard_name}\n"
        f"Firearm: {firearm_serial}\n"
        f"Issued: {permit.issued_at.strftime('%Y-%m-%d %H:%M')}"
    )

    if permit.pdf_path and Path(permit.pdf_path).exists():
        ok, detail = _telegram_send_document(token, chat_id, permit.pdf_path, caption)
    else:
        print(f"Telegram: PDF not available for permit {permit.permit_number} — sending text only")
        ok, detail = _telegram_send_message(token, chat_id, caption)

    if ok:
        permit.whatsapp_sent = True
        permit.whatsapp_sent_at = datetime.utcnow()
        db.commit()
        print(f"Telegram: sent permit {permit.permit_number} to chat {chat_id}")
    else:
        permit.whatsapp_sent = False
        db.commit()
        print(f"Telegram: failed to send permit {permit.permit_number} — {detail}")
    return ok


# ── Delivery target ───────────────────────────────────────────────────────────
class DeliveryTargetError(Exception):
    """No usable delivery address for this permit.

    The message is operator-facing and names the missing detail exactly (e.g.
    "No Telegram Chat ID configured for this guard"), so the UI can show it
    instead of a generic failure.
    """


def _cit_route_number(db: Session, permit: Permit, guard) -> str:
    """The cell number on the CIT route this permit was issued against.

    The permit records the route by name (permit.cit_cell_route, captured on the
    issue form), so match on that. When the guard has exactly one route and the
    permit doesn't name one, that route is unambiguous — use it.
    """
    routes = (
        db.query(GuardCITRoute).filter(GuardCITRoute.guard_id == guard.id).all()
        if guard is not None
        else []
    )

    route_name = (getattr(permit, "cit_cell_route", None) or "").strip()
    route = None
    if route_name:
        route = next(
            (r for r in routes if (r.route_name or "").strip().lower() == route_name.lower()),
            None,
        )
    if route is None and len(routes) == 1 and not route_name:
        route = routes[0]

    number = (route.cell_phone or "").strip() if route is not None else ""
    if not number:
        raise DeliveryTargetError("No cell number configured for this route")
    return number


def resolve_delivery_target(db: Session, permit: Permit, guard) -> str:
    """Where this permit must be delivered, given the company type and provider.

        Security company + Telegram → guard.telegram_chat_id
        Security company + WhatsApp → guard.cell_phone
        CIT company      + WhatsApp → the CIT route's cell number
        CIT company      + Telegram → not a valid combination

    Raises DeliveryTargetError, naming the missing detail, when the required
    contact field is blank.
    """
    provider = get_provider()

    if provider == "none":
        raise DeliveryTargetError(
            "No messaging provider is configured — set one under Settings → Messaging."
        )

    if is_cit_company():
        # CIT permits go to the route, never to the individual guard. Telegram has
        # no route-level address, so the combination is unsupported by design.
        if provider != "whatsapp":
            raise DeliveryTargetError(
                "CIT permits are delivered to the route's cell number over WhatsApp — "
                f"the {provider} provider cannot be used for a CIT company."
            )
        return _cit_route_number(db, permit, guard)

    # Security company — the permit belongs to the individual guard.
    if provider == "telegram":
        chat_id = (getattr(guard, "telegram_chat_id", None) or "").strip() if guard else ""
        if not chat_id:
            raise DeliveryTargetError("No Telegram Chat ID configured for this guard")
        return chat_id

    if provider == "whatsapp":
        number = (getattr(guard, "cell_phone", None) or "").strip() if guard else ""
        if not number:
            raise DeliveryTargetError("No cell number configured for this guard")
        return number

    raise DeliveryTargetError(f"Unknown messaging provider: {provider}")


# ── Public API ────────────────────────────────────────────────────────────────
def send_permit(
    db: Session,
    permit: Permit,
    guard,
    firearm,
    recipient_override: str | None = None,
) -> bool:
    """Deliver a permit using the configured provider.

    Returns True on success (or no-op for the 'none' provider), False on failure.
    Never raises — delivery problems are logged and recorded on the permit, never
    block the issuance/return response.
    """
    provider = get_provider()
    guard_name = f"{guard.first_name} {guard.last_name}" if guard else "Unknown"
    firearm_serial = firearm.serial_number if firearm else "Unknown"

    if provider == "none":
        print(f"Messaging: provider is 'none' — permit {permit.permit_number} not auto-delivered")
        return True

    # An override supplies the address, not the routing rules — an unsupported
    # company-type/provider combination is still refused.
    if is_cit_company() and provider != "whatsapp":
        print(
            f"Messaging: permit {permit.permit_number} not delivered — CIT permits require "
            f"the WhatsApp provider, not {provider!r}"
        )
        return False

    try:
        recipient = recipient_override or resolve_delivery_target(db, permit, guard)
    except DeliveryTargetError as e:
        print(f"Messaging: permit {permit.permit_number} not delivered — {e}")
        return False

    if provider == "telegram":
        return _send_permit_telegram(db, permit, recipient, guard_name, firearm_serial)

    if provider == "whatsapp":
        return wa.send_permit_whatsapp(
            db=db,
            permit=permit,
            recipient_number=recipient,
            guard_name=guard_name,
            firearm_serial=firearm_serial,
        )

    print(f"Messaging: unknown provider {provider!r} — skipping send")
    return False


# ── Credential testing (used by the Test button in the wizard & settings) ──────
def send_test_message(provider: str, credentials: dict, recipient: str) -> tuple[bool, str]:
    """Send a test message to `recipient` using the supplied (unsaved) credentials,
    so the user can confirm they work before saving. Returns (ok, message)."""
    text = "BallistiCore test message — your permit delivery is configured correctly. ✅"

    if provider == "none":
        return True, "No delivery provider selected — nothing to test."

    if not recipient:
        return False, "Enter a recipient to send the test to."

    if provider == "telegram":
        token = (credentials.get("telegram_bot_token") or "").strip()
        if not token:
            return False, "Enter the Telegram bot token first."
        ok, detail = _telegram_send_message(token, recipient.strip(), text)
        if ok:
            return True, f"Test message sent to Telegram chat {recipient}."
        return False, f"Telegram test failed: {detail}"

    if provider == "whatsapp":
        sid = (credentials.get("whatsapp_account_sid") or "").strip()
        token = (credentials.get("whatsapp_auth_token") or "").strip()
        from_number = normalise_whatsapp_from(credentials.get("whatsapp_from_number") or "")
        if not (sid and token and from_number):
            return False, "Enter the Account SID, Auth Token and From Number first."
        try:
            from twilio.rest import Client
            client = Client(sid, token)
            msg = client.messages.create(
                body=text,
                from_=from_number,
                to=wa._format_number(recipient),
            )
            return True, f"Test WhatsApp sent to {recipient} (SID {msg.sid})."
        except Exception as e:  # noqa: BLE001
            return False, f"WhatsApp test failed: {e}"

    return False, f"Unknown provider: {provider}"
