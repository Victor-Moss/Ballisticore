from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import require_active_user, require_admin, require_change_passwords, require_permission
from app.models.user import User
from app.schemas.guard import (
    GuardCreate, GuardUpdate, GuardOut, CITRouteCreate, CITRouteOut,
    GuardAccountSet, GuardAccountOut,
)
from app.schemas.permission import PermissionOut
from app.services import guards as svc
from app.services import permissions as perm_svc
from app.services import firearms as firearm_svc
from app.services import guard_auth

router = APIRouter(prefix="/api/guards", tags=["Guards"], dependencies=[Depends(require_active_user)])


def _validate_firearm_assignments(db: Session, data: GuardCreate) -> None:
    """Reject inline firearm assignments that could never be issued.

    Shares perm_svc.validate_assignment with the edit-flow assignment path, so
    both enforce the same rule. The GuardCreate payload stands in for the guard's
    clearance flags — the guard doesn't exist yet at this point."""
    for firearm_id in dict.fromkeys(data.firearm_ids):
        firearm = firearm_svc.get_by_id(db, firearm_id)
        if not firearm:
            raise HTTPException(status_code=404, detail="Firearm not found")
        perm_svc.validate_assignment(data, firearm)


@router.get("/", response_model=list[GuardOut])
def list_guards(include_inactive: bool = False, db: Session = Depends(get_db)):
    return svc.get_all(db, include_inactive)


@router.get("/{guard_id}", response_model=GuardOut)
def get_guard(guard_id: str, db: Session = Depends(get_db)):
    guard = svc.get_by_id(db, guard_id)
    if not guard:
        raise HTTPException(status_code=404, detail="Guard not found")
    return guard


@router.get("/{guard_id}/permissions", response_model=list[PermissionOut])
def get_guard_permissions(guard_id: str, db: Session = Depends(get_db)):
    guard = svc.get_by_id(db, guard_id)
    if not guard:
        raise HTTPException(status_code=404, detail="Guard not found")
    return perm_svc.get_for_guard(db, guard_id)


@router.post("/", response_model=GuardOut, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_permission("perm_manage_staff"))])
def create_guard(data: GuardCreate, db: Session = Depends(get_db)):
    if data.id_number and svc.get_by_id_number(db, data.id_number):
        raise HTTPException(status_code=409, detail="A guard with this ID number already exists")
    # Validate the username BEFORE creating the guard, so a clash never leaves
    # a half-created guard with no account.
    if data.username and not guard_auth.username_available(db, data.username):
        raise HTTPException(status_code=409, detail="That username is already taken")
    # Same for any firearms being assigned inline — check them up front so the
    # guard is never written when an assignment would fail.
    _validate_firearm_assignments(db, data)
    guard = svc.create(db, data)
    if data.username:
        guard_auth.set_account(db, guard, data.username, data.password)
    return guard


@router.put("/{guard_id}", response_model=GuardOut,
            dependencies=[Depends(require_permission("perm_manage_staff"))])
def update_guard(guard_id: str, data: GuardUpdate, db: Session = Depends(get_db)):
    guard = svc.get_by_id(db, guard_id)
    if not guard:
        raise HTTPException(status_code=404, detail="Guard not found")
    return svc.update(db, guard, data)


@router.put("/{guard_id}/deactivate", response_model=GuardOut,
            dependencies=[Depends(require_permission("perm_manage_staff"))])
def deactivate_guard(guard_id: str, db: Session = Depends(get_db)):
    guard = svc.get_by_id(db, guard_id)
    if not guard:
        raise HTTPException(status_code=404, detail="Guard not found")
    if not guard.is_active:
        raise HTTPException(status_code=400, detail="Guard is already inactive")
    return svc.deactivate(db, guard)


@router.put("/{guard_id}/reactivate", response_model=GuardOut,
            dependencies=[Depends(require_permission("perm_manage_staff"))])
def reactivate_guard(guard_id: str, db: Session = Depends(get_db)):
    guard = svc.get_by_id(db, guard_id)
    if not guard:
        raise HTTPException(status_code=404, detail="Guard not found")
    if guard.is_active:
        raise HTTPException(status_code=400, detail="Guard is already active")
    return svc.reactivate(db, guard)


@router.delete("/{guard_id}", status_code=204)
def delete_guard(
    guard_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("perm_manage_staff")),
):
    guard = svc.get_by_id(db, guard_id)
    if not guard:
        raise HTTPException(status_code=404, detail="Guard not found")
    from app.models.register import Register
    if db.query(Register).filter(Register.guard_id == guard_id).first():
        raise HTTPException(
            status_code=409,
            detail="Cannot delete guard — they currently have a firearm issued. Return it first.",
        )
    # A guard who has generated audit-relevant activity is never hard-deletable:
    # their issue history and permits are compliance records, so the guard row
    # they hang off has to stay. Deactivation is the supported route — it keeps
    # every record intact and takes the guard out of new issuance.
    if svc.has_audit_history(db, guard_id):
        raise HTTPException(
            status_code=400,
            detail=(
                "Cannot delete guard — they have issue history or permits on record, "
                "which must be retained. Deactivate the guard instead: they will no "
                "longer be available for new issuance and their history stays intact."
            ),
        )
    svc.hard_delete(db, guard)


# Sign-in account (operator-managed)

@router.post("/{guard_id}/account", response_model=GuardAccountOut)
def set_guard_account(
    guard_id: str,
    data: GuardAccountSet,
    db: Session = Depends(get_db),
    _: User = Depends(require_change_passwords),
):
    guard = svc.get_by_id(db, guard_id)
    if not guard:
        raise HTTPException(status_code=404, detail="Guard not found")
    if not guard_auth.username_available(db, data.username, exclude_guard_id=guard_id):
        raise HTTPException(status_code=409, detail="That username is already taken")
    temp = guard_auth.set_account(db, guard, data.username, data.password)
    return GuardAccountOut(
        guard_id=guard.id,
        username=guard.username,
        has_account=True,
        must_change_password=guard.must_change_password,
        temp_password=temp,
    )


@router.put("/{guard_id}/account/reset-password", response_model=GuardAccountOut)
def reset_guard_password(
    guard_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_change_passwords),
):
    guard = svc.get_by_id(db, guard_id)
    if not guard:
        raise HTTPException(status_code=404, detail="Guard not found")
    if not guard_auth.has_account(guard):
        raise HTTPException(status_code=400, detail="This guard has no sign-in account yet")
    temp = guard_auth.operator_reset_password(db, guard)
    return GuardAccountOut(
        guard_id=guard.id,
        username=guard.username,
        has_account=True,
        must_change_password=True,
        temp_password=temp,
    )


@router.delete("/{guard_id}/account", status_code=204)
def delete_guard_account(
    guard_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_change_passwords),
):
    guard = svc.get_by_id(db, guard_id)
    if not guard:
        raise HTTPException(status_code=404, detail="Guard not found")
    guard_auth.disable_account(db, guard)


# CIT Routes

@router.get("/{guard_id}/cit-routes", response_model=list[CITRouteOut])
def list_cit_routes(guard_id: str, db: Session = Depends(get_db)):
    guard = svc.get_by_id(db, guard_id)
    if not guard:
        raise HTTPException(status_code=404, detail="Guard not found")
    return svc.get_cit_routes(db, guard_id)


@router.post("/{guard_id}/cit-routes", response_model=CITRouteOut, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_permission("perm_manage_staff"))])
def add_cit_route(guard_id: str, data: CITRouteCreate, db: Session = Depends(get_db)):
    guard = svc.get_by_id(db, guard_id)
    if not guard:
        raise HTTPException(status_code=404, detail="Guard not found")
    return svc.add_cit_route(db, guard_id, data)


@router.delete("/{guard_id}/cit-routes/{route_id}", status_code=204,
               dependencies=[Depends(require_permission("perm_manage_staff"))])
def delete_cit_route(guard_id: str, route_id: str, db: Session = Depends(get_db)):
    if not svc.delete_cit_route(db, route_id):
        raise HTTPException(status_code=404, detail="CIT route not found")
