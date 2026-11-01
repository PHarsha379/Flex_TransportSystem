def generate_student_id(number: int) -> str:
    return f"STU-{number:06d}"


def generate_stop_id(number: int) -> str:
    return f"STOP-{number:06d}"


def generate_bus_id(number: int) -> str:
    return f"BUS-{number:06d}"


def generate_route_id(number: int, year: int = 2026) -> str:
    return f"ROUTE-{year}-{number:06d}"


def generate_assignment_id(student_id: str, year: int = 2026) -> str:
    return f"ASN-{student_id}-{year}"


def generate_notification_id(number: int, year: int = 2026) -> str:
    return f"NOT-{year}-{number:06d}"
