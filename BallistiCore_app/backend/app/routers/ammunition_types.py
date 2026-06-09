from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import require_active_user
from app.schemas.ammunition_type import (
    AmmunitionTypeCreate,
    AmmunitionTypeUpdate,
    AmmunitionTypeOut,
)
from app.services import ammunition_types as svc

router = APIRouter(
    prefix="/api/ammunition-types",
    tags=["Ammunition Types"],
    dependencies=[Depends(require_active_user)],
)


@router.get("/", response_model=list[AmmunitionTypeOut])
def list_ammunition_types(include_inactive: bool = False, db: Session = Depends(get_db)):
    return svc.get_all(db, include_inactive)


@router.get("/{ammunition_type_id}", response_model=AmmunitionTypeOut)
def get_ammunition_type(ammunition_type_id: str, db: Session = Depends(get_db)):
    ammo = svc.get_by_id(db, ammunition_type_id)
    if not ammo:
        raise HTTPException(status_code=404, detail="Ammunition type not found")
    return ammo


@router.post("/", response_model=AmmunitionTypeOut, status_code=status.HTTP_201_CREATED)
def create_ammunition_type(data: AmmunitionTypeCreate, db: Session = Depends(get_db)):
    return svc.create(db, data)


@router.put("/{ammunition_type_id}", response_model=AmmunitionTypeOut)
def update_ammunition_type(ammunition_type_id: str, data: AmmunitionTypeUpdate, db: Session = Depends(get_db)):
    ammo = svc.get_by_id(db, ammunition_type_id)
    if not ammo:
        raise HTTPException(status_code=404, detail="Ammunition type not found")
    return svc.update(db, ammo, data)


@router.delete("/{ammunition_type_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_ammunition_type(ammunition_type_id: str, db: Session = Depends(get_db)):
    ammo = svc.get_by_id(db, ammunition_type_id)
    if not ammo:
        raise HTTPException(status_code=404, detail="Ammunition type not found")
    svc.delete(db, ammo)
