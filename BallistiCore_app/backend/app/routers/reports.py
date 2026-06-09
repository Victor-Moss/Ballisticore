from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import require_active_user
from app.services import reports as svc

router = APIRouter(
    prefix="/api/reports",
    tags=["Reports"],
    dependencies=[Depends(require_active_user)],
)


@router.get("/register")
def export_register(db: Session = Depends(get_db)):
    """Download current register as Excel."""
    data = svc.generate_register_excel(db)
    from datetime import datetime
    filename = f"BallistiCore_Register_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/history")
def export_history(
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    guard_id: Optional[str] = None,
    firearm_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Download filtered history as Excel."""
    data = svc.generate_history_excel(db, from_date, to_date, guard_id, firearm_id)
    from datetime import datetime
    filename = f"BallistiCore_History_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/guard/{guard_id}")
def export_guard_activity(guard_id: str, db: Session = Depends(get_db)):
    """Download a single guard's full activity history as Excel."""
    try:
        data = svc.generate_guard_activity_excel(db, guard_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    from datetime import datetime
    filename = f"BallistiCore_Guard_{guard_id[:8]}_{datetime.now().strftime('%Y%m%d')}.xlsx"
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
