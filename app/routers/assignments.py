from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.assignment import AssignmentProposal
from app.models import Student, Stop, Route, Bus

from app.services.optimization_service import (
    optimize_student_assignment,
    OptimizationServiceError,
)


router = APIRouter(
    prefix="/assignments",
    tags=["Assignments"]
)


# --------------------------------------------------
# 1. VALIDATE ASSIGNMENT
# --------------------------------------------------

@router.post("/validate")
def validate_assignment(
    payload: AssignmentProposal,
    db: Session = Depends(get_db)
):
    student = db.get(Student, payload.student_id)
    stop = db.get(Stop, payload.stop_id)
    route = db.get(Route, payload.route_id)

    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    if not stop:
        raise HTTPException(status_code=404, detail="Stop not found")

    if not route:
        raise HTTPException(status_code=404, detail="Route not found")

    bus = db.get(Bus, route.bus_id)

    if not bus:
        raise HTTPException(status_code=404, detail="Bus not found")

    issues = []

    if str(student.status).upper() != "ACTIVE":
        issues.append("STUDENT_INACTIVE")

    if not stop.is_approved:
        issues.append("UNAPPROVED_STOP")

    if student.requires_accessibility and not bus.accessible:
        issues.append("ACCESSIBILITY_MISMATCH")

    if stop.zone_id != student.zone_id:
        issues.append("ZONE_MISMATCH")

    if payload.current_occupancy >= bus.capacity:
        issues.append("BUS_CAPACITY_EXCEEDED")

    return {
        "valid": len(issues) == 0,
        "student_id": student.student_id,
        "route_id": route.route_id,
        "stop_id": stop.stop_id,
        "issues": issues,
        "note": "Starter validation only; route-run availability and pickup-window checks are handled separately."
    }


# --------------------------------------------------
# 2. OPTIMIZE STUDENT ASSIGNMENT
# --------------------------------------------------

@router.post("/optimize/{student_id}")
def optimize_assignment(
    student_id: str,
    top_n: int = Query(default=5, ge=1, le=20),
    db: Session = Depends(get_db)
):
    try:
        result = optimize_student_assignment(
            db=db,
            student_id=student_id,
            top_n=top_n
        )

        return {
            "success": True,
            "message": "Assignment optimization completed",
            "data": result
        }

    except OptimizationServiceError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Optimization failed: {str(exc)}"
        )