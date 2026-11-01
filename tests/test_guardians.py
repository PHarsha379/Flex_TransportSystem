
from datetime import date, time

from app.models import Student, AddressZone, GuardianContact


def create_test_student(db, student_id="STU-123456"):
    zone = AddressZone(
        zone_name="GUARDIAN-TEST-ZONE",
        latitude=16.5062,
        longitude=80.6480,
        zone_status="ACTIVE",
    )

    db.add(zone)
    db.commit()
    db.refresh(zone)

    student = Student(
        student_id=student_id,
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
    db.refresh(student)

    return student


def create_test_guardian(db, student_id="STU-123456"):
    student = create_test_student(db, student_id)

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
    db.refresh(guardian)

    return guardian, student


# --------------------------------------------------
# 1. CREATE GUARDIAN
# --------------------------------------------------

def test_create_guardian(client, db):
    student = create_test_student(db)

    payload = {
        "student_id": student.student_id,
        "guardian_name": "John Guardian",
        "phone_number": "9876543210",
        "email": "john@test.com",
        "is_primary": True,
        "is_valid": True,
        "contact_status": "ACTIVE",
    }

    response = client.post("/guardians/", json=payload)

    assert response.status_code == 200

    data = response.json()

    assert data["guardian_id"] == "GDN-000001"
    assert data["student_id"] == student.student_id
    assert data["guardian_name"] == "John Guardian"
    assert data["is_primary"] is True


# --------------------------------------------------
# 2. CREATE GUARDIAN WITH INVALID STUDENT
# --------------------------------------------------

def test_create_guardian_student_not_found(client):
    payload = {
        "student_id": "STU-999999",
        "guardian_name": "John Guardian",
        "phone_number": "9876543210",
        "email": "john@test.com",
    }

    response = client.post("/guardians/", json=payload)

    assert response.status_code == 404
    assert response.json()["detail"] == "Student not found"


# --------------------------------------------------
# 3. CREATE GUARDIAN FOR INACTIVE STUDENT
# --------------------------------------------------

def test_create_guardian_inactive_student(client, db):
    student = create_test_student(db)

    student.status = "INACTIVE"
    db.commit()

    payload = {
        "student_id": student.student_id,
        "guardian_name": "John Guardian",
        "phone_number": "9876543210",
        "email": "john@test.com",
    }

    response = client.post("/guardians/", json=payload)

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Cannot add guardian to inactive student"
    )


# --------------------------------------------------
# 4. CREATE DUPLICATE PRIMARY GUARDIAN
# --------------------------------------------------

def test_create_duplicate_primary_guardian(client, db):
    guardian, student = create_test_guardian(db)

    payload = {
        "student_id": student.student_id,
        "guardian_name": "Second Guardian",
        "phone_number": "8888888888",
        "email": "second@test.com",
        "is_primary": True,
    }

    response = client.post("/guardians/", json=payload)

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Student already has a primary guardian"
    )


# --------------------------------------------------
# 5. GET ALL GUARDIANS
# --------------------------------------------------

def test_get_all_guardians(client, db):
    create_test_guardian(db)

    response = client.get("/guardians/")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) == 1


# --------------------------------------------------
# 6. GET GUARDIAN BY ID
# --------------------------------------------------

def test_get_guardian_by_id(client, db):
    guardian, student = create_test_guardian(db)

    response = client.get(
        f"/guardians/{guardian.guardian_id}"
    )

    assert response.status_code == 200
    assert response.json()["guardian_id"] == guardian.guardian_id
    assert response.json()["guardian_name"] == "Test Guardian"


# --------------------------------------------------
# 7. GET GUARDIAN NOT FOUND
# --------------------------------------------------

def test_get_guardian_not_found(client):
    response = client.get("/guardians/GDN-999999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Guardian not found"


# --------------------------------------------------
# 8. GET GUARDIANS BY STUDENT ID
# --------------------------------------------------

def test_get_student_guardians(client, db):
    guardian, student = create_test_guardian(db)

    response = client.get(
        f"/guardians/student/{student.student_id}"
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["student_id"] == student.student_id


# --------------------------------------------------
# 9. GET GUARDIANS FOR INVALID STUDENT
# --------------------------------------------------

def test_get_student_guardians_not_found(client):
    response = client.get(
        "/guardians/student/STU-999999"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Student not found"


# --------------------------------------------------
# 10. UPDATE GUARDIAN
# --------------------------------------------------

def test_update_guardian(client, db):
    guardian, student = create_test_guardian(db)

    payload = {
        "guardian_name": "Updated Guardian",
        "phone_number": "8888888888",
    }

    response = client.put(
        f"/guardians/{guardian.guardian_id}",
        json=payload,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["guardian_name"] == "Updated Guardian"
    assert data["phone_number"] == "8888888888"


# --------------------------------------------------
# 11. UPDATE GUARDIAN NOT FOUND
# --------------------------------------------------

def test_update_guardian_not_found(client):
    response = client.put(
        "/guardians/GDN-999999",
        json={"guardian_name": "Updated Guardian"},
    )

    assert response.status_code == 404


# --------------------------------------------------
# 12. UPDATE WITH ANOTHER PRIMARY GUARDIAN
# --------------------------------------------------

def test_update_duplicate_primary_guardian(client, db):
    guardian1, student = create_test_guardian(db)

    guardian2 = GuardianContact(
        guardian_id="GDN-000002",
        student_id=student.student_id,
        guardian_name="Second Guardian",
        phone_number="8888888888",
        email="second@test.com",
        is_primary=False,
        is_valid=True,
        contact_status="ACTIVE",
    )

    db.add(guardian2)
    db.commit()

    response = client.put(
        f"/guardians/{guardian2.guardian_id}",
        json={"is_primary": True},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Another primary guardian already exists"
    )


# --------------------------------------------------
# 13. DEACTIVATE GUARDIAN
# --------------------------------------------------

def test_deactivate_guardian(client, db):
    guardian, student = create_test_guardian(db)

    response = client.patch(
        f"/guardians/{guardian.guardian_id}/deactivate"
    )

    assert response.status_code == 200
    assert response.json()["message"] == (
        "Guardian deactivated successfully"
    )

    updated_guardian = db.get(
        GuardianContact, guardian.guardian_id
    )

    assert updated_guardian.contact_status == "INACTIVE"
    assert updated_guardian.is_primary is False


# --------------------------------------------------
# 14. DEACTIVATE GUARDIAN NOT FOUND
# --------------------------------------------------

def test_deactivate_guardian_not_found(client):
    response = client.patch(
        "/guardians/GDN-999999/deactivate"
    )

    assert response.status_code == 404


# --------------------------------------------------
# 15. UPDATE CONTACT VALIDITY
# --------------------------------------------------

def test_update_guardian_validity(client, db):
    guardian, student = create_test_guardian(db)

    response = client.patch(
        f"/guardians/{guardian.guardian_id}/validity",
        params={"is_valid": False},
    )

    assert response.status_code == 200

    assert response.json()["is_valid"] is False
    assert response.json()["message"] == "Contact validity updated"

    updated_guardian = db.get(
        GuardianContact, guardian.guardian_id
    )

    assert updated_guardian.is_valid is False


# --------------------------------------------------
# 16. UPDATE CONTACT VALIDITY NOT FOUND
# --------------------------------------------------

def test_update_guardian_validity_not_found(client):
    response = client.patch(
        "/guardians/GDN-999999/validity",
        params={"is_valid": False},
    )

    assert response.status_code == 404
