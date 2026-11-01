from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import date, time


class RouteCreate(BaseModel):
    route_name: str = Field(min_length=2, max_length=100)
    bus_id: str
    driver_id: str
    start_time: time
    end_time: time
    effective_from: date
    effective_to: Optional[date] = None


class RouteUpdate(BaseModel):
    route_name: Optional[str] = None
    bus_id: Optional[str] = None
    driver_id: Optional[str] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    route_status: Optional[str] = None


class RouteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    route_id: str
    route_name: str
    bus_id: str
    driver_id: str
    start_time: time
    end_time: time
    route_status: str
    effective_from: date
    effective_to: Optional[date] = None