"""
Guard self-service — public endpoints a guard uses to recover their username
or reset their password via a WhatsApp OTP. These are intentionally NOT behind
operator authentication: a guard who forgot their password has no token.

To avoid leaking which guards exist, `forgot-username` and `request-reset`
always return the same generic success message regardless of whether a match
was found. Only `reset-password` reports success/failure, based on the OTP.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.guard import (
    ForgotUsernameRequest, RequestResetRequest, ResetPasswordRequest, GenericMessageOut,
)
from app.services import guard_auth
from app.services import whatsapp as wa

router = APIRouter(prefix="/api/guard-account", tags=["Guard Self-Service"])

_GENERIC_SENT = "If a matching guard was found, a WhatsApp message has been sent to the number on file."


@router.post("/forgot-username", response_model=GenericMessageOut)
def forgot_username(data: ForgotUsernameRequest, db: Session = Depends(get_db)):
    if not (data.id_number or data.cell_phone):
        raise HTTPException(status_code=400, detail="Provide your ID number or cell phone")
    guard = guard_auth.find_for_recovery(db, data.id_number, data.cell_phone)
    if guard and guard.username and guard.cell_phone:
        wa.send_guard_username(guard.cell_phone, guard.username, f"{guard.first_name} {guard.last_name}")
    return GenericMessageOut(message=_GENERIC_SENT)


@router.post("/request-reset", response_model=GenericMessageOut)
def request_reset(data: RequestResetRequest, db: Session = Depends(get_db)):
    guard = guard_auth.get_by_username(db, data.username)
    if guard and guard.cell_phone:
        otp = guard_auth.start_otp_reset(db, guard)
        wa.send_guard_otp(guard.cell_phone, otp, f"{guard.first_name} {guard.last_name}")
    return GenericMessageOut(message=_GENERIC_SENT)


@router.post("/reset-password", response_model=GenericMessageOut)
def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    if len(data.new_password) < 6:
        raise HTTPException(status_code=400, detail="New password must be at least 6 characters")
    guard = guard_auth.get_by_username(db, data.username)
    # Generic failure when the username is unknown — avoids confirming accounts.
    if not guard:
        raise HTTPException(status_code=400, detail="Incorrect code. Please try again.")
    ok, message = guard_auth.verify_otp_and_set_password(db, guard, data.otp, data.new_password)
    if not ok:
        raise HTTPException(status_code=400, detail=message)
    return GenericMessageOut(message="Password updated. You can now sign for your firearm.")
