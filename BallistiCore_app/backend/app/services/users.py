import uuid
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from app.models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def get_by_username(db: Session, username: str) -> User | None:
    return db.query(User).filter(User.username == username).first()


def get_by_id(db: Session, user_id: str) -> User | None:
    return db.query(User).filter(User.id == user_id).first()


def get_all(db: Session) -> list[User]:
    return db.query(User).order_by(User.username).all()


def create(db: Session, username: str, email: str | None, password: str, is_admin: bool = False, **kwargs) -> User:
    user = User(
        username=username,
        email=email,
        hashed_password=hash_password(password),
        is_admin=is_admin,
        **kwargs,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update(db: Session, user: User, data: dict) -> User:
    password = data.pop("password", None)
    for key, value in data.items():
        if value is not None and hasattr(user, key):
            setattr(user, key, value)
    if password:
        user.hashed_password = hash_password(password)
    db.commit()
    db.refresh(user)
    return user


def seed_admin(db: Session) -> User:
    existing = get_by_username(db, "admin")
    if existing:
        return existing
    return create(db, username="admin", email="admin@ballisticore.local", password="admin1234", is_admin=True)
