"""
Shared pytest fixtures.

Uses an in-memory SQLite database — completely isolated from the real
PostgreSQL database, no seeding needed, no cleanup required.
"""
import pytest
import uuid
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.core.database import Base, get_db
from app.core.auth import create_access_token
from app.main import app

# ── In-memory SQLite engine ──────────────────────────────────────────────────
# StaticPool ensures every connection reuses the same underlying DB connection,
# so all code (fixtures, app endpoints) sees the same in-memory database.

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, _):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    """Fresh database tables for every test — guarantees isolation."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    """FastAPI TestClient wired to the in-memory DB session."""
    def _override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ── Seed helpers ─────────────────────────────────────────────────────────────

def make_user(db, username="testuser", password="testpass", is_admin=True):
    from app.models.user import User
    from app.services.users import hash_password
    user = User(
        id=str(uuid.uuid4()),
        username=username,
        email=None,
        hashed_password=hash_password(password),
        is_active=True,
        is_admin=is_admin,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def make_guard(db, first_name="John", last_name="Smith",
               id_number="8001015009087", psira_number="PS1234567",
               is_active=True):
    from app.models.guard import Guard
    guard = Guard(
        id=str(uuid.uuid4()),
        first_name=first_name,
        last_name=last_name,
        id_number=id_number,
        psira_number=psira_number,
        is_active=is_active,
    )
    db.add(guard)
    db.commit()
    db.refresh(guard)
    return guard


def make_firearm(db, serial_number="TEST-001", make="Glock", model="17",
                 calibre="9mm", firearm_type=None, is_active=True):
    from app.models.firearm import Firearm
    fa = Firearm(
        id=str(uuid.uuid4()),
        serial_number=serial_number,
        make=make,
        model=model,
        type=firearm_type,
        calibre=calibre,
        is_active=is_active,
    )
    db.add(fa)
    db.commit()
    db.refresh(fa)
    return fa


def make_permission(db, guard_id, firearm_id):
    from app.models.permission import GuardFirearmPermission
    perm = GuardFirearmPermission(
        id=str(uuid.uuid4()),
        guard_id=guard_id,
        firearm_id=firearm_id,
        is_permitted=True,
    )
    db.add(perm)
    db.commit()
    db.refresh(perm)
    return perm


def auth_headers(user_id: str) -> dict:
    """Returns Authorization header dict for the given user ID."""
    token = create_access_token({"sub": user_id})
    return {"Authorization": f"Bearer {token}"}
