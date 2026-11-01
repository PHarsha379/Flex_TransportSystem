from pydantic import BaseModel, ConfigDict, Field
from typing import Optional


class DriverCreate(BaseModel):
    driver_name: str = Field(min_length=2, max_length=100)
    license_number: str = Field(min_length=5, max_length=30)
    phone_number: str = Field(min_length=10, max_length=20)
    driver_status: str = "ACTIVE"


class DriverUpdate(BaseModel):
    driver_name: Optional[str] = None
    license_number: Optional[str] = None
    phone_number: Optional[str] = None
    driver_status: Optional[str] = None


class DriverResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    driver_id: str
    driver_name: str
    license_number: str
    phone_number: str
    driver_status: str