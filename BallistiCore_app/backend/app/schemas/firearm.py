from typing import Optional
from datetime import datetime, date
from pydantic import BaseModel

FIREARM_TYPES = ("carbine", "handgun", "rifle", "shotgun")


class FirearmBase(BaseModel):
    serial_number: str
    make: str
    model: Optional[str] = None
    type: Optional[str] = None
    calibre: Optional[str] = None
    license_number: Optional[str] = None
    license_issue_date: Optional[date] = None
    description: Optional[str] = None
    ammunition_type_id: Optional[str] = None


class FirearmCreate(FirearmBase):
    pass


class FirearmUpdate(BaseModel):
    make: Optional[str] = None
    model: Optional[str] = None
    type: Optional[str] = None
    calibre: Optional[str] = None
    license_number: Optional[str] = None
    license_issue_date: Optional[date] = None
    description: Optional[str] = None
    ammunition_type_id: Optional[str] = None
    is_active: Optional[bool] = None


class FirearmOut(FirearmBase):
    id: str
    is_active: bool
    created_at: datetime
    is_available: Optional[bool] = None
    ammunition_type_name: Optional[str] = None

    model_config = {"from_attributes": True}


class FirearmSummary(BaseModel):
    id: str
    serial_number: str
    make: str
    type: Optional[str] = None
    calibre: Optional[str] = None
    is_active: bool
    is_available: Optional[bool] = None

    model_config = {"from_attributes": True}
