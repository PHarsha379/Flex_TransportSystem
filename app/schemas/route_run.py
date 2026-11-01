
from pydantic import BaseModel, ConfigDict, Field
from datetime import date, time
from typing import Optional


class RouteRunCreate(BaseModel):
    route_id: str
    run_date: date
    trip_number: int = Field(gt=0)
    departure_time: time
    arrival_time: time
    run_status: str = "SCHEDULED"


class RouteRunUpdate(BaseModel):
    departure_time: Optional[time] = None
    arrival_time: Optional[time] = None
    run_status: Optional[str] = None


class RouteRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    run_id: int
    route_id: str
    bus_id: str
    driver_id: str
    run_date: date
    trip_number: int
    departure_time: time
    arrival_time: time
    run_status: str
