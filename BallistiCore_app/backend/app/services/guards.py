from sqlalchemy.orm import Session
from app.models.guard import Guard, GuardCITRoute
from app.schemas.guard import GuardCreate, GuardUpdate, CITRouteCreate
from app.services import permissions as perm_svc


def get_all(db: Session, include_inactive: bool = False) -> list[Guard]:
    q = db.query(Guard)
    if not include_inactive:
        q = q.filter(Guard.is_active == True)
    return q.order_by(Guard.last_name, Guard.first_name).all()


def get_by_id(db: Session, guard_id: str) -> Guard | None:
    return db.query(Guard).filter(Guard.id == guard_id).first()


def get_by_id_number(db: Session, id_number: str) -> Guard | None:
    if not id_number:
        return None
    return db.query(Guard).filter(Guard.id_number == id_number).first()


def create(db: Session, data: GuardCreate) -> Guard:
    # username/password are handled separately (set_account) — never write the
    # raw username/password straight onto the Guard row here.
    guard = Guard(**data.model_dump(exclude={"username", "password", "firearm_ids"}))
    db.add(guard)
    # Flush (not commit) so the guard's id is available for its firearm
    # assignments and both land in the same transaction — either the guard and
    # its assignments are created, or neither is.
    db.flush()
    perm_svc.stage_for_guard(db, guard.id, data.firearm_ids)
    db.commit()
    db.refresh(guard)
    return guard


def update(db: Session, guard: Guard, data: GuardUpdate) -> Guard:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(guard, field, value)
    db.commit()
    db.refresh(guard)
    return guard


def deactivate(db: Session, guard: Guard) -> Guard:
    # Firearm assignments are deliberately left intact, not overlooked: deactivation
    # means "not available for issuance right now", not "no longer authorised".
    # Permanent offboarding revokes assignments explicitly, as a separate step.
    guard.is_active = False
    db.commit()
    db.refresh(guard)
    return guard


def reactivate(db: Session, guard: Guard) -> Guard:
    guard.is_active = True
    db.commit()
    db.refresh(guard)
    return guard


def has_audit_history(db: Session, guard_id: str) -> bool:
    """Whether the guard has any compliance record that must outlive them.

    Register entries, register history and permits are the audit trail. None of
    these cascade on delete by design — a guard carrying any of them can only be
    deactivated, never hard-deleted. Firearm permissions are deliberately not
    counted: they are authorisation links rather than history, and do cascade.
    """
    from app.models.register import Register
    from app.models.register_history import RegisterHistory
    from app.models.permit import Permit

    for model in (Register, RegisterHistory, Permit):
        if db.query(model).filter(model.guard_id == guard_id).first():
            return True
    return False


def hard_delete(db: Session, guard: Guard) -> None:
    db.delete(guard)
    db.commit()


# CIT Routes

def get_cit_routes(db: Session, guard_id: str) -> list[GuardCITRoute]:
    return db.query(GuardCITRoute).filter(GuardCITRoute.guard_id == guard_id).all()


def add_cit_route(db: Session, guard_id: str, data: CITRouteCreate) -> GuardCITRoute:
    route = GuardCITRoute(guard_id=guard_id, **data.model_dump())
    db.add(route)
    db.commit()
    db.refresh(route)
    return route


def delete_cit_route(db: Session, route_id: str) -> bool:
    route = db.query(GuardCITRoute).filter(GuardCITRoute.id == route_id).first()
    if not route:
        return False
    db.delete(route)
    db.commit()
    return True
