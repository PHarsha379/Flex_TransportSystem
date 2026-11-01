from pydantic import BaseModel, ConfigDict, Field
from typing import Optional


class GuardianCreate(BaseModel):
    student_id: str
    guardian_name: str = Field(min_length=2, max_length=100)
    phone_number: str
    email: Optional[str] = None
    is_primary: bool = False
    is_valid: bool = True
    contact_status: str = "ACTIVE"


class GuardianUpdate(BaseModel):
    guardian_name: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None
    is_primary: Optional[bool] = None


class GuardianResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    guardian_id: str
    student_id: str
    guardian_name: str
    phone_number: str
    email: Optional[str]
    is_primary: bool
    is_valid: bool
    contact_status: str