
from datetime import date, time, timedelta

from app.models import Bus, Driver, Route, RouteRun


def create_route_run_test_data(
    db,
    route_status="ACTIVE",
    bus_status="ACTIVE",
    driver_status="ACTIVE",
    effective_from=None,
    effective_to=None,
):
    bus = Bus(
        bus_id="BUS-RUN-001",
        registration_number="RUN-REG-001",
        capacity=50,
        accessible=False,
        bus_status=bus_status,
    )

    driver = Driver(
        driver_id="DRV-RUN-001",
        driver_name="Route Run Driver",
        license_number="RUN-LIC-001",
        phone_number="9876543210",
        driver_status=driver_status,
    )

    db.add_all([bus, driver])
    db.commit()

    route = Route(
        route_id="ROUTE-RUN-001",
        route_name="Route Run Test",
        bus_id=bus.bus_id,
        driver_id=driver.driver_id,
        start_time=time(7, 0),
        end_time=time(9, 0),
        route_status=route_status,
        effective_from=effective_from or date.today() - timedelta(days=10),
        effective_to=effective_to,
    )

    db.add(route)
    db.commit()
    db.refresh(route)

    return route, bus, driver


def route_run_payload(route, **overrides):
    payload = {
        "route_id": route.route_id,
        "run_date": (date.today() + timedelta(days=2)).isoformat(),
        "trip_number": 1,
        "departure_time": "07:15:00",
        "arrival_time": "08:45:00",
        "run_status": "SCHEDULED",
    }

    payload.update(overrides)
    return payload


def create_test_route_run(db):
    route, bus, driver = create_route_run_test_data(db)

    run = RouteRun(
        run_id=1,
        route_id=route.route_id,
        bus_id=bus.bus_id,
        driver_id=driver.driver_id,
        run_date=date.today() + timedelta(days=2),
        trip_number=1,
        departure_time=time(7, 15),
        arrival_time=time(8, 45),
        run_status="SCHEDULED",
    )

    db.add(run)
    db.commit()
    db.refresh(run)

    return run, route


# 1. CREATE ROUTE RUN

def test_create_route_run(client, db):
    route, bus, driver = create_route_run_test_data(db)

    response = client.post(
        "/route-runs/",
        json=route_run_payload(route),
    )

    print("STATUS:", response.status_code)
    print("RESPONSE:", response.json())

    assert response.status_code == 200


# 2. ROUTE NOT FOUND

def test_create_route_run_route_not_found(client):
    response = client.post(
        "/route-runs/",
        json={
            "route_id": "ROUTE-UNKNOWN",
            "run_date": (date.today() + timedelta(days=2)).isoformat(),
            "trip_number": 1,
            "departure_time": "07:15:00",
            "arrival_time": "08:45:00",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Route not found"


# 3. INACTIVE BUS

def test_create_route_run_inactive_bus(client, db):
    route, bus, driver = create_route_run_test_data(
        db,
        bus_status="INACTIVE",
    )

    response = client.post(
        "/route-runs/",
        json=route_run_payload(route),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Bus is not active"


# 4. INACTIVE DRIVER

def test_create_route_run_inactive_driver(client, db):
    route, bus, driver = create_route_run_test_data(
        db,
        driver_status="INACTIVE",
    )

    response = client.post(
        "/route-runs/",
        json=route_run_payload(route),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Driver is not active"


# 5. INACTIVE ROUTE

def test_create_route_run_inactive_route(client, db):
    route, bus, driver = create_route_run_test_data(
        db,
        route_status="INACTIVE",
    )

    response = client.post(
        "/route-runs/",
        json=route_run_payload(route),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Route is not active"


# 6. ARRIVAL BEFORE DEPARTURE

def test_create_route_run_invalid_time(client, db):
    route, bus, driver = create_route_run_test_data(db)

    response = client.post(
        "/route-runs/",
        json=route_run_payload(
            route,
            departure_time="08:30:00",
            arrival_time="08:00:00",
        ),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Arrival time must be after departure time"
    )


# 7. PAST RUN DATE

def test_create_route_run_past_date(client, db):
    route, bus, driver = create_route_run_test_data(db)

    response = client.post(
        "/route-runs/",
        json=route_run_payload(
            route,
            run_date=(date.today() - timedelta(days=1)).isoformat(),
        ),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Cannot create a route run for a past date"
    )


# 8. ROUTE NOT EFFECTIVE ON RUN DATE

def test_create_route_run_outside_effective_date(client, db):
    route, bus, driver = create_route_run_test_data(
        db,
        effective_from=date.today() + timedelta(days=5),
    )

    response = client.post(
        "/route-runs/",
        json=route_run_payload(route),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Route is not effective on this date"
    )


# 9. DEPARTURE BEFORE ROUTE START TIME

def test_create_route_run_early_departure(client, db):
    route, bus, driver = create_route_run_test_data(db)

    response = client.post(
        "/route-runs/",
        json=route_run_payload(
            route,
            departure_time="06:30:00",
        ),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Departure is earlier than the route start time"
    )


# 10. ARRIVAL AFTER ROUTE END TIME

def test_create_route_run_late_arrival(client, db):
    route, bus, driver = create_route_run_test_data(db)

    response = client.post(
        "/route-runs/",
        json=route_run_payload(
            route,
            arrival_time="09:30:00",
        ),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Arrival is later than the route end time"
    )


# 11. DUPLICATE TRIP NUMBER

def test_create_duplicate_route_run(client, db):
    route, bus, driver = create_route_run_test_data(db)

    payload = route_run_payload(route)

    first_response = client.post("/route-runs/", json=payload)
    assert first_response.status_code == 200

    second_response = client.post("/route-runs/", json=payload)

    assert second_response.status_code == 409
    assert second_response.json()["detail"] == (
        "Trip number already exists for this route and date"
    )


# 12. INVALID TRIP NUMBER

def test_create_route_run_invalid_trip_number(client, db):
    route, bus, driver = create_route_run_test_data(db)

    response = client.post(
        "/route-runs/",
        json=route_run_payload(route, trip_number=0),
    )

    assert response.status_code == 422


# 13. GET ALL ROUTE RUNS

def test_get_all_route_runs(client, db):
    create_test_route_run(db)

    response = client.get("/route-runs/")

    assert response.status_code == 200
    assert len(response.json()) == 1


# 14. GET ROUTE RUN BY ID

def test_get_route_run_by_id(client, db):
    run, route = create_test_route_run(db)

    response = client.get(
        f"/route-runs/{run.run_id}"
    )

    assert response.status_code == 200
    assert response.json()["run_id"] == run.run_id


# 15. ROUTE RUN NOT FOUND

def test_get_route_run_not_found(client):
    response = client.get("/route-runs/999999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Route run not found"


# 16. GET RUNS BY ROUTE

def test_get_runs_by_route(client, db):
    run, route = create_test_route_run(db)

    response = client.get(
        f"/route-runs/route/{route.route_id}"
    )

    assert response.status_code == 200
    assert len(response.json()) == 1


# 17. ROUTE NOT FOUND WHEN GETTING RUNS

def test_get_runs_by_route_not_found(client):
    response = client.get(
        "/route-runs/route/ROUTE-UNKNOWN"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Route not found"


# 18. UPDATE ROUTE RUN

def test_update_route_run(client, db):
    run, route = create_test_route_run(db)

    response = client.put(
        f"/route-runs/{run.run_id}",
        json={
            "departure_time": "07:30:00",
            "arrival_time": "08:30:00",
        },
    )

    assert response.status_code == 200
    assert response.json()["departure_time"] == "07:30:00"
    assert response.json()["arrival_time"] == "08:30:00"


# 19. UPDATE ROUTE RUN NOT FOUND

def test_update_route_run_not_found(client):
    response = client.put(
        "/route-runs/999999",
        json={"run_status": "DELAYED"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Route run not found"


# 20. UPDATE WITH INVALID TIME ORDER

def test_update_route_run_invalid_time(client, db):
    run, route = create_test_route_run(db)

    response = client.put(
        f"/route-runs/{run.run_id}",
        json={
            "departure_time": "08:30:00",
            "arrival_time": "08:00:00",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Arrival time must be after departure time"
    )


# 21. UPDATE OUTSIDE ROUTE OPERATING TIMES

def test_update_route_run_outside_operating_times(client, db):
    run, route = create_test_route_run(db)

    response = client.put(
        f"/route-runs/{run.run_id}",
        json={"departure_time": "06:30:00"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Run times must be within route operating times"
    )


# 22. CANCEL ROUTE RUN

def test_cancel_route_run(client, db):
    run, route = create_test_route_run(db)

    response = client.patch(
        f"/route-runs/{run.run_id}/cancel"
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Route run cancelled"
    assert response.json()["run_id"] == run.run_id


# 23. CANCEL COMPLETED ROUTE RUN

def test_cancel_completed_route_run(client, db):
    run, route = create_test_route_run(db)

    run.run_status = "COMPLETED"
    db.commit()

    response = client.patch(
        f"/route-runs/{run.run_id}/cancel"
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Completed runs cannot be cancelled"
    )


# 24. CANCEL ROUTE RUN NOT FOUND

def test_cancel_route_run_not_found(client):
    response = client.patch(
        "/route-runs/999999/cancel"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Route run not found"
