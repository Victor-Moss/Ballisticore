"""
Loads branding.json from the backend root directory.
All hardcoded company/app names flow through this module.

The `branding` dict is a mutable singleton — call save_branding()
to update it at runtime AND persist the change to disk.
All modules that imported `branding` see changes immediately
because they hold a reference to the same dict object.
"""
import json
from pathlib import Path

_BRANDING_FILE = Path(__file__).parent.parent.parent / "branding.json"

_DEFAULTS = {
    "app_name": "BallistiCore",
    "company_name": "Your Company",
    "company_reg": "",
    "psira_number": "",
    "company_address": "",
    "permit_prefix": "BC",
    "support_email": "",
    "primary_color": "#1d4ed8",
    # Whether Cash-in-Transit features are enabled (chosen in first-time setup).
    "cit_enabled": False,
    # Flips to True when the first-time setup wizard is completed; once True the
    # wizard never shows again.
    "setup_completed": False,
    # Auto-logout after this many minutes of no user activity (min 1). Surfaced
    # to the frontend idle timer via the public branding endpoint.
    "session_timeout_minutes": 5,
}


def _load() -> dict:
    if _BRANDING_FILE.exists():
        try:
            data = json.loads(_BRANDING_FILE.read_text(encoding="utf-8"))
            return {**_DEFAULTS, **data}
        except Exception:
            pass
    return _DEFAULTS.copy()


branding = _load()


def is_cit_company() -> bool:
    """True for a Cash-in-Transit install, False for a Security Company install.

    Company type is chosen once in first-time setup and stored as `cit_enabled`.
    It decides where a permit is delivered: a CIT company sends to the cell number
    on the CIT route record, a security company sends to the individual guard.
    """
    return bool(branding.get("cit_enabled", False))


def save_branding(updates: dict) -> None:
    """Update branding in-place and persist to branding.json."""
    branding.update(updates)
    _BRANDING_FILE.write_text(
        json.dumps(branding, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
