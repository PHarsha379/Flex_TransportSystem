
from app.models import Driver


def create_test_driver(db):
    driver = Driver(
        driver_id="DRV-000001",
        driver_name="Test Driver",
        license_number="TEST-LIC-001",
        phone_number="9999999999",
        driver_status="ACTIVE",
    )

    db.add(driver)
    db.commit()
    db.refresh(driver)

    return driver


# --------------------------------------------------
# 1. CREATE DRIVER
# --------------------------------------------------

def test_create_driver(client):
    payload = {
        "driver_name": "John Smith",
        "license_number": "LIC-12345",
        "phone_number": "9876543210",
        "driver_status": "ACTIVE",
    }

    response = client.post("/drivers/", json=payload)

    assert response.status_code == 200

    data = response.json()

    assert data["driver_id"] == "DRV-000001"
    assert data["driver_name"] == "John Smith"
    assert data["license_number"] == "LIC-12345"


# --------------------------------------------------
# 2. CREATE DRIVER WITH DUPLICATE LICENSE
# --------------------------------------------------

def test_create_duplicate_driver(client, db):
    create_test_driver(db)

    payload = {
        "driver_name": "Another Driver",
        "license_number": "TEST-LIC-001",
        "phone_number": "8888888888",
        "driver_status": "ACTIVE",
    }

    response = client.post("/drivers/", json=payload)

    assert response.status_code == 409
    assert response.json()["detail"] == "License number already exists"


# --------------------------------------------------
# 3. GET ALL DRIVERS
# --------------------------------------------------

def test_get_all_drivers(client, db):
    create_test_driver(db)

    response = client.get("/drivers/")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) == 1


# --------------------------------------------------
# 4. GET DRIVER BY ID
# --------------------------------------------------

def test_get_driver_by_id(client, db):
    driver = create_test_driver(db)

    response = client.get(f"/drivers/{driver.driver_id}")

    assert response.status_code == 200

    data = response.json()

    assert data["driver_id"] == driver.driver_id
    assert data["driver_name"] == "Test Driver"


# --------------------------------------------------
# 5. GET DRIVER NOT FOUND
# --------------------------------------------------

def test_get_driver_not_found(client):
    response = client.get("/drivers/DRV-999999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Driver not found"


# --------------------------------------------------
# 6. UPDATE DRIVER
# --------------------------------------------------

def test_update_driver(client, db):
    driver = create_test_driver(db)

    payload = {
        "driver_name": "Updated Driver",
        "phone_number": "8888888888",
    }

    response = client.put(
        f"/drivers/{driver.driver_id}",
        json=payload,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["driver_name"] == "Updated Driver"
    assert data["phone_number"] == "8888888888"


# --------------------------------------------------
# 7. UPDATE DRIVER WITH DUPLICATE LICENSE
# --------------------------------------------------

def test_update_duplicate_license(client, db):
    driver1 = create_test_driver(db)

    driver2 = Driver(
        driver_id="DRV-000002",
        driver_name="Second Driver",
        license_number="TEST-LIC-002",
        phone_number="7777777777",
        driver_status="ACTIVE",
    )

    db.add(driver2)
    db.commit()

    payload = {
        "license_number": "TEST-LIC-001",
    }

    response = client.put(
        f"/drivers/{driver2.driver_id}",
        json=payload,
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "License number already exists"


# --------------------------------------------------
# 8. UPDATE DRIVER NOT FOUND
# --------------------------------------------------

def test_update_driver_not_found(client):
    payload = {
        "driver_name": "Updated Name",
    }

    response = client.put(
        "/drivers/DRV-999999",
        json=payload,
    )

    assert response.status_code == 404


# --------------------------------------------------
# 9. DEACTIVATE DRIVER
# --------------------------------------------------

def test_deactivate_driver(client, db):
    driver = create_test_driver(db)

    response = client.patch(
        f"/drivers/{driver.driver_id}/deactivate"
    )

    assert response.status_code == 200

    assert response.json()["message"] == "Driver deactivated successfully"

    updated_driver = db.get(Driver, driver.driver_id)

    assert updated_driver.driver_status == "INACTIVE"


# --------------------------------------------------
# 10. DEACTIVATE DRIVER NOT FOUND
# --------------------------------------------------

def test_deactivate_driver_not_found(client):
    response = client.patch(
        "/drivers/DRV-999999/deactivate"
    )

    assert response.status_code == 404


# --------------------------------------------------
# 11. INVALID DRIVER DATA
# --------------------------------------------------

def test_create_driver_invalid_data(client):
    payload = {
        "driver_name": "J",
        "license_number": "123",
        "phone_number": "123",
        "driver_status": "ACTIVE",
    }

    response = client.post("/drivers/", json=payload)

    assert response.status_code == 422
