from pydantic import BaseModel, ConfigDict, Field
from typing import Optional


class NotificationCreate(BaseModel):
    guardian_id: str
    student_id: str
    attendance_id: Optional[int] = None
    message: str = Field(min_length=1)
    notification_type: str
    issue_type: Optional[str] = None


class NotificationStatusUpdate(BaseModel):
    delivery_status: str


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    notification_id: str
    guardian_id: str
    student_id: str
    attendance_id: Optional[int]
    message: str
    notification_type: str
    delivery_status: str
    issue_type: Optional[str]
    