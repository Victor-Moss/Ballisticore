from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import require_active_user, require_admin, require_permission
from app.models.user import User
from app.schemas.firearm import FirearmCreate, FirearmUpdate, FirearmOut
from app.services import firearms as svc

router = APIRouter(prefix="/api/firearms", tags=["Firearms"], dependencies=[Depends(require_active_user)])


@router.get("/", response_model=list[FirearmOut])
def list_firearms(include_inactive: bool = False, db: Session = Depends(get_db)):
    firearms = svc.get_all(db, include_inactive)
    result = []
    for f in firearms:
        out = FirearmOut.model_validate(f)
        out.is_available = svc.is_available(db, f.id)
        result.append(out)
    return result


@router.get("/{firearm_id}", response_model=FirearmOut)
def get_firearm(firearm_id: str, db: Session = Depends(get_db)):
    firearm = svc.get_by_id(db, firearm_id)
    if not firearm:
        raise HTTPException(status_code=404, detail="Firearm not found")
    out = FirearmOut.model_validate(firearm)
    out.is_available = svc.is_available(db, firearm_id)
    return out


@router.post("/", response_model=FirearmOut, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_permission("perm_manage_weapons"))])
def create_firearm(data: FirearmCreate, db: Session = Depends(get_db)):
    if svc.get_by_serial(db, data.serial_number):
        raise HTTPException(status_code=409, detail="A firearm with this serial number already exists")
    return svc.create(db, data)


@router.put("/{firearm_id}", response_model=FirearmOut,
            dependencies=[Depends(require_permission("perm_manage_weapons"))])
def update_firearm(firearm_id: str, data: FirearmUpdate, db: Session = Depends(get_db)):
    firearm = svc.get_by_id(db, firearm_id)
    if not firearm:
        raise HTTPException(status_code=404, detail="Firearm not found")
    return svc.update(db, firearm, data)


@router.delete("/{firearm_id}", status_code=204)
def delete_firearm(
    firearm_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("perm_manage_weapons")),
):
    firearm = svc.get_by_id(db, firearm_id)
    if not firearm:
        raise HTTPException(status_code=404, detail="Firearm not found")
    from app.models.register import Register
    if db.query(Register).filter(Register.firearm_id == firearm_id).first():
        raise HTTPException(
            status_code=409,
            detail="Cannot delete firearm — it is currently issued. Return it first.",
        )
    svc.hard_delete(db, firearm)
