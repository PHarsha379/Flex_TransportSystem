
from datetime import date

from app.models import AddressZone, Stop


def create_test_zone(db, zone_name="TEST-ZONE"):
    zone = AddressZone(
        zone_name=zone_name,
        latitude=16.5062,
        longitude=80.6480,
        zone_status="ACTIVE",
    )

    db.add(zone)
    db.commit()
    db.refresh(zone)

    return zone


def create_test_stop(db):
    zone = create_test_zone(db)

    stop = Stop(
        stop_id="STOP-000001",
        stop_name="Test Bus Stop",
        zone_id=zone.zone_id,
        latitude=16.5062,
        longitude=80.6480,
        is_approved=False,
        stop_status="ACTIVE",
    )

    db.add(stop)
    db.commit()
    db.refresh(stop)

    return stop, zone


# --------------------------------------------------
# 1. CREATE STOP
# --------------------------------------------------

def test_create_stop(client, db):
    zone = create_test_zone(db)

    payload = {
        "stop_name": "School Bus Stop",
        "zone_id": zone.zone_id,
        "latitude": 16.5062,
        "longitude": 80.6480,
    }

    response = client.post("/stops/", json=payload)

    assert response.status_code == 200

    data = response.json()

    assert data["stop_id"] == "STOP-000001"
    assert data["stop_name"] == "School Bus Stop"
    assert data["is_approved"] is False
    assert data["zone_id"] == zone.zone_id


# --------------------------------------------------
# 2. CREATE STOP WITH INVALID ZONE
# --------------------------------------------------

def test_create_stop_invalid_zone(client):
    payload = {
        "stop_name": "Test Stop",
        "zone_id": 999999,
        "latitude": 16.5062,
        "longitude": 80.6480,
    }

    response = client.post("/stops/", json=payload)

    assert response.status_code == 404
    assert response.json()["detail"] == "Address zone not found"


# --------------------------------------------------
# 3. CREATE STOP IN INACTIVE ZONE
# --------------------------------------------------

def test_create_stop_inactive_zone(client, db):
    zone = create_test_zone(db)

    zone.zone_status = "INACTIVE"
    db.commit()

    payload = {
        "stop_name": "Test Stop",
        "zone_id": zone.zone_id,
        "latitude": 16.5062,
        "longitude": 80.6480,
    }

    response = client.post("/stops/", json=payload)

    assert response.status_code == 400
    assert response.json()["detail"] == "Cannot create stop in an inactive zone"


# --------------------------------------------------
# 4. GET ALL STOPS
# --------------------------------------------------

def test_get_all_stops(client, db):
    create_test_stop(db)

    response = client.get("/stops/")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) == 1


# --------------------------------------------------
# 5. GET STOP BY ID
# --------------------------------------------------

def test_get_stop_by_id(client, db):
    stop, zone = create_test_stop(db)

    response = client.get(f"/stops/{stop.stop_id}")

    assert response.status_code == 200
    assert response.json()["stop_id"] == stop.stop_id
    assert response.json()["stop_name"] == "Test Bus Stop"


# --------------------------------------------------
# 6. GET STOP NOT FOUND
# --------------------------------------------------

def test_get_stop_not_found(client):
    response = client.get("/stops/STOP-999999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Stop not found"


# --------------------------------------------------
# 7. UPDATE STOP
# --------------------------------------------------

def test_update_stop(client, db):
    stop, zone = create_test_stop(db)

    payload = {
        "stop_name": "Updated Bus Stop",
        "latitude": 16.5100,
        "longitude": 80.6500,
    }

    response = client.put(
        f"/stops/{stop.stop_id}",
        json=payload,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["stop_name"] == "Updated Bus Stop"
    assert data["latitude"] == 16.5100


# --------------------------------------------------
# 8. UPDATE STOP NOT FOUND
# --------------------------------------------------

def test_update_stop_not_found(client):
    response = client.put(
        "/stops/STOP-999999",
        json={"stop_name": "Updated Stop"},
    )

    assert response.status_code == 404


# --------------------------------------------------
# 9. UPDATE STOP WITH INVALID ZONE
# --------------------------------------------------

def test_update_stop_invalid_zone(client, db):
    stop, zone = create_test_stop(db)

    response = client.put(
        f"/stops/{stop.stop_id}",
        json={"zone_id": 999999},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Address zone not found"


# --------------------------------------------------
# 10. UPDATE STOP TO INACTIVE ZONE
# --------------------------------------------------

def test_update_stop_inactive_zone(client, db):
    stop, zone = create_test_stop(db)

    zone.zone_status = "INACTIVE"
    db.commit()

    response = client.put(
        f"/stops/{stop.stop_id}",
        json={"zone_id": zone.zone_id},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Cannot move stop to an inactive zone"


# --------------------------------------------------
# 11. APPROVE STOP
# --------------------------------------------------

def test_approve_stop(client, db):
    stop, zone = create_test_stop(db)

    response = client.patch(
        f"/stops/{stop.stop_id}/approve"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["is_approved"] is True
    assert data["approval_date"] == date.today().isoformat()


# --------------------------------------------------
# 12. APPROVE STOP NOT FOUND
# --------------------------------------------------

def test_approve_stop_not_found(client):
    response = client.patch(
        "/stops/STOP-999999/approve"
    )

    assert response.status_code == 404


# --------------------------------------------------
# 13. APPROVE INACTIVE STOP
# --------------------------------------------------

def test_approve_inactive_stop(client, db):
    stop, zone = create_test_stop(db)

    stop.stop_status = "INACTIVE"
    db.commit()

    response = client.patch(
        f"/stops/{stop.stop_id}/approve"
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Cannot approve an inactive stop"


# --------------------------------------------------
# 14. DEACTIVATE STOP
# --------------------------------------------------

def test_deactivate_stop(client, db):
    stop, zone = create_test_stop(db)

    response = client.patch(
        f"/stops/{stop.stop_id}/deactivate"
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Stop deactivated successfully"

    updated_stop = db.get(Stop, stop.stop_id)

    assert updated_stop.stop_status == "INACTIVE"


# --------------------------------------------------
# 15. DEACTIVATE STOP NOT FOUND
# --------------------------------------------------

def test_deactivate_stop_not_found(client):
    response = client.patch(
        "/stops/STOP-999999/deactivate"
    )

    assert response.status_code == 404
