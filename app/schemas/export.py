from pydantic import BaseModel
from typing import Optional


class ExportResponse(BaseModel):
    success: bool
    message: str
    filename: str
    total_records: Optional[int] = None


class DatasetExportResponse(BaseModel):
    success: bool
    message: str
    total_students: int
    total_assignments: int
    total_attendance: int