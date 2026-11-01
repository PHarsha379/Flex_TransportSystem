def validate_assignment_rules(student, stop, route, bus, current_occupancy):
    issues = []
    if student.status != "ACTIVE":
        issues.append("STUDENT_INACTIVE")
    if not stop.is_approved:
        issues.append("UNAPPROVED_STOP")
    if student.requires_accessibility and not bus.accessible:
        issues.append("ACCESSIBILITY_MISMATCH")
    if student.zone_id != stop.zone_id:
        issues.append("ZONE_MISMATCH")
    if current_occupancy >= bus.capacity:
        issues.append("BUS_CAPACITY_EXCEEDED")
    return {"valid": not issues, "issues": issues}
