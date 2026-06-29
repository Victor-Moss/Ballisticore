from typing import Optional
from datetime import datetime, date
from pydantic import BaseModel, field_validator, computed_field


def _empty_to_none(v):
    """Convert empty strings to None for nullable string fields."""
    if isinstance(v, str) and v.strip() == '':
        return None
    return v


class CITRouteCreate(BaseModel):
    route_name: str
    cell_phone: Optional[str] = None


class CITRouteOut(BaseModel):
    id: str
    guard_id: str
    route_name: str
    cell_phone: Optional[str] = None

    model_config = {"from_attributes": True}


class GuardBase(BaseModel):
    first_name: str
    last_name: str
    id_number: Optional[str] = None
    psira_number: Optional[str] = None
    cell_phone: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    email: Optional[str] = None
    physical_address: Optional[str] = None
    location_id: Optional[str] = None
    region: Optional[str] = None
    personnel_number: Optional[str] = None
    saps_comp_carbine: Optional[str] = None
    saps_expiry_carbine: Optional[date] = None
    saps_comp_handgun: Optional[str] = None
    saps_expiry_handgun: Optional[date] = None
    saps_comp_rifle: Optional[str] = None
    saps_expiry_rifle: Optional[date] = None
    saps_comp_shotgun: Optional[str] = None
    saps_expiry_shotgun: Optional[date] = None
    permitted_carbine: bool = False
    permitted_handgun: bool = False
    permitted_rifle: bool = False
    permitted_shotgun: bool = False

    @field_validator(
        'id_number', 'psira_number', 'cell_phone', 'telegram_chat_id', 'email',
        'physical_address', 'location_id', 'region', 'personnel_number',
        'saps_comp_carbine', 'saps_comp_handgun', 'saps_comp_rifle', 'saps_comp_shotgun',
        mode='before',
    )
    @classmethod
    def empty_str_to_none(cls, v):
        return _empty_to_none(v)


class GuardCreate(GuardBase):
    # Optional sign-in account created together with the guard. The frontend
    # Add Guard form makes these required; the API keeps them optional so the
    # edit-flow (account added later) and tests still work.
    username: Optional[str] = None
    password: Optional[str] = None

    @field_validator("username", "password", mode="before")
    @classmethod
    def empty_creds_to_none(cls, v):
        return _empty_to_none(v)


class GuardUpdate(BaseModel):
    id_number: Optional[str] = None
    psira_number: Optional[str] = None
    cell_phone: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    email: Optional[str] = None
    physical_address: Optional[str] = None
    location_id: Optional[str] = None
    region: Optional[str] = None
    personnel_number: Optional[str] = None
    saps_comp_carbine: Optional[str] = None
    saps_expiry_carbine: Optional[date] = None
    saps_comp_handgun: Optional[str] = None
    saps_expiry_handgun: Optional[date] = None
    saps_comp_rifle: Optional[str] = None
    saps_expiry_rifle: Optional[date] = None
    saps_comp_shotgun: Optional[str] = None
    saps_expiry_shotgun: Optional[date] = None
    permitted_carbine: Optional[bool] = None
    permitted_handgun: Optional[bool] = None
    permitted_rifle: Optional[bool] = None
    permitted_shotgun: Optional[bool] = None


class GuardOut(GuardBase):
    id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    cit_routes: list[CITRouteOut] = []
    # Sign-in account (credentials themselves are never exposed)
    username: Optional[str] = None
    must_change_password: bool = False
    last_signin_at: Optional[datetime] = None

    @computed_field
    @property
    def has_account(self) -> bool:
        return bool(self.username)

    model_config = {"from_attributes": True}


# --- Guard sign-in account (operator-managed) ------------------------------

class GuardAccountSet(BaseModel):
    """Create or update a guard's sign-in account. Omit `password` to have a
    temporary password generated (the guard must change it on next sign-in)."""
    username: str
    password: Optional[str] = None

    @field_validator("password", mode="before")
    @classmethod
    def empty_pw_to_none(cls, v):
        return _empty_to_none(v)


class GuardAccountOut(BaseModel):
    guard_id: str
    username: str
    has_account: bool
    must_change_password: bool
    # Present only when the server generated a password — show it to the
    # operator once so they can hand it to the guard.
    temp_password: Optional[str] = None


# --- Guard self-service (public) -------------------------------------------

class ForgotUsernameRequest(BaseModel):
    id_number: Optional[str] = None
    cell_phone: Optional[str] = None


class RequestResetRequest(BaseModel):
    username: str


class ResetPasswordRequest(BaseModel):
    username: str
    otp: str
    new_password: str


class GenericMessageOut(BaseModel):
    message: str


class GuardSummary(BaseModel):
    id: str
    first_name: str
    last_name: str
    id_number: Optional[str] = None
    psira_number: Optional[str] = None
    is_active: bool
    # Sign-in account presence — lets the Return form know whether this guard
    # must e-sign (enter their password) to hand the firearm back.
    username: Optional[str] = None

    @computed_field
    @property
    def has_account(self) -> bool:
        return bool(self.username)

    model_config = {"from_attributes": True}
