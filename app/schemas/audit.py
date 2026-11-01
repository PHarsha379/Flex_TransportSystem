from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class AuditLogCreate(BaseModel):
    actor_id: str
    action: str
    entity_type: str
    entity_id: str
    old_values: Optional[str] = None
    new_values: Optional[str] = None


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    audit_id: int
    actor_id: str
    action: str
    entity_type: str
    entity_id: str
    old_values: Optional[str]
    new_values: Optional[str]
    created_at: datetime