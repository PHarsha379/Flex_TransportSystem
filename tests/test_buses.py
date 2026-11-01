
from app.models import Bus, AuditLog


def create_test_bus(db):
    bus = Bus(
        bus_id="BUS-000001",
        registration_number="TEST-REG-001",
        capacity=50,
        accessible=True,
        bus_status="ACTIVE",
    )

    db.add(bus)
    db.commit()
    db.refresh(bus)

    return bus


# --------------------------------------------------
# 1. CREATE BUS
# --------------------------------------------------

def test_create_bus(client):
    payload = {
        "registration_number": "TEST-REG-100",
        "capacity": 50,
        "accessible": True,
        "bus_status": "ACTIVE",
    }

    response = client.post("/buses/", json=payload)

    assert response.status_code == 200

    data = response.json()

    assert data["bus_id"] == "BUS-000001"
    assert data["registration_number"] == "TEST-REG-100"
    assert data["capacity"] == 50
    assert data["accessible"] is True


# --------------------------------------------------
# 2. CREATE BUS WITH DUPLICATE REGISTRATION
# --------------------------------------------------

def test_create_duplicate_bus(client, db):
    create_test_bus(db)

    payload = {
        "registration_number": "TEST-REG-001",
        "capacity": 40,
        "accessible": False,
        "bus_status": "ACTIVE",
    }

    response = client.post("/buses/", json=payload)

    assert response.status_code == 409
    assert response.json()["detail"] == "Registration number already exists"


# --------------------------------------------------
# 3. GET ALL BUSES
# --------------------------------------------------

def test_get_all_buses(client, db):
    create_test_bus(db)

    response = client.get("/buses/")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) == 1


# --------------------------------------------------
# 4. GET BUS BY ID
# --------------------------------------------------

def test_get_bus_by_id(client, db):
    bus = create_test_bus(db)

    response = client.get(f"/buses/{bus.bus_id}")

    assert response.status_code == 200
    assert response.json()["bus_id"] == bus.bus_id
    assert response.json()["capacity"] == 50


# --------------------------------------------------
# 5. GET BUS WITH INVALID ID
# --------------------------------------------------

def test_get_bus_not_found(client):
    response = client.get("/buses/BUS-999999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Bus not found"


# --------------------------------------------------
# 6. UPDATE BUS
# --------------------------------------------------

def test_update_bus(client, db):
    bus = create_test_bus(db)

    payload = {
        "capacity": 60,
        "accessible": False,
    }

    response = client.put(
        f"/buses/{bus.bus_id}",
        json=payload,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["capacity"] == 60
    assert data["accessible"] is False


# --------------------------------------------------
# 7. UPDATE BUS WITH DUPLICATE REGISTRATION
# --------------------------------------------------

def test_update_duplicate_registration(client, db):
    bus1 = create_test_bus(db)

    bus2 = Bus(
        bus_id="BUS-000002",
        registration_number="TEST-REG-002",
        capacity=40,
        accessible=False,
        bus_status="ACTIVE",
    )

    db.add(bus2)
    db.commit()

    payload = {
        "registration_number": "TEST-REG-001",
    }

    response = client.put(
        f"/buses/{bus2.bus_id}",
        json=payload,
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Registration number already exists"


# --------------------------------------------------
# 8. UPDATE BUS NOT FOUND
# --------------------------------------------------

def test_update_bus_not_found(client):
    payload = {
        "capacity": 60,
    }

    response = client.put(
        "/buses/BUS-999999",
        json=payload,
    )

    assert response.status_code == 404


# --------------------------------------------------
# 9. DEACTIVATE BUS
# --------------------------------------------------

def test_deactivate_bus(client, db):
    bus = create_test_bus(db)

    response = client.patch(
        f"/buses/{bus.bus_id}/deactivate"
    )

    assert response.status_code == 200

    assert response.json()["message"] == "Bus deactivated successfully"

    updated_bus = db.get(Bus, bus.bus_id)

    assert updated_bus.bus_status == "INACTIVE"


# --------------------------------------------------
# 10. DEACTIVATE ALREADY INACTIVE BUS
# --------------------------------------------------

def test_deactivate_already_inactive_bus(client, db):
    bus = create_test_bus(db)

    bus.bus_status = "INACTIVE"
    db.commit()

    response = client.patch(
        f"/buses/{bus.bus_id}/deactivate"
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Bus is already inactive"


# --------------------------------------------------
# 11. DEACTIVATE BUS NOT FOUND
# --------------------------------------------------

def test_deactivate_bus_not_found(client):
    response = client.patch(
        "/buses/BUS-999999/deactivate"
    )

    assert response.status_code == 404


# --------------------------------------------------
# 12. VERIFY AUDIT LOG
# --------------------------------------------------

def test_create_bus_audit_log(client, db):
    payload = {
        "registration_number": "TEST-REG-200",
        "capacity": 55,
        "accessible": True,
        "bus_status": "ACTIVE",
    }

    response = client.post("/buses/", json=payload)

    assert response.status_code == 200

    log = db.query(AuditLog).filter(
        AuditLog.entity_type == "BUS",
        AuditLog.entity_id == response.json()["bus_id"],
        AuditLog.action == "CREATE",
    ).first()

    assert log is not None

