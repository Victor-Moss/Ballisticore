from sqlalchemy.orm import Session
from app.models.guard import Guard, GuardCITRoute
from app.schemas.guard import GuardCreate, GuardUpdate, CITRouteCreate


def get_all(db: Session, include_inactive: bool = False) -> list[Guard]:
    q = db.query(Guard)
    if not include_inactive:
        q = q.filter(Guard.is_active == True)
    return q.order_by(Guard.last_name, Guard.first_name).all()


def get_by_id(db: Session, guard_id: str) -> Guard | None:
    return db.query(Guard).filter(Guard.id == guard_id).first()


def get_by_id_number(db: Session, id_number: str) -> Guard | None:
    if not id_number:
        return None
    return db.query(Guard).filter(Guard.id_number == id_number).first()


def create(db: Session, data: GuardCreate) -> Guard:
    # username/password are handled separately (set_account) — never write the
    # raw username/password straight onto the Guard row here.
    guard = Guard(**data.model_dump(exclude={"username", "password"}))
    db.add(guard)
    db.commit()
    db.refresh(guard)
    return guard


def update(db: Session, guard: Guard, data: GuardUpdate) -> Guard:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(guard, field, value)
    db.commit()
    db.refresh(guard)
    return guard


def deactivate(db: Session, guard: Guard) -> Guard:
    guard.is_active = False
    db.commit()
    db.refresh(guard)
    return guard


def reactivate(db: Session, guard: Guard) -> Guard:
    guard.is_active = True
    db.commit()
    db.refresh(guard)
    return guard


def hard_delete(db: Session, guard: Guard) -> None:
    db.delete(guard)
    db.commit()


# CIT Routes

def get_cit_routes(db: Session, guard_id: str) -> list[GuardCITRoute]:
    return db.query(GuardCITRoute).filter(GuardCITRoute.guard_id == guard_id).all()


def add_cit_route(db: Session, guard_id: str, data: CITRouteCreate) -> GuardCITRoute:
    route = GuardCITRoute(guard_id=guard_id, **data.model_dump())
    db.add(route)
    db.commit()
    db.refresh(route)
    return route


def delete_cit_route(db: Session, route_id: str) -> bool:
    route = db.query(GuardCITRoute).filter(GuardCITRoute.id == route_id).first()
    if not route:
        return False
    db.delete(route)
    db.commit()
    return True
