from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.models import (
    GuardianContact,
    Student,
    AttendanceEvent,
    Notification
)
from app.models import Notification

from app.schemas.notification import (
    NotificationCreate,
    NotificationStatusUpdate
)

router = APIRouter(
    prefix="/notifications",
    tags=["Notification Management"]
)


def generate_notification_id(db: Session):

    last_notification = (
        db.query(Notification)
        .order_by(Notification.notification_id.desc())
        .first()
    )

    if last_notification:
        last_number = int(
            last_notification.notification_id.split("-")[-1]
        )
        next_number = last_number + 1
    else:
        next_number = 1

    return f"NOT-{datetime.now().year}-{next_number:06d}"


# 1. Create notification
@router.post("/")
def create_notification(
    payload: NotificationCreate,
    db: Session = Depends(get_db)
):

    student = db.get(Student, payload.student_id)

    if not student:
        raise HTTPException(404, "Student not found")

    guardian = db.get(GuardianContact, payload.guardian_id)

    if not guardian:
        raise HTTPException(404, "Guardian not found")

    if guardian.student_id != payload.student_id:
        raise HTTPException(
            400,
            "Guardian does not belong to this student"
        )

    if guardian.contact_status != "ACTIVE":
        raise HTTPException(
            400,
            "Guardian contact is inactive"
        )

    if not guardian.is_valid:
        raise HTTPException(
            400,
            "Guardian contact is invalid"
        )

    attendance = None

    if payload.attendance_id is not None:

        attendance = db.get(
            AttendanceEvent,
            payload.attendance_id
        )

        if not attendance:
            raise HTTPException(
                404,
                "Attendance record not found"
            )

        if attendance.student_id != payload.student_id:
            raise HTTPException(
                400,
                "Attendance record does not belong to this student"
            )

    notification = Notification(
        notification_id=generate_notification_id(db),
        guardian_id=payload.guardian_id,
        student_id=payload.student_id,
        attendance_id=payload.attendance_id,
        message=payload.message,
        notification_type=payload.notification_type,
        delivery_status="PENDING",
        sent_at=None,
        issue_type=payload.issue_type
    )

    db.add(notification)
    db.commit()
    db.refresh(notification)

    return {
        "message": "Notification created successfully",
        "notification": notification
    }


# 2. Get all notifications
@router.get("/")
def get_notifications(db: Session = Depends(get_db)):

    return db.query(Notification).order_by(
        Notification.notification_id.desc()
    ).all()


# 3. Get notification by ID
@router.get("/{notification_id}")
def get_notification(
    notification_id: str,
    db: Session = Depends(get_db)
):

    notification = db.get(Notification, notification_id)

    if not notification:
        raise HTTPException(
            404,
            "Notification not found"
        )

    return notification


# 4. Get notifications for a student
@router.get("/student/{student_id}")
def get_student_notifications(
    student_id: str,
    db: Session = Depends(get_db)
):

    student = db.get(Student, student_id)

    if not student:
        raise HTTPException(404, "Student not found")

    return db.query(Notification).filter(
        Notification.student_id == student_id
    ).all()


# 5. Get notifications for a guardian
@router.get("/guardian/{guardian_id}")
def get_guardian_notifications(
    guardian_id: str,
    db: Session = Depends(get_db)
):

    guardian = db.get(GuardianContact, guardian_id)

    if not guardian:
        raise HTTPException(404, "Guardian not found")

    return db.query(Notification).filter(
        Notification.guardian_id == guardian_id
    ).all()


# 6. Update delivery status
@router.patch("/{notification_id}/status")
def update_notification_status(
    notification_id: str,
    payload: NotificationStatusUpdate,
    db: Session = Depends(get_db)
):

    notification = db.get(Notification, notification_id)

    if not notification:
        raise HTTPException(
            404,
            "Notification not found"
        )

    allowed_statuses = [
        "PENDING",
        "SENT",
        "FAILED"
    ]

    if payload.delivery_status not in allowed_statuses:
        raise HTTPException(
            400,
            "Invalid delivery status"
        )

    notification.delivery_status = payload.delivery_status

    if payload.delivery_status == "SENT":
        notification.sent_at = datetime.utcnow()

    db.commit()
    db.refresh(notification)

    return {
        "message": "Notification status updated",
        "notification": notification
    }