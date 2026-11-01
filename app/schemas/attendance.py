from pydantic import BaseModel, ConfigDict
from datetime import date, time
from typing import Optional


class AttendanceCreate(BaseModel):
    student_id: str
    assignment_id: str
    attendance_date: date
    pickup_status: str
    pickup_time: Optional[time] = None
    event_type: str
    issue_type: Optional[str] = None


class AttendanceUpdate(BaseModel):
    pickup_status: Optional[str] = None
    pickup_time: Optional[time] = None
    event_type: Optional[str] = None
    issue_type: Optional[str] = None


class AttendanceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    attendance_id: int
    student_id: str
    assignment_id: str
    attendance_date: date
    pickup_status: str
    pickup_time: Optional[time]
    event_type: str
    issue_type: Optional[str]
    