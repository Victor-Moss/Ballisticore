from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import require_active_user
from app.schemas.location import LocationCreate, LocationUpdate, LocationOut
from app.services import locations as svc

router = APIRouter(prefix="/api/locations", tags=["Locations"], dependencies=[Depends(require_active_user)])


@router.get("/", response_model=list[LocationOut])
def list_locations(include_inactive: bool = False, db: Session = Depends(get_db)):
    return svc.get_all(db, include_inactive)


@router.get("/{location_id}", response_model=LocationOut)
def get_location(location_id: str, db: Session = Depends(get_db)):
    location = svc.get_by_id(db, location_id)
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    return location


@router.post("/", response_model=LocationOut, status_code=status.HTTP_201_CREATED)
def create_location(data: LocationCreate, db: Session = Depends(get_db)):
    return svc.create(db, data)


@router.put("/{location_id}", response_model=LocationOut)
def update_location(location_id: str, data: LocationUpdate, db: Session = Depends(get_db)):
    location = svc.get_by_id(db, location_id)
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    return svc.update(db, location, data)


@router.delete("/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_location(location_id: str, db: Session = Depends(get_db)):
    location = svc.get_by_id(db, location_id)
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    svc.delete(db, location)
