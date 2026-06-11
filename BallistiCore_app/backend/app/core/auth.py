from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None or not user.is_active:
        raise credentials_exception
    return user


def require_active_user(current_user: User = Depends(get_current_user)) -> User:
    return current_user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if not is_super_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


def is_super_admin(user: User) -> bool:
    """A super admin bypasses every granular permission check.

    Either the legacy `is_admin` flag or the explicit System Admin permission
    grants full access."""
    return bool(user.is_admin or user.perm_system_admin)


def require_permission(*perm_keys: str):
    """Build a dependency that allows the request only if the current user is a
    super admin OR holds at least one of the named `perm_*` permissions.

    Used to gate mutating endpoints so that a non-admin who has been granted a
    specific permission can actually perform that action, while everyone else
    gets a 403. Read endpoints are intentionally left open."""

    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if is_super_admin(current_user):
            return current_user
        if any(getattr(current_user, key, False) for key in perm_keys):
            return current_user
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to perform this action",
        )

    return dependency


def require_change_passwords(current_user: User = Depends(get_current_user)) -> User:
    """Operator must be an admin or hold the change-passwords permission to
    manage guard sign-in accounts."""
    if not (current_user.is_admin or current_user.perm_change_passwords):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to manage guard sign-in accounts",
        )
    return current_user
