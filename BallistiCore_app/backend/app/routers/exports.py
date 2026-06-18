from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import require_admin
from app.services import exports as svc

router = APIRouter(prefix="/api/export", tags=["Export"])


@router.get("/all")
def export_all_data(db: Session = Depends(get_db), current_user=Depends(require_admin)):
    """Export the complete system dataset (Excel + CSV bundle + PDF summary) as a
    single downloadable ZIP.

    Admin-only (require_admin == super admin) because the data includes ID
    numbers, SAPS competency numbers and PSIRA numbers. The service logs each
    export with the requesting user for audit purposes.
    """
    data, filename = svc.build_full_export(db, generated_by=current_user.username)
    return Response(
        content=data,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
