from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.routers.auth import require_admin
from app.services import imports as svc

router = APIRouter(prefix="/api/import", tags=["Import"])

_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


@router.get("/template")
def download_template(current_user=Depends(require_admin)):
    """Download the blank Guards / Firearms / Users import template."""
    data = svc.build_template()
    return Response(
        content=data,
        media_type=_XLSX,
        headers={"Content-Disposition": 'attachment; filename="BallistiCore_Import_Template.xlsx"'},
    )


@router.post("/")
async def import_template(file: UploadFile = File(...), db: Session = Depends(get_db),
                          current_user=Depends(require_admin)):
    """Upload a populated template; validate and bulk-insert row by row.

    Returns a per-sheet report. Invalid rows are reported with their row number
    and reason and do not block the valid rows in the same upload.
    """
    name = (file.filename or "").lower()
    if not name.endswith((".xlsx", ".xlsm")):
        raise HTTPException(status_code=400, detail="Please upload an .xlsx file (the BallistiCore template).")
    data = await file.read()
    try:
        return svc.import_workbook(db, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
