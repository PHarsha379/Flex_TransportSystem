import json
from datetime import datetime

from app.models import AuditLog


def create_audit_log(
    db,
    actor_id,
    action,
    entity_type,
    entity_id,
    old_values=None,
    new_values=None
):

    audit = AuditLog(
        actor_id=actor_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        old_values=(
            json.dumps(old_values, default=str)
            if old_values is not None else None
        ),
        new_values=(
            json.dumps(new_values, default=str)
            if new_values is not None else None
        ),
        created_at=datetime.utcnow()
    )

    db.add(audit)

    return audit