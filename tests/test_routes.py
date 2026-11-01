
from datetime import date, time, timedelta

from app.models import Bus, Driver, Route


def create_route_test_data(db):
    """Create an active bus and driver for route tests."""

    bus = Bus(
        bus_id="BUS-000001",
        registration_number="ROUTE-TEST-BUS",
        capacity=50,
        accessible=True,
        bus_status="ACTIVE",
    )

    driver = Driver(
        driver_id="DRV-000001",
        driver_name="Test Driver",
        license_number="ROUTE-TEST-LIC",
        phone_number="9999999999",
        driver_status="ACTIVE",
    )

    db.add_all([bus, driver])
    db.commit()

    return bus, driver


def create_test_route(db):
    """Create a route directly for read/update/activation tests."""

    bus, driver = create_route_test_data(db)

    route = Route(
        route_id="ROUTE-TEST-001",
        route_name="Test Route",
        bus_id=bus.bus_id,
        driver_id=driver.driver_id,
        start_time=time(7, 0),
        end_time=time(8, 0),
        route_status="DRAFT",
        effective_from=date.today(),
        effective_to=None,
    )

    db.add(route)
    db.commit()
    db.refresh(route)

    return route, bus, driver


def route_payload(bus, driver):
    return {
        "route_name": "Morning School Route",
        "bus_id": bus.bus_id,
        "driver_id": driver.driver_id,
        "start_time": "07:00:00",
        "end_time": "08:00:00",
        "effective_from": date.today().isoformat(),
        "effective_to": None,
    }


# --------------------------------------------------
# 1. CREATE ROUTE
# --------------------------------------------------

def test_create_route(client, db):
    bus, driver = create_route_test_data(db)

    response = client.post(
        "/routes/",
        json=route_payload(bus, driver),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["route_name"] == "Morning School Route"
    assert data["bus_id"] == bus.bus_id
    assert data["driver_id"] == driver.driver_id
    assert data["route_status"] == "DRAFT"
    assert data["route_id"].startswith(f"ROUTE-{date.today().year}-")


# --------------------------------------------------
# 2. CREATE ROUTE WITH INVALID BUS
# --------------------------------------------------

def test_create_route_bus_not_found(client, db):
    payload = {
        "route_name": "Test Route",
        "bus_id": "BUS-999999",
        "driver_id": "DRV-000001",
        "start_time": "07:00:00",
        "end_time": "08:00:00",
        "effective_from": date.today().isoformat(),
    }

    response = client.post("/routes/", json=payload)

    assert response.status_code == 404
    assert response.json()["detail"] == "Bus not found"


# --------------------------------------------------
# 3. CREATE ROUTE WITH INVALID DRIVER
# --------------------------------------------------

def test_create_route_driver_not_found(client, db):
    bus, driver = create_route_test_data(db)

    payload = route_payload(bus, driver)
    payload["driver_id"] = "DRV-999999"

    response = client.post("/routes/", json=payload)

    assert response.status_code == 404
    assert response.json()["detail"] == "Driver not found"


# --------------------------------------------------
# 4. CREATE ROUTE WITH INACTIVE BUS
# --------------------------------------------------

def test_create_route_inactive_bus(client, db):
    bus, driver = create_route_test_data(db)

    bus.bus_status = "INACTIVE"
    db.commit()

    response = client.post(
        "/routes/",
        json=route_payload(bus, driver),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Bus is not active"


# --------------------------------------------------
# 5. CREATE ROUTE WITH INVALID TIME
# --------------------------------------------------

def test_create_route_invalid_time(client, db):
    bus, driver = create_route_test_data(db)

    payload = route_payload(bus, driver)
    payload["start_time"] = "09:00:00"
    payload["end_time"] = "08:00:00"

    response = client.post("/routes/", json=payload)

    assert response.status_code == 400
    assert response.json()["detail"] == "End time must be after start time"


# --------------------------------------------------
# 6. CREATE ROUTE WITH INVALID EFFECTIVE DATES
# --------------------------------------------------

def test_create_route_invalid_effective_dates(client, db):
    bus, driver = create_route_test_data(db)

    payload = route_payload(bus, driver)
    payload["effective_from"] = (
        date.today() + timedelta(days=10)
    ).isoformat()
    payload["effective_to"] = (
        date.today() + timedelta(days=5)
    ).isoformat()

    response = client.post("/routes/", json=payload)

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid route effective dates"


# --------------------------------------------------
# 7. GET ALL ROUTES
# --------------------------------------------------

def test_get_all_routes(client, db):
    create_test_route(db)

    response = client.get("/routes/")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) == 1


# --------------------------------------------------
# 8. GET ROUTE BY ID
# --------------------------------------------------

def test_get_route_by_id(client, db):
    route, bus, driver = create_test_route(db)

    response = client.get(f"/routes/{route.route_id}")

    assert response.status_code == 200
    assert response.json()["route_id"] == route.route_id
    assert response.json()["route_name"] == "Test Route"


# --------------------------------------------------
# 9. GET ROUTE NOT FOUND
# --------------------------------------------------

def test_get_route_not_found(client):
    response = client.get("/routes/ROUTE-UNKNOWN")

    assert response.status_code == 404
    assert response.json()["detail"] == "Route not found"


# --------------------------------------------------
# 10. UPDATE ROUTE
# --------------------------------------------------

def test_update_route(client, db):
    route, bus, driver = create_test_route(db)

    payload = {
        "route_name": "Updated Morning Route",
        "end_time": "08:30:00",
    }

    response = client.put(
        f"/routes/{route.route_id}",
        json=payload,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["route_name"] == "Updated Morning Route"
    assert data["end_time"] == "08:30:00"


# --------------------------------------------------
# 11. UPDATE ROUTE NOT FOUND
# --------------------------------------------------

def test_update_route_not_found(client):
    response = client.put(
        "/routes/ROUTE-UNKNOWN",
        json={"route_name": "Updated Route"},
    )

    assert response.status_code == 404


# --------------------------------------------------
# 12. UPDATE ROUTE WITH INVALID TIME
# --------------------------------------------------

def test_update_route_invalid_time(client, db):
    route, bus, driver = create_test_route(db)

    response = client.put(
        f"/routes/{route.route_id}",
        json={"end_time": "06:00:00"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "End time must be after start time"


# --------------------------------------------------
# 13. ACTIVATE ROUTE
# --------------------------------------------------

def test_activate_route(client, db):
    route, bus, driver = create_test_route(db)

    response = client.patch(
        f"/routes/{route.route_id}/activate"
    )

    assert response.status_code == 200
    assert response.json()["route_status"] == "ACTIVE"


# --------------------------------------------------
# 14. ACTIVATE ROUTE WITH INACTIVE BUS
# --------------------------------------------------

def test_activate_route_inactive_bus(client, db):
    route, bus, driver = create_test_route(db)

    bus.bus_status = "INACTIVE"
    db.commit()

    response = client.patch(
        f"/routes/{route.route_id}/activate"
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Bus is not active"


# --------------------------------------------------
# 15. DEACTIVATE ROUTE
# --------------------------------------------------

def test_deactivate_route(client, db):
    route, bus, driver = create_test_route(db)

    response = client.patch(
        f"/routes/{route.route_id}/deactivate"
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Route deactivated successfully"

    updated_route = db.get(Route, route.route_id)
    assert updated_route.route_status == "INACTIVE"


# --------------------------------------------------
# 16. DEACTIVATE ROUTE NOT FOUND
# --------------------------------------------------

def test_deactivate_route_not_found(client):
    response = client.patch(
        "/routes/ROUTE-UNKNOWN/deactivate"
    )

    assert response.status_code == 404
