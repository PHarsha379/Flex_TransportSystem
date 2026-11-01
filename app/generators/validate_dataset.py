
from sqlalchemy import func
from app.database import SessionLocal

from app.models import (
    AddressZone,
    Student,
    GuardianContact,
    Stop,
    Bus,
    Driver,
    Route,
    RouteStop,
    RouteRun,
    Assignment,
    AttendanceEvent,
    GenerationRun
)


def validate_dataset():

    db = SessionLocal()

    errors = []
    warnings = []

    try:
        print("\nSTUDENT TRANSPORT DATA VALIDATION")
        print("=" * 45)

        # --------------------------------
        # 1. RECORD COUNT VALIDATION
        # --------------------------------

        expected_counts = {
            "zones": (AddressZone, 10),
            "buses": (Bus, 100),
            "drivers": (Driver, 100),
            "stops": (Stop, 300),
            "routes": (Route, 100),
            "route_runs": (RouteRun, 100),
            "students": (Student, 5000),
            "guardians": (GuardianContact, 5000),
            "assignments": (Assignment, 5000),
            "attendance": (AttendanceEvent, 5000)
        }

        print("\n1. RECORD COUNTS")
        print("-" * 45)

        for name, (model, expected) in expected_counts.items():

            actual = db.query(func.count("*")).select_from(
                model
            ).scalar()

            print(f"{name}: {actual} / {expected}")

            if actual != expected:
                errors.append(
                    f"{name}: expected {expected}, found {actual}"
                )

        # --------------------------------
        # 2. GENERATION RUN VALIDATION
        # --------------------------------

        print("\n2. GENERATION RUN")

        generation = db.query(GenerationRun).order_by(
            GenerationRun.generation_run_id.desc()
        ).first()

        if not generation:
            errors.append("No generation run found")

        elif generation.status != "COMPLETED":
            errors.append("Latest generation run is not completed")

        else:
            print("Latest generation run:", generation.generation_run_id)
            print("Seed:", generation.seed)
            print("Status:", generation.status)

            if generation.seed != 20261022:
                errors.append("Unexpected generation seed")

        # --------------------------------
        # 3. DUPLICATE ASSIGNMENTS
        # --------------------------------

        print("\n3. DUPLICATE ACTIVE ASSIGNMENTS")

        duplicates = (
            db.query(
                Assignment.student_id,
                func.count(Assignment.assignment_id)
            )
            .filter(Assignment.assignment_status == "ACTIVE")
            .group_by(Assignment.student_id)
            .having(func.count(Assignment.assignment_id) > 1)
            .all()
        )

        print("Duplicate students:", len(duplicates))

        if duplicates:
            errors.append("Students have multiple active assignments")

        # --------------------------------
        # 4. BUS CAPACITY VALIDATION
        # --------------------------------

        print("\n4. BUS CAPACITY VALIDATION")

        capacity_violations = (
            db.query(
                RouteRun.run_id,
                func.count(Assignment.assignment_id),
                Bus.capacity
            )
            .join(Bus, RouteRun.bus_id == Bus.bus_id)
            .outerjoin(
                Assignment,
                Assignment.run_id == RouteRun.run_id
            )
            .group_by(RouteRun.run_id, Bus.capacity)
            .having(
                func.count(Assignment.assignment_id) > Bus.capacity
            )
            .all()
        )

        print("Capacity violations:", len(capacity_violations))

        if capacity_violations:
            errors.append("One or more route runs exceed bus capacity")

        # --------------------------------
        # 5. ACCESSIBILITY VALIDATION
        # --------------------------------

        print("\n5. ACCESSIBILITY VALIDATION")

        accessibility_violations = (
            db.query(func.count(Assignment.assignment_id))
            .join(
                Student,
                Assignment.student_id == Student.student_id
            )
            .join(
                RouteRun,
                Assignment.run_id == RouteRun.run_id
            )
            .join(
                Bus,
                RouteRun.bus_id == Bus.bus_id
            )
            .filter(
                Student.requires_accessibility.is_(True),
                Bus.accessible.is_(False)
            )
            .scalar()
        )

        print(
            "Accessibility violations:",
            accessibility_violations
        )

        if accessibility_violations:
            errors.append(
                "Accessibility-required students assigned to "
                "non-accessible buses"
            )

        # --------------------------------
        # 6. STOP-ROUTE VALIDATION
        # --------------------------------

        print("\n6. STOP-ROUTE VALIDATION")

        valid_stop_exists = (
            db.query(RouteStop.route_stop_id)
            .filter(
                RouteStop.route_id == Assignment.route_id,
                RouteStop.stop_id == Assignment.stop_id
            )
            .exists()
        )

        invalid_stop_assignments = (
            db.query(func.count(Assignment.assignment_id))
            .filter(~valid_stop_exists)
            .scalar()
        )

        print(
            "Invalid route-stop assignments:",
            invalid_stop_assignments
        )

        if invalid_stop_assignments:
            errors.append(
                "Assignments contain stops not belonging to their routes"
            )

        # --------------------------------
        # 7. STOP APPROVAL VALIDATION
        # --------------------------------

        print("\n7. STOP APPROVAL VALIDATION")

        invalid_stops = (
            db.query(func.count(Assignment.assignment_id))
            .join(Stop, Assignment.stop_id == Stop.stop_id)
            .filter(
                Stop.is_approved.is_(False)
            )
            .scalar()
        )

        print("Assignments using unapproved stops:", invalid_stops)

        if invalid_stops:
            errors.append(
                "Assignments use unapproved stops"
            )

        # --------------------------------
        # 8. STUDENT ZONE VALIDATION
        # --------------------------------

        print("\n8. STUDENT ZONE VALIDATION")

        zone_mismatches = (
            db.query(func.count(Assignment.assignment_id))
            .join(
                Student,
                Assignment.student_id == Student.student_id
            )
            .join(
                Stop,
                Assignment.stop_id == Stop.stop_id
            )
            .filter(Student.zone_id != Stop.zone_id)
            .scalar()
        )

        print("Zone mismatches:", zone_mismatches)

        if zone_mismatches:
            warnings.append(
                "Some students are assigned to stops outside their zone"
            )

        # --------------------------------
        # 9. PICKUP WINDOW VALIDATION
        # --------------------------------

        print("\n9. PICKUP WINDOW VALIDATION")

        pickup_violations = (
            db.query(func.count(Assignment.assignment_id))
            .join(
                Student,
                Assignment.student_id == Student.student_id
            )
            .join(
                RouteStop,
                (Assignment.route_id == RouteStop.route_id)
                & (Assignment.stop_id == RouteStop.stop_id)
            )
            .filter(
                (RouteStop.estimated_arrival < Student.pickup_start)
                | (RouteStop.estimated_arrival > Student.pickup_end)
            )
            .scalar()
        )

        print("Pickup window violations:", pickup_violations)

        if pickup_violations:
            errors.append(
                "Some students have pickup times outside their windows"
            )

        # --------------------------------
        # 10. ROUTE RUN CONSISTENCY
        # --------------------------------

        print("\n10. ROUTE RUN CONSISTENCY")

        run_mismatches = (
            db.query(func.count(RouteRun.run_id))
            .join(Route, RouteRun.route_id == Route.route_id)
            .filter(
                (RouteRun.bus_id != Route.bus_id)
                | (RouteRun.driver_id != Route.driver_id)
            )
            .scalar()
        )

        print("Route run mismatches:", run_mismatches)

        if run_mismatches:
            errors.append(
                "Route run bus or driver does not match its route"
            )

        # --------------------------------
        # 11. ATTENDANCE CONSISTENCY
        # --------------------------------

        print("\n11. ATTENDANCE CONSISTENCY")

        attendance_mismatches = (
            db.query(func.count(AttendanceEvent.attendance_id))
            .join(
                Assignment,
                AttendanceEvent.assignment_id == Assignment.assignment_id
            )
            .filter(
                AttendanceEvent.student_id != Assignment.student_id
            )
            .scalar()
        )

        print("Attendance mismatches:", attendance_mismatches)

        if attendance_mismatches:
            errors.append(
                "Attendance student does not match assignment student"
            )

        # --------------------------------
        # 12. FINAL RESULT
        # --------------------------------

        print("\n" + "=" * 45)
        print("VALIDATION SUMMARY")
        print("=" * 45)

        print("Total errors:", len(errors))
        print("Total warnings:", len(warnings))

        if errors:
            print("\nFAILED CHECKS:")

            for error in errors:
                print("ERROR:", error)

        if warnings:
            print("\nWARNINGS:")

            for warning in warnings:
                print("WARNING:", warning)

        if not errors:
            print("\nDATASET VALIDATION PASSED")

        else:
            print("\nDATASET VALIDATION FAILED")

        return {
            "status": "PASSED" if not errors else "FAILED",
            "errors": errors,
            "warnings": warnings
        }

    finally:
        db.close()


if __name__ == "__main__":
    validate_dataset()
