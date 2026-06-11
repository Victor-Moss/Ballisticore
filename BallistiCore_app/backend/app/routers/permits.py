import os
from typing import Optional
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.core.auth import require_active_user, require_permission
from app.models.permit import Permit
from app.models.guard import Guard
from app.models.firearm import Firearm
from app.services import permit_generator as gen
from app.services import whatsapp as wa

router = APIRouter(prefix="/api/permits", tags=["Permits"], dependencies=[Depends(require_active_user)])
public_router = APIRouter(prefix="/api/permits/public", tags=["Permits (public)"])


def _get_permit_or_404(db: Session, permit_id: str) -> Permit:
    permit = db.query(Permit).filter(Permit.id == permit_id).first()
    if not permit:
        raise HTTPException(status_code=404, detail="Permit not found")
    return permit


@router.get("/")
def list_permits(db: Session = Depends(get_db)):
    permits = db.query(Permit).order_by(Permit.issued_at.desc()).all()
    result = []
    for p in permits:
        guard = db.query(Guard).filter(Guard.id == p.guard_id).first()
        firearm = db.query(Firearm).filter(Firearm.id == p.firearm_id).first()
        result.append({
            "id": p.id,
            "permit_number": p.permit_number,
            "guard_id": p.guard_id,
            "firearm_id": p.firearm_id,
            "issued_at": p.issued_at,
            "valid_date": p.valid_date,
            "whatsapp_sent": p.whatsapp_sent,
            "whatsapp_sent_at": p.whatsapp_sent_at,
            "guard_signed": p.guard_signed,
            "guard_signed_at": p.guard_signed_at,
            "has_pdf": p.pdf_path is not None and os.path.exists(p.pdf_path),
            "guard": {"first_name": guard.first_name, "last_name": guard.last_name} if guard else None,
            "firearm": {"make": firearm.make, "model": firearm.model, "serial_number": firearm.serial_number} if firearm else None,
        })
    return result


@router.get("/{permit_id}")
def get_permit(permit_id: str, db: Session = Depends(get_db)):
    permit = _get_permit_or_404(db, permit_id)
    guard = db.query(Guard).filter(Guard.id == permit.guard_id).first()
    firearm = db.query(Firearm).filter(Firearm.id == permit.firearm_id).first()
    return {
        "id": permit.id,
        "permit_number": permit.permit_number,
        "issued_at": permit.issued_at,
        "valid_date": permit.valid_date,
        "whatsapp_sent": permit.whatsapp_sent,
        "whatsapp_sent_at": permit.whatsapp_sent_at,
        "guard_signed": permit.guard_signed,
        "guard_signed_at": permit.guard_signed_at,
        "has_pdf": permit.pdf_path is not None and os.path.exists(permit.pdf_path),
        "guard": {"id": guard.id, "first_name": guard.first_name, "last_name": guard.last_name, "id_number": guard.id_number} if guard else None,
        "firearm": {"id": firearm.id, "serial_number": firearm.serial_number, "make": firearm.make, "calibre": firearm.calibre} if firearm else None,
    }


@router.post("/{permit_id}/generate")
def generate_permit_pdf(permit_id: str, db: Session = Depends(get_db)):
    permit = _get_permit_or_404(db, permit_id)
    guard = db.query(Guard).filter(Guard.id == permit.guard_id).first()
    firearm = db.query(Firearm).filter(Firearm.id == permit.firearm_id).first()
    if not guard or not firearm:
        raise HTTPException(status_code=400, detail="Guard or firearm record missing")
    paths = gen.generate_both(db, permit, guard, firearm)
    return {"message": "PDFs generated", "full": paths["full"], "mini": paths["mini"]}


@router.get("/{permit_id}/download")
def download_full_permit(permit_id: str, db: Session = Depends(get_db)):
    permit = _get_permit_or_404(db, permit_id)
    if not permit.pdf_path or not os.path.exists(permit.pdf_path):
        raise HTTPException(status_code=404, detail="PDF not yet generated — call /generate first")
    return FileResponse(
        path=permit.pdf_path,
        media_type="application/pdf",
        filename=f"{permit.permit_number}.pdf",
    )


@router.get("/{permit_id}/download-mini")
def download_mini_permit(permit_id: str, db: Session = Depends(get_db)):
    permit = _get_permit_or_404(db, permit_id)
    mini_path = permit.pdf_path.replace("_full.pdf", "_mini.pdf") if permit.pdf_path else None
    if not mini_path or not os.path.exists(mini_path):
        raise HTTPException(status_code=404, detail="Mini PDF not yet generated — call /generate first")
    return FileResponse(
        path=mini_path,
        media_type="application/pdf",
        filename=f"{permit.permit_number}_mini.pdf",
    )


class ResendRequest(BaseModel):
    recipient_number: Optional[str] = None  # override; defaults to guard's cell_phone


@router.post("/{permit_id}/resend-whatsapp", dependencies=[Depends(require_permission("perm_send_whatsapp"))])
def resend_whatsapp(
    permit_id: str,
    data: ResendRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    permit = _get_permit_or_404(db, permit_id)
    guard = db.query(Guard).filter(Guard.id == permit.guard_id).first()
    firearm = db.query(Firearm).filter(Firearm.id == permit.firearm_id).first()

    recipient = data.recipient_number or (guard.cell_phone if guard else None)
    if not recipient:
        raise HTTPException(status_code=400, detail="No recipient number — provide one or add cell_phone to the guard")

    background_tasks.add_task(
        wa.send_permit_whatsapp,
        db=db,
        permit=permit,
        recipient_number=recipient,
        guard_name=f"{guard.first_name} {guard.last_name}" if guard else "Unknown",
        firearm_serial=firearm.serial_number if firearm else "Unknown",
    )
    return {
        "message": f"WhatsApp queued for {recipient}",
        "permit_number": permit.permit_number,
    }


@public_router.get("/{permit_id}/download")
def public_download_permit(
    permit_id: str,
    token: str = Query(..., description="Signed token issued for this permit"),
    db: Session = Depends(get_db),
):
    """Unauthenticated PDF download for Twilio media fetch. Requires a signed
    short-lived token that matches the permit_id."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=403, detail="Invalid or expired token")

    if payload.get("scope") != wa.PERMIT_PDF_TOKEN_SCOPE or payload.get("sub") != permit_id:
        raise HTTPException(status_code=403, detail="Token does not match permit")

    permit = db.query(Permit).filter(Permit.id == permit_id).first()
    if not permit or not permit.pdf_path or not os.path.exists(permit.pdf_path):
        raise HTTPException(status_code=404, detail="Permit PDF not found")

    return FileResponse(
        path=permit.pdf_path,
        media_type="application/pdf",
        filename=f"{permit.permit_number}.pdf",
    )
