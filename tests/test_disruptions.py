
from datetime import date, time

from app.models import (
    AddressZone,
    Bus,
    Driver,
    Route,
    RouteRun,
    RouteDisruption,
)


def create_disruption_test_data(db):
    zone = AddressZone(
        zone_name="DISRUPTION-TEST-ZONE",
        latitude=16.5062,
        longitude=80.6480,
        zone_status="ACTIVE",
    )
    db.add(zone)
    db.commit()
    db.refresh(zone)

    bus = Bus(
        bus_id="BUS-TEST-001",
        registration_number="TEST-REG-001",
        capacity=50,
        accessible=False,
        bus_status="ACTIVE",
    )
    driver = Driver(
        driver_id="DRV-TEST-001",
        driver_name="Test Driver",
        license_number="TEST-LIC-001",
        phone_number="9876543210",
        driver_status="ACTIVE",
    )
    db.add_all([bus, driver])
    db.commit()

    route = Route(
        route_id="ROUTE-TEST-001",
        route_name="Test Route",
        bus_id=bus.bus_id,
        driver_id=driver.driver_id,
        start_time=time(7, 0),
        end_time=time(9, 0),
        route_status="ACTIVE",
        effective_from=date(2026, 1, 1),
        effective_to=None,
    )
    db.add(route)
    db.commit()
    db.refresh(route)

    run = RouteRun(
        route_id=route.route_id,
        bus_id=bus.bus_id,
        driver_id=driver.driver_id,
        run_date=date(2026, 11, 2),
        trip_number=1,
        departure_time=time(7, 0),
        arrival_time=time(9, 0),
        run_status="SCHEDULED",
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    return route, run


def create_test_disruption(db):
    route, run = create_disruption_test_data(db)

    disruption = RouteDisruption(
        route_id=route.route_id,
        run_id=run.run_id,
        disruption_type="TRAFFIC_DELAY",
        description="Heavy traffic near school",
        expected_delay_minutes=20,
        disruption_status="OPEN",
    )

    db.add(disruption)
    db.commit()
    db.refresh(disruption)

    return disruption, route, run


def disruption_payload(route, run=None):
    return {
        "route_id": route.route_id,
        "run_id": run.run_id if run else None,
        "disruption_type": "TRAFFIC_DELAY",
        "description": "Heavy traffic near school",
        "expected_delay_minutes": 20,
    }


# 1. REPORT DISRUPTION

def test_report_disruption(client, db):
    route, run = create_disruption_test_data(db)

    response = client.post(
        "/disruptions/",
        json=disruption_payload(route, run),
    )

    assert response.status_code == 200
    data = response.json()

    assert data["message"] == "Disruption reported successfully"
    assert data["disruption"]["route_id"] == route.route_id
    assert data["disruption"]["disruption_status"] == "OPEN"


# 2. ROUTE NOT FOUND

def test_report_disruption_route_not_found(client):
    response = client.post(
        "/disruptions/",
        json={
            "route_id": "ROUTE-UNKNOWN",
            "run_id": None,
            "disruption_type": "TRAFFIC_DELAY",
            "description": "Traffic delay",
            "expected_delay_minutes": 15,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Route not found"


# 3. INVALID DISRUPTION TYPE

def test_report_invalid_disruption_type(client, db):
    route, run = create_disruption_test_data(db)

    payload = disruption_payload(route, run)
    payload["disruption_type"] = "INVALID_TYPE"

    response = client.post("/disruptions/", json=payload)

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid disruption type"


# 4. ROUTE RUN NOT FOUND

def test_report_disruption_run_not_found(client, db):
    route, run = create_disruption_test_data(db)

    payload = disruption_payload(route)
    payload["run_id"] = 999999

    response = client.post("/disruptions/", json=payload)

    assert response.status_code == 404
    assert response.json()["detail"] == "Route run not found"


# 5. ROUTE RUN DOES NOT BELONG TO ROUTE

def test_report_disruption_wrong_run(client, db):
    route, run = create_disruption_test_data(db)

    another_route = Route(
        route_id="ROUTE-TEST-002",
        route_name="Another Route",
        bus_id=route.bus_id,
        driver_id=route.driver_id,
        start_time=time(10, 0),
        end_time=time(12, 0),
        route_status="ACTIVE",
        effective_from=date(2026, 1, 1),
        effective_to=None,
    )
    db.add(another_route)
    db.commit()

    payload = disruption_payload(another_route, run)

    response = client.post("/disruptions/", json=payload)

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Route run does not belong to this route"
    )


# 6. NEGATIVE DELAY VALIDATION

def test_report_disruption_negative_delay(client, db):
    route, run = create_disruption_test_data(db)

    payload = disruption_payload(route, run)
    payload["expected_delay_minutes"] = -10

    response = client.post("/disruptions/", json=payload)

    assert response.status_code == 422


# 7. GET ALL DISRUPTIONS

def test_get_all_disruptions(client, db):
    create_test_disruption(db)

    response = client.get("/disruptions/")

    assert response.status_code == 200
    assert len(response.json()) == 1


# 8. GET DISRUPTION BY ID

def test_get_disruption_by_id(client, db):
    disruption, route, run = create_test_disruption(db)

    response = client.get(
        f"/disruptions/{disruption.disruption_id}"
    )

    assert response.status_code == 200
    assert response.json()["disruption_id"] == disruption.disruption_id


# 9. DISRUPTION NOT FOUND

def test_get_disruption_not_found(client):
    response = client.get("/disruptions/999999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Disruption not found"


# 10. GET DISRUPTIONS BY ROUTE

def test_get_route_disruptions(client, db):
    disruption, route, run = create_test_disruption(db)

    response = client.get(
        f"/disruptions/route/{route.route_id}"
    )

    assert response.status_code == 200
    assert len(response.json()) == 1


# 11. ROUTE NOT FOUND FOR DISRUPTION LIST

def test_get_route_disruptions_route_not_found(client):
    response = client.get(
        "/disruptions/route/ROUTE-UNKNOWN"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Route not found"


# 12. UPDATE DISRUPTION

def test_update_disruption(client, db):
    disruption, route, run = create_test_disruption(db)

    response = client.put(
        f"/disruptions/{disruption.disruption_id}",
        json={
            "description": "Updated traffic delay",
            "expected_delay_minutes": 35,
        },
    )

    assert response.status_code == 200
    assert response.json()["description"] == "Updated traffic delay"
    assert response.json()["expected_delay_minutes"] == 35


# 13. UPDATE DISRUPTION NOT FOUND

def test_update_disruption_not_found(client):
    response = client.put(
        "/disruptions/999999",
        json={"description": "Updated description"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Disruption not found"


# 14. NEGATIVE DELAY ON UPDATE

def test_update_disruption_negative_delay(client, db):
    disruption, route, run = create_test_disruption(db)

    response = client.put(
        f"/disruptions/{disruption.disruption_id}",
        json={"expected_delay_minutes": -5},
    )

    assert response.status_code == 422


# 15. RESOLVED DISRUPTION CANNOT BE UPDATED

def test_update_resolved_disruption(client, db):
    disruption, route, run = create_test_disruption(db)

    disruption.disruption_status = "RESOLVED"
    db.commit()

    response = client.put(
        f"/disruptions/{disruption.disruption_id}",
        json={"description": "Trying to update"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Resolved disruption cannot be updated"
    )


# 16. UPDATE STATUS TO IN PROGRESS

def test_update_disruption_status_in_progress(client, db):
    disruption, route, run = create_test_disruption(db)

    response = client.patch(
        f"/disruptions/{disruption.disruption_id}/status",
        json={"disruption_status": "IN_PROGRESS"},
    )

    assert response.status_code == 200
    assert response.json()["disruption"]["disruption_status"] == "IN_PROGRESS"


# 17. UPDATE STATUS TO RESOLVED

def test_update_disruption_status_resolved(client, db):
    disruption, route, run = create_test_disruption(db)

    response = client.patch(
        f"/disruptions/{disruption.disruption_id}/status",
        json={"disruption_status": "RESOLVED"},
    )

    assert response.status_code == 200

    data = response.json()["disruption"]

    assert data["disruption_status"] == "RESOLVED"
    assert data["resolved_at"] is not None


# 18. INVALID DISRUPTION STATUS

def test_update_invalid_disruption_status(client, db):
    disruption, route, run = create_test_disruption(db)

    response = client.patch(
        f"/disruptions/{disruption.disruption_id}/status",
        json={"disruption_status": "CANCELLED"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid disruption status"


# 19. UPDATE STATUS NOT FOUND

def test_update_disruption_status_not_found(client):
    response = client.patch(
        "/disruptions/999999/status",
        json={"disruption_status": "RESOLVED"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Disruption not found"
