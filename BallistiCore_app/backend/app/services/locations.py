from sqlalchemy.orm import Session
from app.models.location import Location
from app.schemas.location import LocationCreate, LocationUpdate


def get_all(db: Session, include_inactive: bool = False) -> list[Location]:
    q = db.query(Location)
    if not include_inactive:
        q = q.filter(Location.is_active == True)
    return q.order_by(Location.name).all()


def get_by_id(db: Session, location_id: str) -> Location | None:
    return db.query(Location).filter(Location.id == location_id).first()


def create(db: Session, data: LocationCreate) -> Location:
    location = Location(**data.model_dump())
    db.add(location)
    db.commit()
    db.refresh(location)
    return location


def update(db: Session, location: Location, data: LocationUpdate) -> Location:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(location, field, value)
    db.commit()
    db.refresh(location)
    return location


def delete(db: Session, location: Location) -> None:
    location.is_active = False
    db.commit()
