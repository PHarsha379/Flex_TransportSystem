from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AuditLog

router = APIRouter(
    prefix="/audit-logs",
    tags=["Audit Management"]
)


# 1. Get all audit logs
@router.get("/")
def get_all_audit_logs(
    db: Session = Depends(get_db)
):

    return db.query(AuditLog).order_by(
        AuditLog.created_at.desc()
    ).all()


# 2. Get audit log by ID
@router.get("/{audit_id}")
def get_audit_log(
    audit_id: int,
    db: Session = Depends(get_db)
):

    audit = db.get(AuditLog, audit_id)

    if not audit:
        raise HTTPException(
            status_code=404,
            detail="Audit log not found"
        )

    return audit


# 3. Get logs by actor
@router.get("/actor/{actor_id}")
def get_logs_by_actor(
    actor_id: str,
    db: Session = Depends(get_db)
):

    return db.query(AuditLog).filter(
        AuditLog.actor_id == actor_id
    ).order_by(
        AuditLog.created_at.desc()
    ).all()


# 4. Get logs by entity
@router.get("/entity/{entity_type}/{entity_id}")
def get_logs_by_entity(
    entity_type: str,
    entity_id: str,
    db: Session = Depends(get_db)
):

    return db.query(AuditLog).filter(
        AuditLog.entity_type == entity_type,
        AuditLog.entity_id == entity_id
    ).order_by(
        AuditLog.created_at.desc()
    ).all()


# 5. Get logs by action
@router.get("/action/{action}")
def get_logs_by_action(
    action: str,
    db: Session = Depends(get_db)
):

    return db.query(AuditLog).filter(
        AuditLog.action == action.upper()
    ).order_by(
        AuditLog.created_at.desc()
    ).all()