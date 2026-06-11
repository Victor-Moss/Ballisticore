from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import create_access_token, get_current_user, require_admin, require_permission, is_super_admin
from app.schemas.user import UserCreate, UserUpdate, UserOut, TokenOut
from app.services import users as user_svc
from app.models.user import User

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post("/login", response_model=TokenOut)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = user_svc.get_by_username(db, form.username)
    if not user or not user_svc.verify_password(form.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=403, detail="User account is disabled")

    token = create_access_token({"sub": user.id})
    return TokenOut(access_token=token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(
    data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("perm_add_user")),
):
    # Privilege-escalation guard: only a super admin (is_admin OR System Admin)
    # may mint another System Admin. A non-super operator with "Add Users" can
    # only create standard operator-level accounts — clamp the elevated flags.
    if not is_super_admin(current_user):
        data.is_admin = False
        data.perm_system_admin = False
    if user_svc.get_by_username(db, data.username):
        raise HTTPException(status_code=409, detail="Username already exists")
    if data.email and user_svc.get_by_email(db, data.email):
        raise HTTPException(status_code=409, detail="A user with that email already exists")
    extra = data.model_dump(exclude={"username", "password", "email", "is_admin"})
    try:
        return user_svc.create(db, data.username, data.email, data.password, data.is_admin, **extra)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="A user with that username or email already exists")


@router.get("/users", response_model=list[UserOut])
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("perm_add_user", "perm_modify_user", "perm_change_passwords")),
):
    return user_svc.get_all(db)


@router.put("/users/{user_id}", response_model=UserOut)
def update_user(
    user_id: str,
    data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("perm_modify_user", "perm_change_passwords")),
):
    user = user_svc.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if data.email:
        existing = user_svc.get_by_email(db, data.email)
        if existing and existing.id != user_id:
            raise HTTPException(status_code=409, detail="A user with that email already exists")
    update_data = data.model_dump(exclude_none=True)
    # Only a super admin may grant or revoke System Admin. A non-super operator
    # cannot elevate (or demote) the System Admin flags on any account — drop
    # them from the update so the existing values are preserved.
    if not is_super_admin(current_user):
        update_data.pop("is_admin", None)
        update_data.pop("perm_system_admin", None)
    try:
        return user_svc.update(db, user, update_data)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="A user with that email already exists")


@router.put("/users/{user_id}/deactivate", response_model=UserOut)
def deactivate_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("perm_modify_user")),
):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot deactivate your own account")
    user = user_svc.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = False
    db.commit()
    db.refresh(user)
    return user


@router.put("/users/{user_id}/reactivate", response_model=UserOut)
def reactivate_user(
    user_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("perm_modify_user")),
):
    user = user_svc.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = True
    db.commit()
    db.refresh(user)
    return user
