
from datetime import date, time

from app.models import (
    AddressZone,
    Student,
    GuardianContact,
    Notification,
)


def create_notification_test_data(db):
    zone = AddressZone(
        zone_name="NOTIFICATION-TEST-ZONE",
        latitude=16.5062,
        longitude=80.6480,
        zone_status="ACTIVE",
    )

    db.add(zone)
    db.commit()
    db.refresh(zone)

    student = Student(
        student_id="STU-123456",
        first_name="Test",
        last_name="Student",
        grade="5",
        synthetic_address="Test Address",
        zone_id=zone.zone_id,
        requires_accessibility=False,
        pickup_start=time(7, 0),
        pickup_end=time(8, 0),
        status="ACTIVE",
    )

    db.add(student)
    db.commit()

    guardian = GuardianContact(
        guardian_id="GDN-000001",
        student_id=student.student_id,
        guardian_name="Test Guardian",
        phone_number="9876543210",
        email="guardian@test.com",
        is_primary=True,
        is_valid=True,
        contact_status="ACTIVE",
    )

    db.add(guardian)
    db.commit()

    db.refresh(student)
    db.refresh(guardian)

    return student, guardian


def create_test_notification(db):
    student, guardian = create_notification_test_data(db)

    notification = Notification(
        notification_id="NOT-2026-000001",
        guardian_id=guardian.guardian_id,
        student_id=student.student_id,
        attendance_id=None,
        message="Student attendance notification",
        notification_type="ATTENDANCE",
        delivery_status="PENDING",
        sent_at=None,
        issue_type=None,
    )

    db.add(notification)
    db.commit()
    db.refresh(notification)

    return notification, student, guardian


def notification_payload(student, guardian):
    return {
        "guardian_id": guardian.guardian_id,
        "student_id": student.student_id,
        "attendance_id": None,
        "message": "Student attendance notification",
        "notification_type": "ATTENDANCE",
        "issue_type": None,
    }


# --------------------------------------------------
# 1. CREATE NOTIFICATION
# --------------------------------------------------

def test_create_notification(client, db):
    student, guardian = create_notification_test_data(db)

    response = client.post(
        "/notifications/",
        json=notification_payload(student, guardian),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["message"] == "Notification created successfully"
    assert data["notification"]["student_id"] == student.student_id
    assert data["notification"]["guardian_id"] == guardian.guardian_id
    assert data["notification"]["delivery_status"] == "PENDING"


# --------------------------------------------------
# 2. STUDENT NOT FOUND
# --------------------------------------------------

def test_create_notification_student_not_found(client, db):
    student, guardian = create_notification_test_data(db)

    payload = notification_payload(student, guardian)
    payload["student_id"] = "STU-999999"

    response = client.post("/notifications/", json=payload)

    assert response.status_code == 404
    assert response.json()["detail"] == "Student not found"


# --------------------------------------------------
# 3. GUARDIAN NOT FOUND
# --------------------------------------------------

def test_create_notification_guardian_not_found(client, db):
    student, guardian = create_notification_test_data(db)

    payload = notification_payload(student, guardian)
    payload["guardian_id"] = "GDN-999999"

    response = client.post("/notifications/", json=payload)

    assert response.status_code == 404
    assert response.json()["detail"] == "Guardian not found"


# --------------------------------------------------
# 4. GUARDIAN BELONGS TO ANOTHER STUDENT
# --------------------------------------------------

def test_create_notification_wrong_guardian(client, db):
    student, guardian = create_notification_test_data(db)

    another_student = Student(
        student_id="STU-654321",
        first_name="Another",
        last_name="Student",
        grade="6",
        synthetic_address="Another Address",
        zone_id=student.zone_id,
        requires_accessibility=False,
        pickup_start=time(7, 0),
        pickup_end=time(8, 0),
        status="ACTIVE",
    )

    db.add(another_student)
    db.commit()

    payload = notification_payload(student, guardian)
    payload["student_id"] = another_student.student_id

    response = client.post("/notifications/", json=payload)

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Guardian does not belong to this student"
    )


# --------------------------------------------------
# 5. INACTIVE GUARDIAN
# --------------------------------------------------

def test_create_notification_inactive_guardian(client, db):
    student, guardian = create_notification_test_data(db)

    guardian.contact_status = "INACTIVE"
    db.commit()

    response = client.post(
        "/notifications/",
        json=notification_payload(student, guardian),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Guardian contact is inactive"


# --------------------------------------------------
# 6. INVALID GUARDIAN CONTACT
# --------------------------------------------------

def test_create_notification_invalid_guardian(client, db):
    student, guardian = create_notification_test_data(db)

    guardian.is_valid = False
    db.commit()

    response = client.post(
        "/notifications/",
        json=notification_payload(student, guardian),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Guardian contact is invalid"


# --------------------------------------------------
# 7. GET ALL NOTIFICATIONS
# --------------------------------------------------

def test_get_all_notifications(client, db):
    create_test_notification(db)

    response = client.get("/notifications/")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) == 1


# --------------------------------------------------
# 8. GET NOTIFICATION BY ID
# --------------------------------------------------

def test_get_notification_by_id(client, db):
    notification, student, guardian = create_test_notification(db)

    response = client.get(
        f"/notifications/{notification.notification_id}"
    )

    assert response.status_code == 200

    assert response.json()["notification_id"] == (
        notification.notification_id
    )


# --------------------------------------------------
# 9. NOTIFICATION NOT FOUND
# --------------------------------------------------

def test_get_notification_not_found(client):
    response = client.get("/notifications/NOT-2026-999999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Notification not found"


# --------------------------------------------------
# 10. GET STUDENT NOTIFICATIONS
# --------------------------------------------------

def test_get_student_notifications(client, db):
    notification, student, guardian = create_test_notification(db)

    response = client.get(
        f"/notifications/student/{student.student_id}"
    )

    assert response.status_code == 200
    assert len(response.json()) == 1


# --------------------------------------------------
# 11. STUDENT NOTIFICATIONS NOT FOUND
# --------------------------------------------------

def test_get_student_notifications_not_found(client):
    response = client.get(
        "/notifications/student/STU-999999"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Student not found"


# --------------------------------------------------
# 12. GET GUARDIAN NOTIFICATIONS
# --------------------------------------------------

def test_get_guardian_notifications(client, db):
    notification, student, guardian = create_test_notification(db)

    response = client.get(
        f"/notifications/guardian/{guardian.guardian_id}"
    )

    assert response.status_code == 200
    assert len(response.json()) == 1


# --------------------------------------------------
# 13. GUARDIAN NOTIFICATIONS NOT FOUND
# --------------------------------------------------

def test_get_guardian_notifications_not_found(client):
    response = client.get(
        "/notifications/guardian/GDN-999999"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Guardian not found"


# --------------------------------------------------
# 14. UPDATE DELIVERY STATUS TO SENT
# --------------------------------------------------

def test_update_notification_status_sent(client, db):
    notification, student, guardian = create_test_notification(db)

    response = client.patch(
        f"/notifications/{notification.notification_id}/status",
        json={"delivery_status": "SENT"},
    )

    assert response.status_code == 200

    data = response.json()["notification"]

    assert data["delivery_status"] == "SENT"
    assert data["sent_at"] is not None


# --------------------------------------------------
# 15. UPDATE DELIVERY STATUS TO FAILED
# --------------------------------------------------

def test_update_notification_status_failed(client, db):
    notification, student, guardian = create_test_notification(db)

    response = client.patch(
        f"/notifications/{notification.notification_id}/status",
        json={"delivery_status": "FAILED"},
    )

    assert response.status_code == 200
    assert response.json()["notification"]["delivery_status"] == "FAILED"


# --------------------------------------------------
# 16. INVALID DELIVERY STATUS
# --------------------------------------------------

def test_update_notification_invalid_status(client, db):
    notification, student, guardian = create_test_notification(db)

    response = client.patch(
        f"/notifications/{notification.notification_id}/status",
        json={"delivery_status": "UNKNOWN"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid delivery status"


# --------------------------------------------------
# 17. UPDATE NOTIFICATION NOT FOUND
# --------------------------------------------------

def test_update_notification_not_found(client):
    response = client.patch(
        "/notifications/NOT-2026-999999/status",
        json={"delivery_status": "SENT"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Notification not found"
