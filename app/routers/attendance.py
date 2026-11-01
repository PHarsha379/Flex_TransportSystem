from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Student, Assignment, AttendanceEvent
from app.schemas.attendance import AttendanceCreate, AttendanceUpdate

from datetime import datetime

router = APIRouter(
    prefix="/attendance",
    tags=["Attendance Management"]
)


VALID_STATUSES = [
    "PICKED_UP",
    "ABSENT",
    "LATE_PICKUP",
    "MISSED"
]


# 1. Mark attendance
@router.post("/")
def mark_attendance(
    payload: AttendanceCreate,
    db: Session = Depends(get_db)
):

    student = db.get(Student, payload.student_id)

    if not student:
        raise HTTPException(404, "Student not found")

    assignment = db.get(Assignment, payload.assignment_id)

    if not assignment:
        raise HTTPException(404, "Assignment not found")

    if assignment.student_id != payload.student_id:
        raise HTTPException(
            400,
            "Assignment does not belong to this student"
        )

    if assignment.assignment_status != "ACTIVE":
        raise HTTPException(
            400,
            "Attendance cannot be recorded for an inactive assignment"
        )

    if payload.pickup_status not in VALID_STATUSES:
        raise HTTPException(
            400,
            "Invalid pickup status"
        )

    if payload.pickup_status in ["PICKED_UP", "LATE_PICKUP"]:
        if payload.pickup_time is None:
            raise HTTPException(
                400,
                "Pickup time is required for picked-up statuses"
            )

    existing = db.query(AttendanceEvent).filter(
        AttendanceEvent.student_id == payload.student_id,
        AttendanceEvent.assignment_id == payload.assignment_id,
        AttendanceEvent.attendance_date == payload.attendance_date
    ).first()

    if existing:
        raise HTTPException(
            409,
            "Attendance already recorded for this student and assignment"
        )

    attendance = AttendanceEvent(
        student_id=payload.student_id,
        assignment_id=payload.assignment_id,
        attendance_date=payload.attendance_date,
        pickup_status=payload.pickup_status,
        pickup_time=payload.pickup_time,
        event_type=payload.event_type,
        issue_type=payload.issue_type,
        created_at=datetime.utcnow()
    )

    db.add(attendance)
    db.commit()
    db.refresh(attendance)

    return {
        "message": "Attendance recorded successfully",
        "attendance": attendance
    }


# 2. Get all attendance records
@router.get("/")
def get_all_attendance(db: Session = Depends(get_db)):
    return db.query(AttendanceEvent).order_by(
        AttendanceEvent.attendance_date.desc()
    ).all()


# 3. Get attendance by ID
@router.get("/{attendance_id}")
def get_attendance(
    attendance_id: int,
    db: Session = Depends(get_db)
):

    attendance = db.get(AttendanceEvent, attendance_id)

    if not attendance:
        raise HTTPException(404, "Attendance record not found")

    return attendance


# 4. Get attendance for a student
@router.get("/student/{student_id}")
def get_student_attendance(
    student_id: str,
    db: Session = Depends(get_db)
):

    student = db.get(Student, student_id)

    if not student:
        raise HTTPException(404, "Student not found")

    return db.query(AttendanceEvent).filter(
        AttendanceEvent.student_id == student_id
    ).order_by(
        AttendanceEvent.attendance_date.desc()
    ).all()


# 5. Update attendance
@router.put("/{attendance_id}")
def update_attendance(
    attendance_id: int,
    payload: AttendanceUpdate,
    db: Session = Depends(get_db)
):

    attendance = db.get(AttendanceEvent, attendance_id)

    if not attendance:
        raise HTTPException(404, "Attendance record not found")

    updates = payload.model_dump(exclude_unset=True)

    if (
        "pickup_status" in updates
        and updates["pickup_status"] not in VALID_STATUSES
    ):
        raise HTTPException(400, "Invalid pickup status")

    new_status = updates.get(
        "pickup_status",
        attendance.pickup_status
    )

    new_time = updates.get(
        "pickup_time",
        attendance.pickup_time
    )

    if new_status in ["PICKED_UP", "LATE_PICKUP"] and new_time is None:
        raise HTTPException(
            400,
            "Pickup time is required for picked-up statuses"
        )

    for field, value in updates.items():
        setattr(attendance, field, value)

    db.commit()
    db.refresh(attendance)

    return attendance