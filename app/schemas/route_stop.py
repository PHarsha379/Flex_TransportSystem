from pydantic import BaseModel, ConfigDict, Field
from datetime import time
from typing import Optional


class RouteStopCreate(BaseModel):
    stop_id: str
    stop_sequence: int = Field(gt=0)
    estimated_arrival: time
    travel_time_from_previous: int = Field(ge=0)


class RouteStopUpdate(BaseModel):
    stop_sequence: Optional[int] = Field(default=None, gt=0)
    estimated_arrival: Optional[time] = None
    travel_time_from_previous: Optional[int] = Field(
        default=None, ge=0
    )


class RouteStopResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    route_stop_id: int
    route_id: str
    stop_id: str
    stop_sequence: int
    estimated_arrival: time
    travel_time_from_previous: int