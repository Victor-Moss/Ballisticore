"""
Core issuance engine — all business logic for issuing and returning firearms.

ISSUE flow:
  1. Guard exists and is active
  2. Firearm exists and is active
  3. Guard has permission (is_permitted = True in guard_firearm_permissions)
  4. Firearm not already issued (not in register)
  5. All pass → insert register + register_history + create permit record

RETURN flow:
  1. Find register entry by firearm_id
  2. Remove from register
  3. Append to register_history with action='RETURNED'
"""

from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.register import Register
from app.models.register_history import RegisterHistory
from app.models.permit import Permit
from app.services import guards as guard_svc
from app.services import firearms as firearm_svc
from app.services import permissions as perm_svc
from app.services import permit_generator as pdf_gen
from app.services import whatsapp as wa
from app.services import guard_auth
from app.core.branding import branding


def _generate_permit_number(db: Session) -> str:
    today = datetime.utcnow().strftime("%Y%m%d")
    prefix = f"{branding['permit_prefix']}-{today}-"
    count = db.query(Permit).filter(Permit.permit_number.like(f"{prefix}%")).count()
    return f"{prefix}{str(count + 1).zfill(4)}"


def issue_firearm(
    db: Session,
    guard_id: str,
    firearm_id: str,
    issued_by: str,
    notes: str | None = None,
    background_tasks=None,
    rounds_issued: int | None = None,
    period_from_time=None,
    valid_until_time=None,
    cit_cell_route: str | None = None,
    witness: str | None = None,
    saps_competency_number: str | None = None,
    ammunition_issued: int | None = None,
    firearm_inspected_correct: bool | None = None,
    cit_id: str | None = None,
    responsible_person_name: str | None = None,
    guard_password: str | None = None,
) -> Register:
    # 1. Guard check
    guard = guard_svc.get_by_id(db, guard_id)
    if not guard:
        raise HTTPException(status_code=404, detail="Guard not found")
    if not guard.is_active:
        raise HTTPException(status_code=400, detail="Guard is not active")

    # 2. Firearm check
    firearm = firearm_svc.get_by_id(db, firearm_id)
    if not firearm:
        raise HTTPException(status_code=404, detail="Firearm not found")
    if not firearm.is_active:
        raise HTTPException(status_code=400, detail="Firearm is not active")

    # 3. Permission check
    if not perm_svc.is_guard_permitted(db, guard_id, firearm_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"{guard.first_name} {guard.last_name} is not authorised to carry firearm {firearm.serial_number}",
        )

    # 3b. Weapon-type clearance check (only enforced when firearm has a type set)
    if firearm.type:
        permitted_flag = f"permitted_{firearm.type}"
        if not getattr(guard, permitted_flag, False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"{guard.first_name} {guard.last_name} does not have clearance for {firearm.type} type firearms",
            )

    # 4. Availability check
    existing = db.query(Register).filter(Register.firearm_id == firearm_id).first()
    if existing:
        holder = guard_svc.get_by_id(db, existing.guard_id)
        holder_name = f"{holder.first_name} {holder.last_name}" if holder else "another guard"
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Firearm {firearm.serial_number} is currently issued to {holder_name}",
        )

    # 4b. Electronic signature.
    # A guard who has a sign-in account MUST sign (enter their password) to be
    # issued a firearm. A guard with no account yet is issued unsigned — this
    # keeps rollout possible while accounts are still being created.
    signed_at = None
    if guard_auth.has_account(guard):
        if not guard_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{guard.first_name} {guard.last_name} has a sign-in account and must sign for this firearm. Enter their password.",
            )
        if not guard_auth.verify_guard_password(guard, guard_password):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Signature failed — the password entered for {guard.first_name} {guard.last_name} is incorrect.",
            )
        signed_at = datetime.utcnow()
        guard.last_signin_at = signed_at

    # 5. Create permit record
    # Snapshot the firearm's linked ammunition type name at issue time. Stored as
    # text on each record so the permit stays accurate if the type is later renamed.
    ammunition_type_name = firearm.ammunition_type_name

    permit = Permit(
        permit_number=_generate_permit_number(db),
        guard_id=guard_id,
        firearm_id=firearm_id,
        issued_by=issued_by,
        issued_at=datetime.utcnow(),
        rounds_issued=rounds_issued,
        ammunition_type=ammunition_type_name,
        period_from_time=period_from_time,
        valid_until_time=valid_until_time,
        cit_cell_route=cit_cell_route,
        witness=witness,
        saps_competency_number=saps_competency_number,
        guard_signed=signed_at is not None,
        guard_signed_at=signed_at,
        guard_signature_method="electronic_password" if signed_at else None,
    )
    db.add(permit)
    db.flush()  # get permit.id before committing

    # 6. Insert into register
    entry = Register(
        guard_id=guard_id,
        firearm_id=firearm_id,
        issued_by=issued_by,
        issued_at=datetime.utcnow(),
        permit_id=permit.id,
        ammunition_issued=ammunition_issued,
        ammunition_type=ammunition_type_name,
        firearm_inspected_correct=firearm_inspected_correct,
        cit_id=cit_id,
        responsible_person_name=responsible_person_name,
        guard_signed=signed_at is not None,
        guard_signed_at=signed_at,
    )
    db.add(entry)

    # 7. Append to history
    history = RegisterHistory(
        guard_id=guard_id,
        firearm_id=firearm_id,
        action="ISSUED",
        actioned_by=issued_by,
        actioned_at=datetime.utcnow(),
        notes=notes,
        ammunition_issued=ammunition_issued,
        ammunition_type=ammunition_type_name,
        firearm_inspected_correct=firearm_inspected_correct,
        cit_id=cit_id,
        responsible_person_name=responsible_person_name,
        guard_signed=signed_at is not None,
        guard_signed_at=signed_at,
    )
    db.add(history)
    db.commit()
    db.refresh(entry)

    # Auto-generate PDFs after commit (non-blocking)
    try:
        pdf_gen.generate_both(db, permit, guard, firearm)
    except Exception as e:
        print(f"PDF generation warning: {e}")

    # Auto-send WhatsApp if guard has a cell number
    if guard.cell_phone and background_tasks is not None:
        background_tasks.add_task(
            wa.send_permit_whatsapp,
            db=db,
            permit=permit,
            recipient_number=guard.cell_phone,
            guard_name=f"{guard.first_name} {guard.last_name}",
            firearm_serial=firearm.serial_number,
        )
    elif guard.cell_phone:
        # Fallback: send synchronously if no background_tasks passed
        wa.send_permit_whatsapp(
            db=db,
            permit=permit,
            recipient_number=guard.cell_phone,
            guard_name=f"{guard.first_name} {guard.last_name}",
            firearm_serial=firearm.serial_number,
        )

    return entry


def return_firearm(
    db: Session,
    firearm_id: str,
    actioned_by: str,
    notes: str | None = None,
    rounds_returned: int | None = None,
    firearm_returned_correct: bool | None = None,
    in_order: bool | None = None,
    remarks: str | None = None,
    ammunition_returned: int | None = None,
    permit_returned: bool | None = None,
) -> RegisterHistory:
    # 1. Find current register entry
    entry = db.query(Register).filter(Register.firearm_id == firearm_id).first()
    if not entry:
        firearm = firearm_svc.get_by_id(db, firearm_id)
        serial = firearm.serial_number if firearm else firearm_id
        raise HTTPException(
            status_code=404,
            detail=f"Firearm {serial} is not currently issued to anyone",
        )

    guard_id = entry.guard_id

    # 2. Update the permit with return inspection data
    if entry.permit_id:
        permit = db.query(Permit).filter(Permit.id == entry.permit_id).first()
        if permit:
            if rounds_returned is not None:
                permit.rounds_returned = rounds_returned
            if firearm_returned_correct is not None:
                permit.firearm_returned_correct = firearm_returned_correct
            if in_order is not None:
                permit.in_order = in_order
            if remarks:
                permit.remarks = remarks

    # 3. Remove from register
    db.delete(entry)

    # 5. Append to history (carry forward issue-time fields from register entry)
    history = RegisterHistory(
        guard_id=guard_id,
        firearm_id=firearm_id,
        action="RETURNED",
        actioned_by=actioned_by,
        actioned_at=datetime.utcnow(),
        notes=notes,
        ammunition_issued=entry.ammunition_issued,
        ammunition_returned=ammunition_returned,
        ammunition_type=entry.ammunition_type,
        firearm_inspected_correct=entry.firearm_inspected_correct,
        firearm_returned_correct=firearm_returned_correct,
        permit_returned=permit_returned,
        cit_id=entry.cit_id,
        responsible_person_name=entry.responsible_person_name,
    )
    db.add(history)
    db.commit()
    db.refresh(history)
    return history


def get_current_register(db: Session) -> list[Register]:
    return db.query(Register).order_by(Register.issued_at.desc()).all()


def get_register_for_guard(db: Session, guard_id: str) -> list[Register]:
    return db.query(Register).filter(Register.guard_id == guard_id).all()


def get_history(
    db: Session,
    guard_id: str | None = None,
    firearm_id: str | None = None,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
) -> list[RegisterHistory]:
    q = db.query(RegisterHistory)
    if guard_id:
        q = q.filter(RegisterHistory.guard_id == guard_id)
    if firearm_id:
        q = q.filter(RegisterHistory.firearm_id == firearm_id)
    if from_date:
        q = q.filter(RegisterHistory.actioned_at >= from_date)
    if to_date:
        q = q.filter(RegisterHistory.actioned_at <= to_date)
    return q.order_by(RegisterHistory.actioned_at.desc()).all()
