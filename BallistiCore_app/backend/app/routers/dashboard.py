from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import require_active_user
from app.services import dashboard as svc

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"], dependencies=[Depends(require_active_user)])


@router.get("/")
def get_dashboard(db: Session = Depends(get_db)):
    """Key stats + the last 10 firearm issues/returns for the dashboard."""
    return svc.get_summary(db)
