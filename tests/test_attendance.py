
from datetime import date, time, datetime, timedelta

from app.models import (
    AddressZone,
    Student,
    Bus,
    Driver,
    Stop,
    Route,
    Assignment,
    AttendanceEvent,
)


def create_attendance_test_data(db):
    zone = AddressZone(
        zone_name="ATTENDANCE-TEST-ZONE",
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

    bus = Bus(
        bus_id="BUS-000001",
        registration_number="ATT-TEST-BUS",
        capacity=50,
        accessible=True,
        bus_status="ACTIVE",
    )

    driver = Driver(
        driver_id="DRV-000001",
        driver_name="Test Driver",
        license_number="ATT-TEST-LIC",
        phone_number="9999999999",
        driver_status="ACTIVE",
    )

    stop = Stop(
        stop_id="STOP-000001",
        stop_name="Test Stop",
        zone_id=zone.zone_id,
        latitude=16.5062,
        longitude=80.6480,
        is_approved=True,
        stop_status="ACTIVE",
    )

    db.add_all([student, bus, driver, stop])
    db.commit()

    route = Route(
        route_id="ROUTE-TEST-001",
        route_name="Test Route",
        bus_id=bus.bus_id,
        driver_id=driver.driver_id,
        start_time=time(7, 0),
        end_time=time(8, 0),
        route_status="ACTIVE",
        effective_from=date.today(),
    )

    db.add(route)
    db.commit()

    assignment = Assignment(
        assignment_id="ASN-TEST-000001",
        student_id=student.student_id,
        route_id=route.route_id,
        stop_id=stop.stop_id,
        run_id=None,
        assigned_date=date.today(),
        effective_from=date.today(),
        effective_to=None,
        assignment_status="ACTIVE",
    )

    db.add(assignment)
    db.commit()
    db.refresh(assignment)

    return student, assignment


def create_test_attendance(db):
    student, assignment = create_attendance_test_data(db)

    attendance = AttendanceEvent(
        student_id=student.student_id,
        assignment_id=assignment.assignment_id,
        attendance_date=date.today(),
        pickup_status="ABSENT",
        pickup_time=None,
        event_type="DAILY_ATTENDANCE",
        issue_type=None,
        created_at=datetime.utcnow(),
    )

    db.add(attendance)
    db.commit()
    db.refresh(attendance)

    return attendance, student, assignment


def attendance_payload(student, assignment):
    return {
        "student_id": student.student_id,
        "assignment_id": assignment.assignment_id,
        "attendance_date": date.today().isoformat(),
        "pickup_status": "ABSENT",
        "pickup_time": None,
        "event_type": "DAILY_ATTENDANCE",
        "issue_type": None,
    }


# --------------------------------------------------
# 1. MARK ATTENDANCE
# --------------------------------------------------

def test_mark_attendance(client, db):
    student, assignment = create_attendance_test_data(db)

    response = client.post(
        "/attendance/",
        json=attendance_payload(student, assignment),
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Attendance recorded successfully"

    data = response.json()["attendance"]

    assert data["student_id"] == student.student_id
    assert data["assignment_id"] == assignment.assignment_id
    assert data["pickup_status"] == "ABSENT"


# --------------------------------------------------
# 2. STUDENT NOT FOUND
# --------------------------------------------------

def test_mark_attendance_student_not_found(client, db):
    student, assignment = create_attendance_test_data(db)

    payload = attendance_payload(student, assignment)
    payload["student_id"] = "STU-999999"

    response = client.post("/attendance/", json=payload)

    assert response.status_code == 404
    assert response.json()["detail"] == "Student not found"


# --------------------------------------------------
# 3. ASSIGNMENT NOT FOUND
# --------------------------------------------------

def test_mark_attendance_assignment_not_found(client, db):
    student, assignment = create_attendance_test_data(db)

    payload = attendance_payload(student, assignment)
    payload["assignment_id"] = "ASN-UNKNOWN"

    response = client.post("/attendance/", json=payload)

    assert response.status_code == 404
    assert response.json()["detail"] == "Assignment not found"


# --------------------------------------------------
# 4. ASSIGNMENT BELONGS TO ANOTHER STUDENT
# --------------------------------------------------

def test_mark_attendance_wrong_student(client, db):
    student, assignment = create_attendance_test_data(db)

    payload = attendance_payload(student, assignment)
    payload["student_id"] = "STU-999999"

    response = client.post("/attendance/", json=payload)

    assert response.status_code == 404
    assert response.json()["detail"] == "Student not found"


# --------------------------------------------------
# 5. INACTIVE ASSIGNMENT
# --------------------------------------------------

def test_mark_attendance_inactive_assignment(client, db):
    student, assignment = create_attendance_test_data(db)

    assignment.assignment_status = "INACTIVE"
    db.commit()

    response = client.post(
        "/attendance/",
        json=attendance_payload(student, assignment),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Attendance cannot be recorded for an inactive assignment"
    )


# --------------------------------------------------
# 6. INVALID PICKUP STATUS
# --------------------------------------------------

def test_mark_attendance_invalid_status(client, db):
    student, assignment = create_attendance_test_data(db)

    payload = attendance_payload(student, assignment)
    payload["pickup_status"] = "UNKNOWN"

    response = client.post("/attendance/", json=payload)

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid pickup status"


# --------------------------------------------------
# 7. PICKUP TIME REQUIRED
# --------------------------------------------------

def test_mark_attendance_missing_pickup_time(client, db):
    student, assignment = create_attendance_test_data(db)

    payload = attendance_payload(student, assignment)
    payload["pickup_status"] = "PICKED_UP"
    payload["pickup_time"] = None

    response = client.post("/attendance/", json=payload)

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Pickup time is required for picked-up statuses"
    )


# --------------------------------------------------
# 8. DUPLICATE ATTENDANCE
# --------------------------------------------------

def test_duplicate_attendance(client, db):
    student, assignment = create_attendance_test_data(db)

    payload = attendance_payload(student, assignment)

    first_response = client.post("/attendance/", json=payload)
    second_response = client.post("/attendance/", json=payload)

    assert first_response.status_code == 200
    assert second_response.status_code == 409

    assert "already recorded" in second_response.json()["detail"]


# --------------------------------------------------
# 9. GET ALL ATTENDANCE
# --------------------------------------------------

def test_get_all_attendance(client, db):
    create_test_attendance(db)

    response = client.get("/attendance/")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) == 1


# --------------------------------------------------
# 10. GET ATTENDANCE BY ID
# --------------------------------------------------

def test_get_attendance_by_id(client, db):
    attendance, student, assignment = create_test_attendance(db)

    response = client.get(
        f"/attendance/{attendance.attendance_id}"
    )

    assert response.status_code == 200
    assert response.json()["attendance_id"] == attendance.attendance_id


# --------------------------------------------------
# 11. ATTENDANCE NOT FOUND
# --------------------------------------------------

def test_get_attendance_not_found(client):
    response = client.get("/attendance/999999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Attendance record not found"


# --------------------------------------------------
# 12. GET STUDENT ATTENDANCE
# --------------------------------------------------

def test_get_student_attendance(client, db):
    attendance, student, assignment = create_test_attendance(db)

    response = client.get(
        f"/attendance/student/{student.student_id}"
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["student_id"] == student.student_id


# --------------------------------------------------
# 13. STUDENT ATTENDANCE NOT FOUND
# --------------------------------------------------

def test_get_student_attendance_not_found(client):
    response = client.get(
        "/attendance/student/STU-999999"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Student not found"


# --------------------------------------------------
# 14. UPDATE ATTENDANCE
# --------------------------------------------------

def test_update_attendance(client, db):
    attendance, student, assignment = create_test_attendance(db)

    payload = {
        "pickup_status": "MISSED",
        "event_type": "PICKUP_ISSUE",
        "issue_type": "STUDENT_NOT_PRESENT",
    }

    response = client.put(
        f"/attendance/{attendance.attendance_id}",
        json=payload,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["pickup_status"] == "MISSED"
    assert data["event_type"] == "PICKUP_ISSUE"
    assert data["issue_type"] == "STUDENT_NOT_PRESENT"


# --------------------------------------------------
# 15. UPDATE ATTENDANCE NOT FOUND
# --------------------------------------------------

def test_update_attendance_not_found(client):
    response = client.put(
        "/attendance/999999",
        json={"pickup_status": "MISSED"},
    )

    assert response.status_code == 404


# --------------------------------------------------
# 16. UPDATE WITH INVALID STATUS
# --------------------------------------------------

def test_update_attendance_invalid_status(client, db):
    attendance, student, assignment = create_test_attendance(db)

    response = client.put(
        f"/attendance/{attendance.attendance_id}",
        json={"pickup_status": "UNKNOWN"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid pickup status"


# --------------------------------------------------
# 17. UPDATE PICKUP STATUS WITHOUT TIME
# --------------------------------------------------

def test_update_attendance_missing_pickup_time(client, db):
    attendance, student, assignment = create_test_attendance(db)

    response = client.put(
        f"/attendance/{attendance.attendance_id}",
        json={
            "pickup_status": "PICKED_UP",
            "pickup_time": None,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Pickup time is required for picked-up statuses"
    )
