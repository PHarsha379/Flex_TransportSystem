from pydantic import BaseModel
from datetime import date


class ReallocationRequest(BaseModel):
    new_run_id: str
    new_stop_id: str
    change_reason: str
    changed_by: str
    assigned_date: date