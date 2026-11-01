from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime


class GenerationRunCreate(BaseModel):
    seed: int = 20261022


class GenerationRunUpdate(BaseModel):
    students_generated: Optional[int] = Field(default=None, ge=0)
    buses_generated: Optional[int] = Field(default=None, ge=0)
    stops_generated: Optional[int] = Field(default=None, ge=0)
    routes_generated: Optional[int] = Field(default=None, ge=0)
    assignments_generated: Optional[int] = Field(default=None, ge=0)


class GenerationRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    generation_id: int
    seed: int
    generation_status: str
    started_at: datetime
    completed_at: Optional[datetime]

    students_generated: int
    buses_generated: int
    stops_generated: int
    routes_generated: int
    assignments_generated: int

    error_message: Optional[str]