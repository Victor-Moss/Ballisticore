from typing import Optional
from datetime import datetime
from pydantic import BaseModel, field_validator


def _empty_to_none(v):
    """Treat blank/whitespace strings as not-provided (None).

    Important for `email`, which is UNIQUE in the DB: storing '' for several
    users without an email would collide on the unique index, whereas multiple
    NULLs are allowed.
    """
    if isinstance(v, str) and v.strip() == "":
        return None
    return v


_OPTIONAL_STR_FIELDS = (
    "email", "personnel_number", "psira_number", "competency", "phone_number", "id_number",
)


class UserCreate(BaseModel):
    username: str
    password: str
    email: Optional[str] = None
    is_admin: bool = False
    personnel_number: Optional[str] = None
    psira_number: Optional[str] = None
    competency: Optional[str] = None
    phone_number: Optional[str] = None
    id_number: Optional[str] = None
    perm_new_permits: bool = False
    perm_return_permits: bool = False
    perm_manage_weapons: bool = False
    perm_manage_staff: bool = False
    perm_access_database: bool = False
    perm_send_whatsapp: bool = False
    perm_view_register_history: bool = False
    perm_system_admin: bool = False
    perm_add_user: bool = False
    perm_modify_user: bool = False
    perm_change_passwords: bool = False
    perm_clear_logs: bool = False
    perm_carbine: bool = False
    perm_handgun: bool = False
    perm_rifle: bool = False
    perm_shotgun: bool = False

    @field_validator(*_OPTIONAL_STR_FIELDS, mode="before")
    @classmethod
    def _blank_to_none(cls, v):
        return _empty_to_none(v)


class UserUpdate(BaseModel):
    email: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None
    personnel_number: Optional[str] = None
    psira_number: Optional[str] = None
    competency: Optional[str] = None
    phone_number: Optional[str] = None
    id_number: Optional[str] = None
    perm_new_permits: Optional[bool] = None
    perm_return_permits: Optional[bool] = None
    perm_manage_weapons: Optional[bool] = None
    perm_manage_staff: Optional[bool] = None
    perm_access_database: Optional[bool] = None
    perm_send_whatsapp: Optional[bool] = None
    perm_view_register_history: Optional[bool] = None
    perm_system_admin: Optional[bool] = None
    perm_add_user: Optional[bool] = None
    perm_modify_user: Optional[bool] = None
    perm_change_passwords: Optional[bool] = None
    perm_clear_logs: Optional[bool] = None
    perm_carbine: Optional[bool] = None
    perm_handgun: Optional[bool] = None
    perm_rifle: Optional[bool] = None
    perm_shotgun: Optional[bool] = None

    @field_validator(*_OPTIONAL_STR_FIELDS, mode="before")
    @classmethod
    def _blank_to_none(cls, v):
        return _empty_to_none(v)


class UserOut(BaseModel):
    id: str
    username: str
    email: Optional[str] = None
    is_active: bool
    is_admin: bool
    created_at: datetime
    personnel_number: Optional[str] = None
    psira_number: Optional[str] = None
    competency: Optional[str] = None
    phone_number: Optional[str] = None
    id_number: Optional[str] = None
    perm_new_permits: bool = False
    perm_return_permits: bool = False
    perm_manage_weapons: bool = False
    perm_manage_staff: bool = False
    perm_access_database: bool = False
    perm_send_whatsapp: bool = False
    perm_view_register_history: bool = False
    perm_system_admin: bool = False
    perm_add_user: bool = False
    perm_modify_user: bool = False
    perm_change_passwords: bool = False
    perm_clear_logs: bool = False
    perm_carbine: bool = False
    perm_handgun: bool = False
    perm_rifle: bool = False
    perm_shotgun: bool = False

    model_config = {"from_attributes": True}


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
