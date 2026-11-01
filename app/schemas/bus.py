from pydantic import BaseModel, ConfigDict, Field
from typing import Optional


class BusCreate(BaseModel):
    registration_number: str = Field(min_length=5, max_length=20)
    capacity: int = Field(gt=0)
    accessible: bool = False
    bus_status: str = "ACTIVE"


class BusUpdate(BaseModel):
    registration_number: Optional[str] = None
    capacity: Optional[int] = Field(default=None, gt=0)
    accessible: Optional[bool] = None
    bus_status: Optional[str] = None


class BusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    bus_id: str
    registration_number: str
    capacity: int
    accessible: bool
    bus_status: str