from typing import Optional
from datetime import datetime
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import require_active_user, require_permission
from app.models.user import User
from app.schemas.register import IssueRequest, ReturnRequest, RegisterEntryOut, HistoryEntryOut
from app.services import issuance as svc
from app.services import guards as guard_svc

router = APIRouter(prefix="/api/register", tags=["Register"], dependencies=[Depends(require_active_user)])


@router.get("/", response_model=list[RegisterEntryOut])
def current_register(db: Session = Depends(get_db)):
    return svc.get_current_register(db)


@router.get("/guard/{guard_id}", response_model=list[RegisterEntryOut])
def register_for_guard(guard_id: str, db: Session = Depends(get_db)):
    if not guard_svc.get_by_id(db, guard_id):
        raise HTTPException(status_code=404, detail="Guard not found")
    return svc.get_register_for_guard(db, guard_id)


@router.post("/issue", response_model=RegisterEntryOut)
def issue_firearm(
    data: IssueRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("perm_new_permits")),
):
    return svc.issue_firearm(
        db, data.guard_id, data.firearm_id, data.issued_by, data.notes, background_tasks,
        rounds_issued=data.rounds_issued,
        period_from_time=data.period_from_time,
        valid_until_time=data.valid_until_time,
        cit_cell_route=data.cit_cell_route,
        witness=data.witness,
        saps_competency_number=data.saps_competency_number,
        ammunition_issued=data.ammunition_issued,
        firearm_inspected_correct=data.firearm_inspected_correct,
        cit_id=data.cit_id,
        responsible_person_name=data.responsible_person_name,
        guard_password=data.guard_password,
        current_user=current_user,
        issuer_password=data.issuer_password,
    )


@router.post("/return", response_model=HistoryEntryOut)
def return_firearm(
    data: ReturnRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("perm_return_permits")),
):
    return svc.return_firearm(
        db, data.firearm_id, data.actioned_by, data.notes,
        rounds_returned=data.rounds_returned,
        firearm_returned_correct=data.firearm_returned_correct,
        in_order=data.in_order,
        remarks=data.remarks,
        ammunition_returned=data.ammunition_returned,
        permit_returned=data.permit_returned,
        current_user=current_user,
        staff_password=data.staff_password,
        guard_password=data.guard_password,
    )


@router.get("/history", response_model=list[HistoryEntryOut])
def history(
    guard_id: Optional[str] = None,
    firearm_id: Optional[str] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
):
    return svc.get_history(db, guard_id, firearm_id, from_date, to_date)


@router.get("/history/guard/{guard_id}", response_model=list[HistoryEntryOut])
def history_for_guard(guard_id: str, db: Session = Depends(get_db)):
    if not guard_svc.get_by_id(db, guard_id):
        raise HTTPException(status_code=404, detail="Guard not found")
    return svc.get_history(db, guard_id=guard_id)


@router.get("/history/firearm/{firearm_id}", response_model=list[HistoryEntryOut])
def history_for_firearm(firearm_id: str, db: Session = Depends(get_db)):
    return svc.get_history(db, firearm_id=firearm_id)
