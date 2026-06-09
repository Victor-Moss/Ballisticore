from sqlalchemy.orm import Session
from app.models.ammunition_type import AmmunitionType
from app.schemas.ammunition_type import AmmunitionTypeCreate, AmmunitionTypeUpdate


def get_all(db: Session, include_inactive: bool = False) -> list[AmmunitionType]:
    q = db.query(AmmunitionType)
    if not include_inactive:
        q = q.filter(AmmunitionType.is_active == True)
    return q.order_by(AmmunitionType.name).all()


def get_by_id(db: Session, ammunition_type_id: str) -> AmmunitionType | None:
    return db.query(AmmunitionType).filter(AmmunitionType.id == ammunition_type_id).first()


def create(db: Session, data: AmmunitionTypeCreate) -> AmmunitionType:
    ammo = AmmunitionType(**data.model_dump())
    db.add(ammo)
    db.commit()
    db.refresh(ammo)
    return ammo


def update(db: Session, ammo: AmmunitionType, data: AmmunitionTypeUpdate) -> AmmunitionType:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(ammo, field, value)
    db.commit()
    db.refresh(ammo)
    return ammo


def delete(db: Session, ammo: AmmunitionType) -> None:
    ammo.is_active = False
    db.commit()
