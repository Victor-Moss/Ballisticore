"""
Unified permit-delivery service.

This is the single entry point the rest of the codebase uses to deliver a permit.
It reads the configured provider from config.json (see core.messaging_config) and
routes to the right transport:

  - telegram : POST https://api.telegram.org/bot{token}/sendDocument with the
               permit PDF uploaded as a file. Recipient = guard.telegram_chat_id.
  - whatsapp : existing Twilio logic (services.whatsapp), unchanged.
               Recipient = guard.cell_phone.
  - none     : no-op — permits are generated but not auto-delivered. Returns
               success silently.

Callers (issuance, return, resend) call send_permit() and never need to know
which provider is active. Delivery attempts are logged and recorded on the permit
(permit.whatsapp_sent / whatsapp_sent_at — the generic "delivered" audit flag)
regardless of provider.
"""
from datetime import datetime
from pathlib import Path

import httpx
from sqlalchemy.orm import Session

from app.core.messaging_config import (
    get_provider,
    get_messaging,
    normalise_whatsapp_from,
)
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


# ── Public API ────────────────────────────────────────────────────────────────
def recipient_for(guard) -> str | None:
    """The delivery address for the active provider, read off the guard.

    Telegram → telegram_chat_id, WhatsApp → cell_phone, None → None.
    """
    provider = get_provider()
    if provider == "telegram":
        return getattr(guard, "telegram_chat_id", None)
    if provider == "whatsapp":
        return guard.cell_phone
    return None


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

    if provider == "telegram":
        chat_id = recipient_override or (getattr(guard, "telegram_chat_id", None) if guard else None)
        return _send_permit_telegram(db, permit, chat_id, guard_name, firearm_serial)

    if provider == "whatsapp":
        recipient = recipient_override or (guard.cell_phone if guard else None)
        if not recipient:
            print(f"WhatsApp: guard {guard_name} has no contact number — skipping send")
            return False
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
