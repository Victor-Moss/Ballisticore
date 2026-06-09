from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import require_active_user, require_admin, require_change_passwords
from app.models.user import User
from app.schemas.guard import (
    GuardCreate, GuardUpdate, GuardOut, CITRouteCreate, CITRouteOut,
    GuardAccountSet, GuardAccountOut,
)
from app.schemas.permission import PermissionOut
from app.services import guards as svc
from app.services import permissions as perm_svc
from app.services import guard_auth

router = APIRouter(prefix="/api/guards", tags=["Guards"], dependencies=[Depends(require_active_user)])


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


@router.post("/", response_model=GuardOut, status_code=status.HTTP_201_CREATED)
def create_guard(data: GuardCreate, db: Session = Depends(get_db)):
    if data.id_number and svc.get_by_id_number(db, data.id_number):
        raise HTTPException(status_code=409, detail="A guard with this ID number already exists")
    # Validate the username BEFORE creating the guard, so a clash never leaves
    # a half-created guard with no account.
    if data.username and not guard_auth.username_available(db, data.username):
        raise HTTPException(status_code=409, detail="That username is already taken")
    guard = svc.create(db, data)
    if data.username:
        guard_auth.set_account(db, guard, data.username, data.password)
    return guard


@router.put("/{guard_id}", response_model=GuardOut)
def update_guard(guard_id: str, data: GuardUpdate, db: Session = Depends(get_db)):
    guard = svc.get_by_id(db, guard_id)
    if not guard:
        raise HTTPException(status_code=404, detail="Guard not found")
    return svc.update(db, guard, data)


@router.put("/{guard_id}/deactivate", response_model=GuardOut)
def deactivate_guard(guard_id: str, db: Session = Depends(get_db)):
    guard = svc.get_by_id(db, guard_id)
    if not guard:
        raise HTTPException(status_code=404, detail="Guard not found")
    if not guard.is_active:
        raise HTTPException(status_code=400, detail="Guard is already inactive")
    return svc.deactivate(db, guard)


@router.put("/{guard_id}/reactivate", response_model=GuardOut)
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
    _: User = Depends(require_admin),
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


@router.post("/{guard_id}/cit-routes", response_model=CITRouteOut, status_code=status.HTTP_201_CREATED)
def add_cit_route(guard_id: str, data: CITRouteCreate, db: Session = Depends(get_db)):
    guard = svc.get_by_id(db, guard_id)
    if not guard:
        raise HTTPException(status_code=404, detail="Guard not found")
    return svc.add_cit_route(db, guard_id, data)


@router.delete("/{guard_id}/cit-routes/{route_id}", status_code=204)
def delete_cit_route(guard_id: str, route_id: str, db: Session = Depends(get_db)):
    if not svc.delete_cit_route(db, route_id):
        raise HTTPException(status_code=404, detail="CIT route not found")
