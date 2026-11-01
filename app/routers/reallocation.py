from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date

from app.database import get_db
from app.models import Assignment, AssignmentHistory
from app.schemas.reallocation import ReallocationRequest

router = APIRouter(
    prefix="/assignments",
    tags=["Assignment Reallocation"]
)


@router.patch("/{assignment_id}/reallocate")
def reallocate_assignment(
    assignment_id: str,
    payload: ReallocationRequest,
    db: Session = Depends(get_db)
):

    old_assignment = db.get(Assignment, assignment_id)

    if not old_assignment:
        raise HTTPException(404, "Assignment not found")

    if old_assignment.assignment_status != "ACTIVE":
        raise HTTPException(
            400,
            "Only active assignments can be reallocated"
        )

    if payload.assigned_date != old_assignment.assigned_date:
        raise HTTPException(
            400,
            "Reallocation date must match the existing assignment date"
        )

    # Validate new assignment using existing assignment engine
    from app.routers.assignments import validate_assignment
    from app.schemas.assignment import AssignmentProposal

    proposal = AssignmentProposal(
        student_id=old_assignment.student_id,
        run_id=payload.new_run_id,
        stop_id=payload.new_stop_id,
        assigned_date=payload.assigned_date
    )

    result, issues = validate_assignment(proposal, db)

    # The current assignment should not block its own reallocation.
    if "STUDENT_ALREADY_ASSIGNED" in issues:
        issues.remove("STUDENT_ALREADY_ASSIGNED")

    # Do not reallocate to the same trip and stop.
    if (
        old_assignment.run_id == payload.new_run_id
        and old_assignment.stop_id == payload.new_stop_id
    ):
        issues.append("SAME_ASSIGNMENT")

    if issues:
        raise HTTPException(
            400,
            {
                "message": "Reallocation validation failed",
                "issues": issues
            }
        )

    new_assignment_id = (
        f"ASN-{old_assignment.student_id}-{payload.assigned_date.year}"
    )

    # The original annual ID may already exist.
    # Use a separate versioned ID for the replacement assignment.
    new_assignment_id = (
        f"{new_assignment_id}-R{old_assignment.assignment_id.count('-R') + 1}"
    )

    if db.get(Assignment, new_assignment_id):
        raise HTTPException(409, "Replacement assignment ID already exists")

    try:
        history = AssignmentHistory(
            assignment_id=old_assignment.assignment_id,
            old_route_id=old_assignment.route_id,
            new_route_id=result["route"].route_id,
            old_stop_id=old_assignment.stop_id,
            new_stop_id=payload.new_stop_id,
            old_status=old_assignment.assignment_status,
            new_status="REASSIGNED",
            changed_by=payload.changed_by,
            change_reason=payload.change_reason
        )

        old_assignment.assignment_status = "REASSIGNED"
        old_assignment.effective_to = payload.assigned_date

        new_assignment = Assignment(
            assignment_id=new_assignment_id,
            student_id=old_assignment.student_id,
            route_id=result["route"].route_id,
            stop_id=payload.new_stop_id,
            run_id=payload.new_run_id,
            assigned_date=payload.assigned_date,
            effective_from=payload.assigned_date,
            effective_to=None,
            assignment_status="ACTIVE",
            assignment_score=None
        )

        db.add(history)
        db.add(new_assignment)
        db.commit()
        db.refresh(new_assignment)

    except Exception:
        db.rollback()
        raise HTTPException(
            500,
            "Could not complete assignment reallocation"
        )

    return {
        "message": "Assignment reallocated successfully",
        "old_assignment_id": old_assignment.assignment_id,
        "new_assignment": new_assignment
    }
@router.patch("/{assignment_id}/cancel")
def cancel_assignment(
    assignment_id: str,
    changed_by: str,
    change_reason: str,
    db: Session = Depends(get_db)
):

    assignment = db.get(Assignment, assignment_id)

    if not assignment:
        raise HTTPException(404, "Assignment not found")

    if assignment.assignment_status != "ACTIVE":
        raise HTTPException(
            400,
            "Only active assignments can be cancelled"
        )

    try:
        history = AssignmentHistory(
            assignment_id=assignment.assignment_id,
            old_route_id=assignment.route_id,
            new_route_id=None,
            old_stop_id=assignment.stop_id,
            new_stop_id=None,
            old_status=assignment.assignment_status,
            new_status="CANCELLED",
            changed_by=changed_by,
            change_reason=change_reason
        )

        assignment.assignment_status = "CANCELLED"
        assignment.effective_to = date.today()

        db.add(history)
        db.commit()

    except Exception:
        db.rollback()
        raise HTTPException(500, "Could not cancel assignment")

    return {
        "message": "Assignment cancelled successfully",
        "assignment_id": assignment_id
    }