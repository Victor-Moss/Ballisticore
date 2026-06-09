from sqlalchemy.orm import Session
from app.models.firearm import Firearm
from app.models.register import Register
from app.schemas.firearm import FirearmCreate, FirearmUpdate


def get_all(db: Session, include_inactive: bool = False) -> list[Firearm]:
    q = db.query(Firearm)
    if not include_inactive:
        q = q.filter(Firearm.is_active == True)
    return q.order_by(Firearm.make, Firearm.serial_number).all()


def get_by_id(db: Session, firearm_id: str) -> Firearm | None:
    return db.query(Firearm).filter(Firearm.id == firearm_id).first()


def get_by_serial(db: Session, serial_number: str) -> Firearm | None:
    return db.query(Firearm).filter(Firearm.serial_number == serial_number).first()


def is_available(db: Session, firearm_id: str) -> bool:
    return db.query(Register).filter(Register.firearm_id == firearm_id).first() is None


def create(db: Session, data: FirearmCreate) -> Firearm:
    firearm = Firearm(**data.model_dump())
    db.add(firearm)
    db.commit()
    db.refresh(firearm)
    return firearm


def update(db: Session, firearm: Firearm, data: FirearmUpdate) -> Firearm:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(firearm, field, value)
    db.commit()
    db.refresh(firearm)
    return firearm


def hard_delete(db: Session, firearm: Firearm) -> None:
    db.delete(firearm)
    db.commit()
