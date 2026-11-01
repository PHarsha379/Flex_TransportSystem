
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional


class DisruptionCreate(BaseModel):
    route_id: str
    run_id: Optional[int] = None

    disruption_type: str
    description: str

    expected_delay_minutes: int = Field(default=0, ge=0)


class DisruptionUpdate(BaseModel):
    description: Optional[str] = None
    expected_delay_minutes: Optional[int] = Field(
        default=None,
        ge=0
    )


class DisruptionStatusUpdate(BaseModel):
    disruption_status: str


class DisruptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    disruption_id: int
    route_id: str
    run_id: Optional[int]
    disruption_type: str
    description: str
    expected_delay_minutes: int
    disruption_status: str
