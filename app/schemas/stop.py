from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import date


class StopCreate(BaseModel):
    stop_name: str = Field(min_length=2, max_length=100)
    zone_id: int
    latitude: float
    longitude: float


class StopUpdate(BaseModel):
    stop_name: Optional[str] = None
    zone_id: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    stop_status: Optional[str] = None


class StopResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    stop_id: str
    stop_name: str
    zone_id: int
    latitude: float
    longitude: float
    is_approved: bool
    approval_date: Optional[date] = None
    stop_status: str