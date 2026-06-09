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


def save_branding(updates: dict) -> None:
    """Update branding in-place and persist to branding.json."""
    branding.update(updates)
    _BRANDING_FILE.write_text(
        json.dumps(branding, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
