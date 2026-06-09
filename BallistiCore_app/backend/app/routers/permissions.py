from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import require_active_user
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


@router.post("/", response_model=PermissionOut, status_code=status.HTTP_201_CREATED)
def set_permission(data: PermissionCreate, db: Session = Depends(get_db)):
    if not guard_svc.get_by_id(db, data.guard_id):
        raise HTTPException(status_code=404, detail="Guard not found")
    if not firearm_svc.get_by_id(db, data.firearm_id):
        raise HTTPException(status_code=404, detail="Firearm not found")
    return svc.upsert(db, data)


@router.delete("/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_permission(permission_id: str, db: Session = Depends(get_db)):
    perm = svc.get_by_id(db, permission_id)
    if not perm:
        raise HTTPException(status_code=404, detail="Permission not found")
    svc.delete(db, perm)
