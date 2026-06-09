from typing import Optional
from pydantic import BaseModel


class LocationBase(BaseModel):
    name: str
    address: Optional[str] = None


class LocationCreate(LocationBase):
    pass


class LocationUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    is_active: Optional[bool] = None


class LocationOut(LocationBase):
    id: str
    is_active: bool

    model_config = {"from_attributes": True}
