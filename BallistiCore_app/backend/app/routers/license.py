from fastapi import APIRouter

from app.core import license as lic

router = APIRouter(prefix="/api/license", tags=["License"])


@router.get("/")
def get_license():
    """Public — the current license state so the frontend can show the banner
    and switch to read-only mode. Carries no secrets."""
    s = lic.get_status()
    return {
        "state": s.state,
        "company": s.company,
        "expires_at": s.expires_at,
        "days_left": s.days_left,
        "read_only": s.read_only,
        "message": s.message,
    }
