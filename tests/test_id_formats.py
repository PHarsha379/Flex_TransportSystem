from app.utils.id_generator import generate_student_id, generate_stop_id, generate_bus_id


def test_deterministic_ids():
    assert generate_student_id(1) == "STU-000001"
    assert generate_stop_id(1) == "STOP-000001"
    assert generate_bus_id(1) == "BUS-000001"
