from pydantic import BaseModel, Field
from datetime import date


class AssignmentProposal(BaseModel):
    student_id: str
    route_id: str
    stop_id: str
    assigned_date: date
    current_occupancy: int = Field(ge=0)
