from typing import Optional
from pydantic import BaseModel


class AmmunitionTypeBase(BaseModel):
    name: str
    description: Optional[str] = None


class AmmunitionTypeCreate(AmmunitionTypeBase):
    pass


class AmmunitionTypeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class AmmunitionTypeOut(AmmunitionTypeBase):
    id: str
    is_active: bool

    model_config = {"from_attributes": True}
