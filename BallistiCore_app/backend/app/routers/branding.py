from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.branding import branding, save_branding
from app.routers.auth import require_admin

router = APIRouter(prefix="/api/branding", tags=["Branding"])


class BrandingUpdate(BaseModel):
    company_name: Optional[str] = None
    company_reg: Optional[str] = None
    psira_number: Optional[str] = None
    company_address: Optional[str] = None
    permit_prefix: Optional[str] = None
    support_email: Optional[str] = None
    primary_color: Optional[str] = None
    cit_enabled: Optional[bool] = None
    setup_completed: Optional[bool] = None
    session_timeout_minutes: Optional[int] = None


@router.get("/")
def get_branding():
    """Public — returns safe display fields only (no auth required).

    Includes the first-time-setup and CIT flags so the frontend can decide
    whether to launch the setup wizard before an admin session is established.
    """
    return {
        "app_name": branding["app_name"],
        "company_name": branding["company_name"],
        "permit_prefix": branding["permit_prefix"],
        "primary_color": branding["primary_color"],
        "cit_enabled": branding.get("cit_enabled", False),
        "setup_completed": branding.get("setup_completed", False),
        "session_timeout_minutes": branding.get("session_timeout_minutes", 5),
    }


@router.get("/full")
def get_branding_full(current_user=Depends(require_admin)):
    """Admin only — returns all branding fields for the settings form."""
    return dict(branding)


@router.put("/")
def update_branding(data: BrandingUpdate, current_user=Depends(require_admin)):
    """Admin only — update company details and persist to branding.json."""
    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    # Enforce the inactivity-timeout bounds server-side: at least 1 minute, and
    # cap at 24h so a bad value can't effectively disable the auto-logout.
    if updates.get("session_timeout_minutes") is not None:
        updates["session_timeout_minutes"] = max(1, min(int(updates["session_timeout_minutes"]), 1440))
    if updates:
        save_branding(updates)
    return dict(branding)
