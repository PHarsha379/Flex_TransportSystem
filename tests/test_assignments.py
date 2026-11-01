
from datetime import date, datetime, time, timedelta

from app.models import (
    AddressZone,
    Student,
    Stop,
    Bus,
    Driver,
    Route,
    RouteStop,
    RouteRun,
)


def create_assignment_test_data(db):
    """Create one valid student, bus, route, stop and future route run."""

    zone = AddressZone(
        zone_name="TEST-ZONE",
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
        bus_id="BUS-TEST-001",
        registration_number="TEST-BUS-001",
        capacity=50,
        accessible=True,
        bus_status="ACTIVE",
    )

    driver = Driver(
        driver_id="DRV-TEST-001",
        driver_name="Test Driver",
        license_number="TEST-LIC-001",
        phone_number="9999999999",
        driver_status="ACTIVE",
    )

    stop = Stop(
        stop_id="STOP-TEST-001",
        stop_name="Test Stop",
        zone_id=zone.zone_id,
        latitude=16.5062,
        longitude=80.6480,
        is_approved=True,
        approval_date=date.today(),
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

    future_date = date.today() + timedelta(days=1)

    route_stop = RouteStop(
        route_id=route.route_id,
        stop_id=stop.stop_id,
        stop_sequence=1,
        estimated_arrival=time(7, 30),
        travel_time_from_previous=0,
    )

    route_run = RouteRun(
        route_id=route.route_id,
        bus_id=bus.bus_id,
        driver_id=driver.driver_id,
        run_date=future_date,
        trip_number=1,
        departure_time=time(7, 0),
        arrival_time=time(8, 0),
        run_status="SCHEDULED",
    )

    db.add_all([route_stop, route_run])
    db.commit()

    return student, stop, route, bus, route_run


# --------------------------------------------------
# 1. VALID ASSIGNMENT
# --------------------------------------------------

def test_validate_assignment_success(client, db):
    student, stop, route, bus, route_run = create_assignment_test_data(db)

    payload = {
        "student_id": student.student_id,
        "route_id": route.route_id,
        "stop_id": stop.stop_id,
        "assigned_date": (date.today() + timedelta(days=1)).isoformat(),
        "current_occupancy": 20,
    }

    response = client.post("/assignments/validate", json=payload)

    assert response.status_code == 200
    assert response.json()["valid"] is True
    assert response.json()["issues"] == []


# --------------------------------------------------
# 2. STUDENT NOT FOUND
# --------------------------------------------------

def test_validate_student_not_found(client, db):
    student, stop, route, bus, route_run = create_assignment_test_data(db)

    payload = {
        "student_id": "STU-999999",
        "route_id": route.route_id,
        "stop_id": stop.stop_id,
        "assigned_date": date.today().isoformat(),
        "current_occupancy": 10,
    }

    response = client.post("/assignments/validate", json=payload)

    assert response.status_code == 404
    assert response.json()["detail"] == "Student not found"


# --------------------------------------------------
# 3. STOP NOT FOUND
# --------------------------------------------------

def test_validate_stop_not_found(client, db):
    student, stop, route, bus, route_run = create_assignment_test_data(db)

    payload = {
        "student_id": student.student_id,
        "route_id": route.route_id,
        "stop_id": "STOP-UNKNOWN",
        "assigned_date": date.today().isoformat(),
        "current_occupancy": 10,
    }

    response = client.post("/assignments/validate", json=payload)

    assert response.status_code == 404
    assert response.json()["detail"] == "Stop not found"


# --------------------------------------------------
# 4. ROUTE NOT FOUND
# --------------------------------------------------

def test_validate_route_not_found(client, db):
    student, stop, route, bus, route_run = create_assignment_test_data(db)

    payload = {
        "student_id": student.student_id,
        "route_id": "ROUTE-UNKNOWN",
        "stop_id": stop.stop_id,
        "assigned_date": date.today().isoformat(),
        "current_occupancy": 10,
    }

    response = client.post("/assignments/validate", json=payload)

    assert response.status_code == 404
    assert response.json()["detail"] == "Route not found"


# --------------------------------------------------
# 5. ASSIGNMENT VALIDATION ISSUES
# --------------------------------------------------

def test_validate_assignment_constraints(client, db):
    student, stop, route, bus, route_run = create_assignment_test_data(db)

    # Introduce validation problems.
    student.requires_accessibility = True
    bus.accessible = False
    stop.is_approved = False
    stop.zone_id = stop.zone_id + 1

    db.commit()

    payload = {
        "student_id": student.student_id,
        "route_id": route.route_id,
        "stop_id": stop.stop_id,
        "assigned_date": date.today().isoformat(),
        "current_occupancy": bus.capacity,
    }

    response = client.post("/assignments/validate", json=payload)

    assert response.status_code == 200

    issues = response.json()["issues"]

    assert "UNAPPROVED_STOP" in issues
    assert "ACCESSIBILITY_MISMATCH" in issues
    assert "ZONE_MISMATCH" in issues
    assert "BUS_CAPACITY_EXCEEDED" in issues
    assert response.json()["valid"] is False


# --------------------------------------------------
# 6. SUCCESSFUL OPTIMIZATION
# --------------------------------------------------

def test_optimize_assignment_success(client, db):
    student, stop, route, bus, route_run = create_assignment_test_data(db)

    response = client.post(
        f"/assignments/optimize/{student.student_id}?top_n=5"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["data"]["student_id"] == student.student_id
    assert data["data"]["total_candidates"] >= 1
    assert len(data["data"]["proposals"]) >= 1

    proposal = data["data"]["proposals"][0]

    assert proposal["route_id"] == route.route_id
    assert proposal["stop_id"] == stop.stop_id
    assert proposal["total_score"] >= 0


# --------------------------------------------------
# 7. OPTIMIZATION STUDENT NOT FOUND
# --------------------------------------------------

def test_optimize_student_not_found(client, db):
    response = client.post("/assignments/optimize/STU-999999")

    assert response.status_code == 400
    assert "was not found" in response.json()["detail"]


# --------------------------------------------------
# 8. INVALID TOP_N
# --------------------------------------------------

def test_optimize_invalid_top_n(client, db):
    response = client.post(
        "/assignments/optimize/STU-123456?top_n=0"
    )

    assert response.status_code == 422
