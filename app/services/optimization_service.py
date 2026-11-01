from datetime import date, datetime, time

from sqlalchemy import func, or_

from app.models import (
    Student,
    Assignment,
    Route,
    RouteRun,
    RouteStop,
    Stop,
    Bus,
    Driver,
)


class OptimizationServiceError(Exception):
    """Raised when assignment optimization cannot be completed."""
    pass


def _is_unavailable(status):
    """
    Identify records that should not be considered for optimization.
    """
    if status is None:
        return False

    return str(status).lower() in {
        "inactive",
        "cancelled",
        "canceled",
        "completed",
        "not working",
        "rejected",
    }


def _time_to_minutes(value):
    """Convert a Python time object into minutes after midnight."""
    return value.hour * 60 + value.minute


def _calculate_pickup_score(pickup_start, pickup_end, estimated_arrival):
    """
    Score how suitable a stop's estimated arrival time is
    for the student's preferred pickup window.

    Within the window: 100 points.
    Outside the window: score decreases with the time difference.
    """

    if not pickup_start or not pickup_end or not estimated_arrival:
        return 50.0

    start = _time_to_minutes(pickup_start)
    end = _time_to_minutes(pickup_end)
    arrival = _time_to_minutes(estimated_arrival)

    # Handle a pickup window that crosses midnight.
    if end < start:
        end += 24 * 60

    # Handle an arrival after midnight in a crossing-midnight window.
    if end >= 24 * 60 and arrival < start:
        arrival += 24 * 60

    if start <= arrival <= end:
        return 100.0

    if arrival < start:
        difference = start - arrival
    else:
        difference = arrival - end

    # Reduce 2 points for every minute outside the window.
    return max(0.0, 100.0 - (difference * 2))


def _calculate_zone_score(student_zone_id, stop_zone_id):
    """
    Zone compatibility score.

    This version uses exact zone matching because student
    coordinates are not available.
    """
    return 100.0 if student_zone_id == stop_zone_id else 0.0


def _calculate_capacity_score(current_load, bus_capacity):
    """
    Give a higher score to buses with more available capacity.
    """
    if bus_capacity <= 0:
        return 0.0

    utilization = current_load / bus_capacity

    return max(0.0, (1 - utilization) * 100)


def _calculate_total_score(zone_score, pickup_score, capacity_score):
    """
    Weighted optimization score:
    Zone compatibility      = 40%
    Pickup window suitability = 35%
    Capacity balance        = 25%
    """
    total = (
        (zone_score * 0.40)
        + (pickup_score * 0.35)
        + (capacity_score * 0.25)
    )

    return round(total, 2)


def optimize_student_assignment(db, student_id, top_n=5):
    """
    Find and rank suitable route-run-stop combinations for a student.

    This function only generates optimization proposals.
    It does NOT create, update, or delete assignments.
    """

    # --------------------------------------------------
    # 1. Get student
    # --------------------------------------------------

    student = db.query(Student).filter(
        Student.student_id == student_id
    ).first()

    if not student:
        raise OptimizationServiceError(
            f"Student '{student_id}' was not found."
        )

    if _is_unavailable(student.status):
        raise OptimizationServiceError(
            "This student is not currently available for assignment."
        )

    if not student.zone_id:
        raise OptimizationServiceError(
            "Student does not have an assigned zone."
        )

    # --------------------------------------------------
    # 2. Get future route-run candidates
    # --------------------------------------------------

    today = date.today()

    candidates = (
        db.query(
            RouteRun,
            Route,
            Bus,
            Driver,
            RouteStop,
            Stop,
        )
        .join(
            Route,
            RouteRun.route_id == Route.route_id,
        )
        .join(
            Bus,
            RouteRun.bus_id == Bus.bus_id,
        )
        .join(
            Driver,
            RouteRun.driver_id == Driver.driver_id,
        )
        .join(
            RouteStop,
            RouteStop.route_id == Route.route_id,
        )
        .join(
            Stop,
            RouteStop.stop_id == Stop.stop_id,
        )
        .filter(
            RouteRun.run_date >= today,

            # Ensure route-run vehicle and driver match the route.
            RouteRun.bus_id == Route.bus_id,
            RouteRun.driver_id == Route.driver_id,

            # Route must be effective on the run date.
            Route.effective_from <= RouteRun.run_date,
            or_(
                Route.effective_to.is_(None),
                Route.effective_to >= RouteRun.run_date,
            ),

            # Stop must be approved.
            Stop.is_approved.is_(True),

            # Student and stop must belong to the same zone.
            Stop.zone_id == student.zone_id,
        )
        .all()
    )

    # --------------------------------------------------
    # 3. Evaluate candidates
    # --------------------------------------------------

    proposals = []

    for (
        route_run,
        route,
        bus,
        driver,
        route_stop,
        stop,
    ) in candidates:

        # Check route, bus, driver, run and stop availability.
        if _is_unavailable(route.route_status):
            continue

        if _is_unavailable(bus.bus_status):
            continue

        if _is_unavailable(driver.driver_status):
            continue

        if _is_unavailable(route_run.run_status):
            continue

        if _is_unavailable(stop.stop_status):
            continue

        # Hard constraint: accessibility.
        if student.requires_accessibility and not bus.accessible:
            continue

        # Hard constraint: valid capacity.
        if not bus.capacity or bus.capacity <= 0:
            continue

        # --------------------------------------------------
        # 4. Calculate current bus/run load
        # --------------------------------------------------

        current_load = (
            db.query(func.count(Assignment.assignment_id))
            .filter(
                Assignment.run_id == route_run.run_id,
                Assignment.effective_to.is_(None),
                Assignment.assignment_status == "active",
                Assignment.student_id != student.student_id,
            )
            .scalar()
        ) or 0

        # Hard constraint: bus must have space for this student.
        if current_load >= bus.capacity:
            continue

        # --------------------------------------------------
        # 5. Calculate optimization scores
        # --------------------------------------------------

        zone_score = _calculate_zone_score(
            student.zone_id,
            stop.zone_id,
        )

        pickup_score = _calculate_pickup_score(
            student.pickup_start,
            student.pickup_end,
            route_stop.estimated_arrival,
        )

        capacity_score = _calculate_capacity_score(
            current_load + 1,
            bus.capacity,
        )

        total_score = _calculate_total_score(
            zone_score,
            pickup_score,
            capacity_score,
        )

        # --------------------------------------------------
        # 6. Add proposal
        # --------------------------------------------------

        proposals.append({
            "student_id": student.student_id,

            "run_id": route_run.run_id,
            "run_date": route_run.run_date.isoformat(),

            "route_id": route.route_id,
            "route_name": route.route_name,

            "bus_id": bus.bus_id,
            "bus_capacity": bus.capacity,
            "bus_accessible": bus.accessible,

            "driver_id": driver.driver_id,
            "driver_name": driver.driver_name,

            "stop_id": stop.stop_id,
            "stop_name": stop.stop_name,
            "estimated_arrival": (
                route_stop.estimated_arrival.strftime("%H:%M:%S")
                if route_stop.estimated_arrival
                else None
            ),

            "current_load": current_load,
            "remaining_capacity": bus.capacity - current_load - 1,

            "scores": {
                "zone_compatibility": round(zone_score, 2),
                "pickup_window": round(pickup_score, 2),
                "capacity_balance": round(capacity_score, 2),
            },

            "total_score": total_score,
        })

    # --------------------------------------------------
    # 7. Rank proposals
    # --------------------------------------------------

    proposals.sort(
        key=lambda item: item["total_score"],
        reverse=True,
    )

    # Return only the requested number of proposals.
    return {
        "student_id": student.student_id,
        "total_candidates": len(proposals),
        "optimization_weights": {
            "zone_compatibility": 40,
            "pickup_window": 35,
            "capacity_balance": 25,
        },
        "proposals": proposals[:top_n],
    }