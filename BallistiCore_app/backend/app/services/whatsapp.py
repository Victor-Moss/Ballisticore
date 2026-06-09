"""
WhatsApp permit delivery via Twilio.

Sends the permit PDF as a WhatsApp message to the guard's cell phone
(or a specified CRT vehicle number) on issuance.

Twilio sandbox: whatsapp:+14155238886
Production:     a purchased Twilio WhatsApp-enabled number

The send runs as a FastAPI BackgroundTask — failure is logged and
recorded on the permit but never blocks the issuance response.

PDF attachment requires PUBLIC_BASE_URL to be set in the environment
to a URL Twilio can reach (e.g. an ngrok tunnel in dev, or the prod
domain). When unset, the sender falls back to a text-only message.
"""

from datetime import datetime, timedelta
from pathlib import Path
from jose import jwt
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.permit import Permit

PERMIT_PDF_TOKEN_SCOPE = "permit_pdf"


def _format_number(number: str) -> str:
    """Normalise to E.164 format for Twilio. Handles SA numbers."""
    number = number.strip().replace(" ", "").replace("-", "")
    if number.startswith("0") and len(number) == 10:
        number = "+27" + number[1:]
    if not number.startswith("+"):
        number = "+" + number
    return f"whatsapp:{number}"


def _credentials_configured() -> bool:
    return bool(settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN)


def build_signed_pdf_url(permit_id: str) -> str | None:
    """Mint a short-lived signed URL Twilio can fetch the permit PDF from.
    Returns None when PUBLIC_BASE_URL is not configured."""
    base = settings.PUBLIC_BASE_URL.rstrip("/")
    if not base:
        return None
    expire = datetime.utcnow() + timedelta(minutes=settings.PERMIT_LINK_TTL_MINUTES)
    token = jwt.encode(
        {"sub": permit_id, "scope": PERMIT_PDF_TOKEN_SCOPE, "exp": expire},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    return f"{base}/api/permits/public/{permit_id}/download?token={token}"


def _send_text(recipient_number: str, body: str) -> bool:
    """Send a plain WhatsApp text message. Returns False (no-op) when Twilio
    credentials are not configured, so callers never crash in dev."""
    if not _credentials_configured():
        print("WhatsApp: Twilio credentials not configured — skipping send")
        return False
    try:
        from twilio.rest import Client
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            body=body,
            from_=settings.TWILIO_WHATSAPP_FROM,
            to=_format_number(recipient_number),
        )
        print(f"WhatsApp: sent text to {_format_number(recipient_number)} — SID: {message.sid}")
        return True
    except Exception as e:
        print(f"WhatsApp: failed to send text to {recipient_number} — {e}")
        return False


def send_guard_otp(recipient_number: str, otp: str, guard_name: str) -> bool:
    """Deliver a password-reset OTP to a guard's WhatsApp number."""
    body = (
        f"BallistiCore password reset\n"
        f"Hi {guard_name}, your one-time code is: {otp}\n\n"
        f"It expires in 10 minutes. If you did not request this, ignore this message."
    )
    return _send_text(recipient_number, body)


def send_guard_username(recipient_number: str, username: str, guard_name: str) -> bool:
    """Remind a guard of their sign-in username via WhatsApp."""
    body = (
        f"BallistiCore sign-in\n"
        f"Hi {guard_name}, your username is: {username}\n\n"
        f"Use it to sign for your firearm. If you've forgotten your password, "
        f"request a reset code."
    )
    return _send_text(recipient_number, body)


def send_permit_whatsapp(
    db: Session,
    permit: Permit,
    recipient_number: str,
    guard_name: str,
    firearm_serial: str,
) -> bool:
    """
    Send the permit to recipient_number via WhatsApp. Attaches the PDF as
    a media URL when PUBLIC_BASE_URL is configured and the PDF exists;
    otherwise sends text only. Updates permit.whatsapp_sent on success.
    """
    if not _credentials_configured():
        print("WhatsApp: Twilio credentials not configured — skipping send")
        return False

    pdf_url = None
    if permit.pdf_path and Path(permit.pdf_path).exists():
        pdf_url = build_signed_pdf_url(permit.id)
    else:
        print(f"WhatsApp: PDF not available for permit {permit.permit_number} — sending text only")

    try:
        from twilio.rest import Client
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

        to_number = _format_number(recipient_number)
        body = (
            f"BallistiCore Firearms Permit\n"
            f"Permit #: {permit.permit_number}\n"
            f"Guard: {guard_name}\n"
            f"Firearm: {firearm_serial}\n"
            f"Issued: {permit.issued_at.strftime('%Y-%m-%d %H:%M')}\n\n"
            f"Please retain this permit for the duration of the shift."
        )

        kwargs = {
            "body": body,
            "from_": settings.TWILIO_WHATSAPP_FROM,
            "to": to_number,
        }
        if pdf_url:
            kwargs["media_url"] = [pdf_url]

        message = client.messages.create(**kwargs)

        permit.whatsapp_sent = True
        permit.whatsapp_sent_at = datetime.utcnow()
        db.commit()
        attach_note = "with PDF" if pdf_url else "text only"
        print(f"WhatsApp: sent permit {permit.permit_number} ({attach_note}) to {to_number} — SID: {message.sid}")
        return True

    except Exception as e:
        print(f"WhatsApp: failed to send permit {permit.permit_number} — {e}")
        permit.whatsapp_sent = False
        db.commit()
        return False
