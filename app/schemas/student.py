from pydantic import BaseModel, ConfigDict, Field
from datetime import time


class StudentCreate(BaseModel):
    student_id: str = Field(pattern=r"^STU-\d{6}$")
    first_name: str
    last_name: str
    grade: str
    synthetic_address: str
    zone_id: int
    requires_accessibility: bool = False
    pickup_start: time
    pickup_end: time
    status: str = "ACTIVE"


class StudentRead(StudentCreate):
    model_config = ConfigDict(from_attributes=True)
