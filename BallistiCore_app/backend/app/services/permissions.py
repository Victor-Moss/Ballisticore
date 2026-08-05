from typing import Iterable

from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.permission import GuardFirearmPermission
from app.schemas.permission import PermissionCreate


def validate_assignment(clearance_holder, firearm) -> None:
    """Reject a guard→firearm assignment that could never be issued.

    Mirrors the checks the issuance engine applies at issue time, so an
    assignment is never stored that would be refused at the counter. Applied by
    both assignment paths — inline at guard creation and from the edit screen.

    `clearance_holder` is anything carrying the permitted_* flags: a Guard row
    (edit flow) or the GuardCreate payload (creation, before the guard exists).
    Weapon type is only enforced when the firearm has one recorded — same
    exception the issuance engine makes for untyped firearms.

    Validation applies to new assignment attempts only; permissions already in
    the database are never re-checked or invalidated.
    """
    if not firearm.is_active:
        raise HTTPException(
            status_code=400,
            detail=f"Firearm {firearm.serial_number} is not active and cannot be assigned",
        )
    if firearm.type and not getattr(clearance_holder, f"permitted_{firearm.type}", False):
        raise HTTPException(
            status_code=400,
            detail=(
                f"Firearm {firearm.serial_number} is a {firearm.type} — the guard needs "
                f"{firearm.type} clearance before it can be assigned"
            ),
        )


def get_for_guard(db: Session, guard_id: str) -> list[GuardFirearmPermission]:
    return (
        db.query(GuardFirearmPermission)
        .filter(GuardFirearmPermission.guard_id == guard_id)
        .all()
    )


def get_by_id(db: Session, permission_id: str) -> GuardFirearmPermission | None:
    return db.query(GuardFirearmPermission).filter(GuardFirearmPermission.id == permission_id).first()


def get_by_guard_and_firearm(db: Session, guard_id: str, firearm_id: str) -> GuardFirearmPermission | None:
    return (
        db.query(GuardFirearmPermission)
        .filter(
            GuardFirearmPermission.guard_id == guard_id,
            GuardFirearmPermission.firearm_id == firearm_id,
        )
        .first()
    )


def is_guard_permitted(db: Session, guard_id: str, firearm_id: str) -> bool:
    perm = get_by_guard_and_firearm(db, guard_id, firearm_id)
    if perm is None:
        return False
    return perm.is_permitted


def stage_for_guard(
    db: Session, guard_id: str, firearm_ids: Iterable[str]
) -> list[GuardFirearmPermission]:
    """Add guard→firearm permissions to the session WITHOUT committing.

    Lets guard creation write the guard and its firearm assignments in a single
    transaction, so a guard can never end up created with weapon types selected
    but no assignment. Callers own the commit. Repeated ids are collapsed so the
    unique (guard_id, firearm_id) constraint can't be tripped by one request.
    """
    perms = []
    for firearm_id in dict.fromkeys(firearm_ids):  # de-duplicate, preserve order
        perm = GuardFirearmPermission(
            guard_id=guard_id, firearm_id=firearm_id, is_permitted=True
        )
        db.add(perm)
        perms.append(perm)
    return perms


def upsert(db: Session, data: PermissionCreate) -> GuardFirearmPermission:
    existing = get_by_guard_and_firearm(db, data.guard_id, data.firearm_id)
    if existing:
        existing.is_permitted = data.is_permitted
        db.commit()
        db.refresh(existing)
        return existing
    perm = GuardFirearmPermission(**data.model_dump())
    db.add(perm)
    db.commit()
    db.refresh(perm)
    return perm


def delete(db: Session, permission: GuardFirearmPermission) -> None:
    db.delete(permission)
    db.commit()
