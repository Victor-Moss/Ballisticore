from sqlalchemy.orm import Session
from app.models.permission import GuardFirearmPermission
from app.schemas.permission import PermissionCreate


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
