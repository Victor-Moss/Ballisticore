from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import require_active_user, require_permission
from app.schemas.permission import PermissionCreate, PermissionOut
from app.services import permissions as svc
from app.services import guards as guard_svc
from app.services import firearms as firearm_svc

router = APIRouter(prefix="/api/permissions", tags=["Permissions"], dependencies=[Depends(require_active_user)])


@router.get("/guard/{guard_id}", response_model=list[PermissionOut])
def list_permissions_for_guard(guard_id: str, db: Session = Depends(get_db)):
    if not guard_svc.get_by_id(db, guard_id):
        raise HTTPException(status_code=404, detail="Guard not found")
    return svc.get_for_guard(db, guard_id)


@router.post("/", response_model=PermissionOut, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_permission("perm_manage_staff"))])
def set_permission(data: PermissionCreate, db: Session = Depends(get_db)):
    guard = guard_svc.get_by_id(db, data.guard_id)
    if not guard:
        raise HTTPException(status_code=404, detail="Guard not found")
    firearm = firearm_svc.get_by_id(db, data.firearm_id)
    if not firearm:
        raise HTTPException(status_code=404, detail="Firearm not found")
    # Only granting is gated on clearance — revoking must always be possible,
    # including for an assignment that predates this rule.
    if data.is_permitted:
        svc.validate_assignment(guard, firearm)
    return svc.upsert(db, data)


@router.delete("/{permission_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require_permission("perm_manage_staff"))])
def delete_permission(permission_id: str, db: Session = Depends(get_db)):
    perm = svc.get_by_id(db, permission_id)
    if not perm:
        raise HTTPException(status_code=404, detail="Permission not found")
    svc.delete(db, perm)
