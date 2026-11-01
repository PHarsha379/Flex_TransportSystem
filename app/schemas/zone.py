from pydantic import BaseModel, ConfigDict
from typing import Optional


class ZoneCreate(BaseModel):
    zone_name: str
    latitude: float
    longitude: float
    zone_status: str = "ACTIVE"


class ZoneUpdate(BaseModel):
    zone_name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    zone_status: Optional[str] = None


class ZoneResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    zone_id: int
    zone_name: str
    latitude: float
    longitude: float
    zone_status: str