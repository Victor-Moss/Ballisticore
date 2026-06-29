"""
Loads config.json from the backend root directory and exposes the `messaging`
block — the company's chosen permit-delivery provider and its credentials.

Chosen during first-time setup (Setup Wizard → Messaging step) and editable
later under Settings → Messaging. The `messaging` dict is a mutable singleton —
call save_messaging() to update it at runtime AND persist to disk. All modules
that imported `messaging` see changes immediately because they hold a reference
to the same dict object.

WhatsApp credentials fall back to the legacy environment variables (TWILIO_*)
when left blank here, so existing env-configured installs keep working until they
re-enter the details in the UI. See whatsapp_credentials().
"""
import json
from pathlib import Path

from app.core.config import settings

_CONFIG_FILE = Path(__file__).parent.parent.parent / "config.json"

# Supported permit-delivery providers.
PROVIDERS = ("telegram", "whatsapp", "none")

_DEFAULTS = {
    "messaging": {
        # One of PROVIDERS. "none" = permits are generated but not auto-delivered.
        "provider": "none",
        "telegram_bot_token": "",
        "whatsapp_account_sid": "",
        "whatsapp_auth_token": "",
        "whatsapp_from_number": "",
    }
}


def _load() -> dict:
    if _CONFIG_FILE.exists():
        try:
            data = json.loads(_CONFIG_FILE.read_text(encoding="utf-8"))
            merged = {**_DEFAULTS, **data}
            # Deep-merge the messaging block so new keys get their defaults.
            merged["messaging"] = {**_DEFAULTS["messaging"], **data.get("messaging", {})}
            return merged
        except Exception:
            pass
    return json.loads(json.dumps(_DEFAULTS))  # deep copy of defaults


config = _load()


def get_messaging() -> dict:
    """The current messaging block (provider + credentials)."""
    return config["messaging"]


def get_provider() -> str:
    """The active provider: 'telegram', 'whatsapp' or 'none'."""
    return config["messaging"].get("provider", "none")


def save_messaging(updates: dict) -> None:
    """Update the messaging block in-place and persist to config.json."""
    config["messaging"].update(updates)
    _CONFIG_FILE.write_text(
        json.dumps(config, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def whatsapp_credentials() -> tuple[str, str, str]:
    """Resolved Twilio WhatsApp credentials (sid, auth_token, from_number).

    Prefers the values entered in the UI (config.json) and falls back to the
    legacy TWILIO_* environment variables so existing installs keep working."""
    m = config["messaging"]
    sid = m.get("whatsapp_account_sid") or settings.TWILIO_ACCOUNT_SID
    token = m.get("whatsapp_auth_token") or settings.TWILIO_AUTH_TOKEN
    from_number = m.get("whatsapp_from_number") or settings.TWILIO_WHATSAPP_FROM
    return sid, token, normalise_whatsapp_from(from_number)


def normalise_whatsapp_from(number: str) -> str:
    """Ensure the Twilio 'from' number carries the required whatsapp: prefix."""
    number = (number or "").strip()
    if number and not number.startswith("whatsapp:"):
        number = f"whatsapp:{number}"
    return number
