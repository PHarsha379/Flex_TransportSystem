def test_get_student_by_id(client, db):
    from datetime import time
    from app.models import Student, AddressZone

    zone = AddressZone(
        zone_name="TEST-ZONE",
        latitude=16.5062,
        longitude=80.6480,
        zone_status="ACTIVE"
    )

    db.add(zone)
    db.commit()
    db.refresh(zone)

    student = Student(
        student_id="STU-999999",
        first_name="Test",
        last_name="Student",
        grade="5",
        synthetic_address="Test Address",
        zone_id=zone.zone_id,
        requires_accessibility=False,
        pickup_start=time(7, 0),
        pickup_end=time(8, 0),
        status="ACTIVE"
    )

    db.add(student)
    db.commit()

    response = client.get("/students/STU-999999")

    assert response.status_code == 200

    data = response.json()

    assert data["student_id"] == "STU-999999"
    assert data["first_name"] == "Test"
# 1. GET ALL STUDENTS
def test_get_all_students(client):
    response = client.get("/students/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


# 2. GET STUDENT BY INVALID ID
def test_get_student_invalid_id(client):
    response = client.get("/students/STU-999999")
    assert response.status_code == 404


# 3. GET STUDENT WITH EMPTY ID
def test_get_student_empty_id(client):
    response = client.get("/students/")
    assert response.status_code == 200