
from datetime import datetime

from app.models import AuditLog


def create_test_audit_logs(db):
    logs = [
        AuditLog(
            actor_id="admin_001",
            action="CREATE",
            entity_type="BUS",
            entity_id="BUS-001",
            old_values=None,
            new_values='{"capacity": 50}',
            created_at=datetime(2026, 10, 20, 10, 0, 0),
        ),
        AuditLog(
            actor_id="admin_001",
            action="UPDATE",
            entity_type="BUS",
            entity_id="BUS-001",
            old_values='{"capacity": 40}',
            new_values='{"capacity": 50}',
            created_at=datetime(2026, 10, 20, 11, 0, 0),
        ),
        AuditLog(
            actor_id="admin_002",
            action="CREATE",
            entity_type="DRIVER",
            entity_id="DRV-001",
            old_values=None,
            new_values='{"driver_name": "Test Driver"}',
            created_at=datetime(2026, 10, 20, 12, 0, 0),
        ),
    ]

    db.add_all(logs)
    db.commit()
    db.refresh(logs[0])
    db.refresh(logs[1])
    db.refresh(logs[2])

    return logs


# 1. GET ALL AUDIT LOGS

def test_get_all_audit_logs(client, db):
    create_test_audit_logs(db)

    response = client.get("/audit-logs/")

    assert response.status_code == 200
    assert len(response.json()) == 3


# 2. GET ALL AUDIT LOGS - EMPTY

def test_get_all_audit_logs_empty(client):
    response = client.get("/audit-logs/")

    assert response.status_code == 200
    assert response.json() == []


# 3. GET AUDIT LOG BY ID

def test_get_audit_log_by_id(client, db):
    logs = create_test_audit_logs(db)

    response = client.get(
        f"/audit-logs/{logs[0].audit_id}"
    )

    assert response.status_code == 200
    assert response.json()["audit_id"] == logs[0].audit_id
    assert response.json()["actor_id"] == "admin_001"


# 4. AUDIT LOG NOT FOUND

def test_get_audit_log_not_found(client):
    response = client.get("/audit-logs/999999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Audit log not found"


# 5. GET LOGS BY ACTOR

def test_get_logs_by_actor(client, db):
    create_test_audit_logs(db)

    response = client.get("/audit-logs/actor/admin_001")

    assert response.status_code == 200
    assert len(response.json()) == 2

    for log in response.json():
        assert log["actor_id"] == "admin_001"


# 6. GET LOGS BY ACTOR - NO RECORDS

def test_get_logs_by_actor_empty(client, db):
    create_test_audit_logs(db)

    response = client.get("/audit-logs/actor/unknown_user")

    assert response.status_code == 200
    assert response.json() == []


# 7. GET LOGS BY ENTITY

def test_get_logs_by_entity(client, db):
    create_test_audit_logs(db)

    response = client.get(
        "/audit-logs/entity/BUS/BUS-001"
    )

    assert response.status_code == 200
    assert len(response.json()) == 2

    for log in response.json():
        assert log["entity_type"] == "BUS"
        assert log["entity_id"] == "BUS-001"


# 8. GET LOGS BY ENTITY - NO RECORDS

def test_get_logs_by_entity_empty(client, db):
    create_test_audit_logs(db)

    response = client.get(
        "/audit-logs/entity/STUDENT/STU-999"
    )

    assert response.status_code == 200
    assert response.json() == []


# 9. GET LOGS BY ACTION

def test_get_logs_by_action(client, db):
    create_test_audit_logs(db)

    response = client.get("/audit-logs/action/create")

    assert response.status_code == 200
    assert len(response.json()) == 2

    for log in response.json():
        assert log["action"] == "CREATE"


# 10. GET LOGS BY ACTION - CASE INSENSITIVE

def test_get_logs_by_action_uppercase(client, db):
    create_test_audit_logs(db)

    response = client.get("/audit-logs/action/CREATE")

    assert response.status_code == 200
    assert len(response.json()) == 2


# 11. GET LOGS BY ACTION - NO RECORDS

def test_get_logs_by_action_empty(client, db):
    create_test_audit_logs(db)

    response = client.get("/audit-logs/action/DELETE")

    assert response.status_code == 200
    assert response.json() == []
