"""
License validation for BallistiCore.

A license key is a compact signed token  base64url(payload) "." base64url(sig)
signed with the vendor's Ed25519 private key (see tools/license_gen.py). The app
ships only the matching public key (license_public_key.pem), so keys cannot be
forged from the application source.

The key is read from `license.key` in the backend root (override with the
LICENSE_FILE env var). The signature + company binding are verified once and
cached; the expiry is evaluated live on every call, so the app flips to
read-only at the moment the subscription lapses without needing a restart.

States (read_only = EXPIRED | MISSING | INVALID):
  ACTIVE   valid signature, company matches, > WARN_DAYS left
  WARNING  valid, <= WARN_DAYS left (still fully usable)
  EXPIRED  valid, past expiry date
  MISSING  no license file present
  INVALID  bad signature, malformed, or company does not match
"""

import base64
import json
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from app.core.config import settings
from app.core.branding import branding

WARN_DAYS = 14

_BACKEND_ROOT = Path(__file__).parent.parent.parent
_PUBLIC_KEY_PEM = Path(__file__).parent / "license_public_key.pem"

ACTIVE, WARNING, EXPIRED, MISSING, INVALID = "active", "warning", "expired", "missing", "invalid"

_EXPIRED_MSG = "Subscription expired — contact BallistiCore"
_NO_LICENSE_MSG = "No valid license — contact BallistiCore"


@dataclass(frozen=True)
class LicenseStatus:
    state: str
    company: Optional[str]
    expires_at: Optional[str]   # ISO date string, for display
    days_left: Optional[int]
    read_only: bool
    message: str


def _license_file() -> Path:
    override = (settings.LICENSE_FILE or "").strip()
    return Path(override) if override else _BACKEND_ROOT / "license.key"


def _b64url_decode(part: str) -> bytes:
    padding = "=" * (-len(part) % 4)
    return base64.urlsafe_b64decode(part + padding)


def _load_public_key() -> Optional[Ed25519PublicKey]:
    if not _PUBLIC_KEY_PEM.is_file():
        return None
    try:
        key = serialization.load_pem_public_key(_PUBLIC_KEY_PEM.read_bytes())
        return key if isinstance(key, Ed25519PublicKey) else None
    except Exception:
        return None


# Cached verification result: (ok, company, expires_date, reason). Computed once
# (verification is signature + company binding, which don't change at runtime);
# the date-based state is derived live in get_status().
_verified: Optional[tuple] = None


def _verify() -> tuple:
    """Return (ok: bool, company: str|None, expires: date|None, reason: str)."""
    path = _license_file()
    if not path.is_file():
        return (False, None, None, MISSING)

    public_key = _load_public_key()
    if public_key is None:
        # No public key embedded — cannot trust anything.
        return (False, None, None, INVALID)

    token = path.read_text(encoding="utf-8").strip()
    try:
        payload_b64, sig_b64 = token.split(".", 1)
        payload_bytes = _b64url_decode(payload_b64)
        signature = _b64url_decode(sig_b64)
    except (ValueError, Exception):
        return (False, None, None, INVALID)

    try:
        public_key.verify(signature, payload_bytes)
    except InvalidSignature:
        return (False, None, None, INVALID)
    except Exception:
        return (False, None, None, INVALID)

    try:
        payload = json.loads(payload_bytes.decode("utf-8"))
        company = payload["company"]
        expires = datetime.strptime(payload["expires"], "%Y-%m-%d").date()
    except (KeyError, ValueError, Exception):
        return (False, None, None, INVALID)

    # Company binding — the key is tied to the configured company.
    if (company or "").strip().casefold() != (branding.get("company_name") or "").strip().casefold():
        return (False, company, expires, INVALID)

    return (True, company, expires, "")


def reload() -> LicenseStatus:
    """Re-read and re-verify the license file. Called at startup; also clears
    the cache so a freshly dropped-in key is picked up."""
    global _verified
    _verified = _verify()
    return get_status()


def get_status() -> LicenseStatus:
    global _verified
    if _verified is None:
        _verified = _verify()
    ok, company, expires, reason = _verified

    enforce = settings.LICENSE_ENFORCE

    if not ok:
        state = reason  # MISSING or INVALID
        msg = _NO_LICENSE_MSG
        return LicenseStatus(
            state=state, company=company,
            expires_at=expires.isoformat() if expires else None,
            days_left=None,
            read_only=enforce,  # fail-closed unless enforcement disabled
            message=msg if enforce else f"{msg} (enforcement disabled)",
        )

    days_left = (expires - date.today()).days
    if days_left < 0:
        state, read_only, msg = EXPIRED, enforce, _EXPIRED_MSG
    elif days_left <= WARN_DAYS:
        state, read_only, msg = WARNING, False, (
            f"Subscription expires in {days_left} day{'s' if days_left != 1 else ''} — contact BallistiCore to renew."
        )
    else:
        state, read_only, msg = ACTIVE, False, ""

    return LicenseStatus(
        state=state, company=company, expires_at=expires.isoformat(),
        days_left=days_left, read_only=read_only,
        message=msg if (read_only or state == WARNING) else "",
    )
