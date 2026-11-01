def test_overview(client):
    response = client.get("/analytics/overview")

    assert response.status_code == 200

    data = response.json()

    assert data["total_students"] == 0
    assert data["total_buses"] == 0
    assert data["total_routes"] == 0
    assert data["total_assignments"] == 0


def test_students_analytics(client):
    response = client.get("/analytics/students")

    assert response.status_code == 200

    data = response.json()

    assert data["total_students"] == 0
    assert data["active_students"] == 0


def test_bus_analytics(client):
    response = client.get("/analytics/buses")

    assert response.status_code == 200

    data = response.json()

    assert data["total_buses"] == 0
    assert data["total_seat_capacity"] == 0
    assert data["bus_details"] == []


def test_route_analytics(client):
    response = client.get("/analytics/routes")

    assert response.status_code == 200

    data = response.json()

    assert data["total_routes"] == 0
    assert data["route_details"] == []


def test_attendance_analytics(client):
    response = client.get("/analytics/attendance")

    assert response.status_code == 200

    data = response.json()

    assert data["total_attendance_records"] == 0
    assert data["attendance_by_status"] == {}


def test_zone_analytics(client):
    response = client.get("/analytics/zones")

    assert response.status_code == 200

    data = response.json()

    assert data["total_zones"] == 0
    assert data["zone_wise_students"] == []