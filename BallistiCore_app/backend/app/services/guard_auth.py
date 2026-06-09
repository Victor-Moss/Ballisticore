"""
Guard sign-in accounts — credentials a guard uses to electronically sign
for a firearm at the operator's terminal.

This is deliberately separate from operator `users`: a guard login can ONLY
be used to sign for a firearm. It carries no system access. The Guard row
itself holds the credentials (`username`, `hashed_password`) plus the
self-service password-reset state (`reset_otp_*`).

Password reset has two paths:
  - self-service: a 6-digit OTP is sent to the guard's WhatsApp number
  - operator fallback: an operator issues a temporary password the guard
    must change on next sign-in
"""

import secrets
import string
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.guard import Guard
from app.services.users import hash_password, verify_password

OTP_TTL_MINUTES = 10
OTP_MAX_ATTEMPTS = 5
OTP_LENGTH = 6
TEMP_PASSWORD_LENGTH = 10


# --- generators -------------------------------------------------------------

def generate_otp() -> str:
    """A numeric one-time PIN, e.g. '048213'."""
    return "".join(secrets.choice(string.digits) for _ in range(OTP_LENGTH))


def generate_temp_password() -> str:
    """A readable temporary password (no ambiguous chars) for operator resets."""
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz23456789"
    return "".join(secrets.choice(alphabet) for _ in range(TEMP_PASSWORD_LENGTH))


# --- lookups ----------------------------------------------------------------

def get_by_username(db: Session, username: str) -> Guard | None:
    if not username:
        return None
    return db.query(Guard).filter(Guard.username == username).first()


def username_available(db: Session, username: str, exclude_guard_id: str | None = None) -> bool:
    q = db.query(Guard).filter(Guard.username == username)
    if exclude_guard_id:
        q = q.filter(Guard.id != exclude_guard_id)
    return q.first() is None


def find_for_recovery(db: Session, id_number: str | None = None, cell_phone: str | None = None) -> Guard | None:
    """Locate a guard for username recovery by ID number or cell phone."""
    if id_number:
        g = db.query(Guard).filter(Guard.id_number == id_number).first()
        if g:
            return g
    if cell_phone:
        return db.query(Guard).filter(Guard.cell_phone == cell_phone).first()
    return None


# --- account management -----------------------------------------------------

def has_account(guard: Guard) -> bool:
    return bool(guard.username and guard.hashed_password)


def set_account(db: Session, guard: Guard, username: str, password: str | None = None) -> str | None:
    """
    Create or update a guard's sign-in account.

    If `password` is given, it is set directly. If omitted, a temporary
    password is generated and `must_change_password` is set — the plaintext
    temp password is returned so the operator can hand it over once. When a
    real password is supplied, returns None.
    """
    guard.username = username
    temp: str | None = None
    if password:
        guard.hashed_password = hash_password(password)
        guard.must_change_password = False
    else:
        temp = generate_temp_password()
        guard.hashed_password = hash_password(temp)
        guard.must_change_password = True
    guard.password_set_at = datetime.utcnow()
    _clear_otp(guard)
    db.commit()
    db.refresh(guard)
    return temp


def operator_reset_password(db: Session, guard: Guard) -> str:
    """Operator fallback: reset to a temporary password (must change on next sign-in)."""
    temp = generate_temp_password()
    guard.hashed_password = hash_password(temp)
    guard.must_change_password = True
    guard.password_set_at = datetime.utcnow()
    _clear_otp(guard)
    db.commit()
    db.refresh(guard)
    return temp


def change_password(db: Session, guard: Guard, new_password: str) -> None:
    guard.hashed_password = hash_password(new_password)
    guard.must_change_password = False
    guard.password_set_at = datetime.utcnow()
    _clear_otp(guard)
    db.commit()


def verify_guard_password(guard: Guard, password: str) -> bool:
    if not guard.hashed_password or not password:
        return False
    return verify_password(password, guard.hashed_password)


def disable_account(db: Session, guard: Guard) -> None:
    guard.username = None
    guard.hashed_password = None
    guard.must_change_password = False
    guard.password_set_at = None
    _clear_otp(guard)
    db.commit()


# --- OTP reset --------------------------------------------------------------

def start_otp_reset(db: Session, guard: Guard) -> str:
    """Mint a fresh OTP, store its hash + expiry, and return the plaintext
    so the caller can deliver it via WhatsApp."""
    otp = generate_otp()
    guard.reset_otp_hash = hash_password(otp)
    guard.reset_otp_expires_at = datetime.utcnow() + timedelta(minutes=OTP_TTL_MINUTES)
    guard.reset_otp_attempts = 0
    db.commit()
    return otp


def verify_otp_and_set_password(db: Session, guard: Guard, otp: str, new_password: str) -> tuple[bool, str]:
    """
    Validate the OTP and, on success, set the new password.
    Returns (ok, message). On failure `message` explains why (for the guard).
    """
    if not guard.reset_otp_hash or not guard.reset_otp_expires_at:
        return False, "No password reset was requested. Please request a new code."
    if datetime.utcnow() > guard.reset_otp_expires_at:
        _clear_otp(guard)
        db.commit()
        return False, "That code has expired. Please request a new one."
    if guard.reset_otp_attempts >= OTP_MAX_ATTEMPTS:
        _clear_otp(guard)
        db.commit()
        return False, "Too many incorrect attempts. Please request a new code."
    if not verify_password(otp, guard.reset_otp_hash):
        guard.reset_otp_attempts += 1
        db.commit()
        return False, "Incorrect code. Please try again."

    # success
    guard.hashed_password = hash_password(new_password)
    guard.must_change_password = False
    guard.password_set_at = datetime.utcnow()
    _clear_otp(guard)
    db.commit()
    return True, "Password updated."


def _clear_otp(guard: Guard) -> None:
    guard.reset_otp_hash = None
    guard.reset_otp_expires_at = None
    guard.reset_otp_attempts = 0
