from typing import Optional
from datetime import datetime
from pydantic import BaseModel
from app.schemas.firearm import FirearmSummary
from app.schemas.guard import GuardSummary


class PermissionCreate(BaseModel):
    guard_id: str
    firearm_id: str
    is_permitted: bool


class PermissionUpdate(BaseModel):
    is_permitted: bool


class PermissionOut(BaseModel):
    id: str
    guard_id: str
    firearm_id: str
    is_permitted: bool
    created_at: datetime
    firearm: Optional[FirearmSummary] = None
    guard: Optional[GuardSummary] = None

    model_config = {"from_attributes": True}
