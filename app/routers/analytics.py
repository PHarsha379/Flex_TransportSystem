from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy import func, or_
from app.schemas.analytics import (
    AnalyticsOverview,
    StudentAnalytics,
    BusAnalytics,
    RouteAnalytics,
    AttendanceAnalytics,
    ZoneAnalytics,
)
from app.database import get_db
from app.models import (
    Student,
    Bus,
    Route,
    RouteRun,
    Assignment,
    AttendanceEvent,
    AddressZone,
)

router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"]
)


# --------------------------------------------------
# 1. OVERALL DASHBOARD STATISTICS
# --------------------------------------------------

@router.get("/overview",response_model=AnalyticsOverview)
def get_overview(db: Session = Depends(get_db)):

    total_students = db.query(func.count(Student.student_id)).scalar() or 0
    total_buses = db.query(func.count(Bus.bus_id)).scalar() or 0
    total_routes = db.query(func.count(Route.route_id)).scalar() or 0
    total_assignments = db.query(func.count(Assignment.assignment_id)).scalar() or 0
    total_route_runs = db.query(func.count(RouteRun.run_id)).scalar() or 0
    total_attendance = db.query(
        func.count(AttendanceEvent.attendance_id)
    ).scalar() or 0

    active_students = db.query(
        func.count(Student.student_id)
    ).filter(
        func.lower(Student.status) == "active"
    ).scalar() or 0

    active_buses = db.query(
        func.count(Bus.bus_id)
    ).filter(
        func.lower(Bus.bus_status) == "active"
    ).scalar() or 0

    active_routes = db.query(
        func.count(Route.route_id)
    ).filter(
        func.lower(Route.route_status) == "active"
    ).scalar() or 0

    return {
        "total_students": total_students,
        "active_students": active_students,
        "total_buses": total_buses,
        "active_buses": active_buses,
        "total_routes": total_routes,
        "active_routes": active_routes,
        "total_route_runs": total_route_runs,
        "total_assignments": total_assignments,
        "total_attendance_records": total_attendance,
    }


# --------------------------------------------------
# 2. STUDENT STATISTICS
# --------------------------------------------------

@router.get("/students", response_model=StudentAnalytics)
def get_student_analytics(db: Session = Depends(get_db)):

    total_students = db.query(
        func.count(Student.student_id)
    ).scalar() or 0

    active_students = db.query(
        func.count(Student.student_id)
    ).filter(
        func.lower(Student.status) == "active"
    ).scalar() or 0

    inactive_students = db.query(
    func.count(Student.student_id)
    ).filter(
    or_(
        func.lower(Student.status) != "active",
        Student.status.is_(None)
    )
    ).scalar() or 0

    accessibility_required = db.query(
        func.count(Student.student_id)
    ).filter(
        Student.requires_accessibility.is_(True)
    ).scalar() or 0

    return {
        "total_students": total_students,
        "active_students": active_students,
        "inactive_students": inactive_students,
        "students_requiring_accessibility": accessibility_required,
    }


# --------------------------------------------------
# 3. BUS CAPACITY AND UTILIZATION
# --------------------------------------------------

@router.get("/buses", response_model=BusAnalytics)
def get_bus_analytics(db: Session = Depends(get_db)):

    total_buses = db.query(
        func.count(Bus.bus_id)
    ).scalar() or 0

    total_capacity = db.query(
        func.coalesce(func.sum(Bus.capacity), 0)
    ).scalar() or 0

    accessible_buses = db.query(
        func.count(Bus.bus_id)
    ).filter(
        Bus.accessible.is_(True)
    ).scalar() or 0

    # Count current assignments for each bus through its route runs.
    bus_loads = (
        db.query(
            RouteRun.bus_id,
            func.count(Assignment.assignment_id).label("assigned_students")
        )
        .join(
            Assignment,
            Assignment.run_id == RouteRun.run_id
        )
        .filter(
            Assignment.effective_to.is_(None),
            func.lower(Assignment.assignment_status) == "active"
        )
        .group_by(RouteRun.bus_id)
        .all()
    )

    load_map = {
        row.bus_id: row.assigned_students
        for row in bus_loads
    }

    buses = db.query(Bus).all()

    bus_details = []

    for bus in buses:

        assigned = load_map.get(bus.bus_id, 0)

        remaining = max(bus.capacity - assigned, 0)

        utilization = (
            round((assigned / bus.capacity) * 100, 2)
            if bus.capacity and bus.capacity > 0
            else 0
        )

        bus_details.append({
            "bus_id": bus.bus_id,
            "registration_number": bus.registration_number,
            "capacity": bus.capacity,
            "assigned_students": assigned,
            "available_capacity": remaining,
            "utilization_percentage": utilization,
            "accessible": bus.accessible,
            "status": bus.bus_status,
        })

    return {
        "total_buses": total_buses,
        "total_seat_capacity": total_capacity,
        "accessible_buses": accessible_buses,
        "bus_details": bus_details,
    }


# --------------------------------------------------
# 4. ROUTE STATISTICS
# --------------------------------------------------

@router.get("/routes", response_model=RouteAnalytics)
def get_route_analytics(db: Session = Depends(get_db)):

    total_routes = db.query(
        func.count(Route.route_id)
    ).scalar() or 0

    active_routes = db.query(
        func.count(Route.route_id)
    ).filter(
        func.lower(Route.route_status) == "active"
    ).scalar() or 0

    total_route_runs = db.query(
        func.count(RouteRun.run_id)
    ).scalar() or 0

    route_details = (
        db.query(
            Route.route_id,
            Route.route_name,
            Route.route_status,
            func.count(RouteRun.run_id).label("total_runs")
        )
        .outerjoin(
            RouteRun,
            RouteRun.route_id == Route.route_id
        )
        .group_by(
            Route.route_id,
            Route.route_name,
            Route.route_status
        )
        .all()
    )

    return {
        "total_routes": total_routes,
        "active_routes": active_routes,
        "total_route_runs": total_route_runs,
        "route_details": [
            {
                "route_id": row.route_id,
                "route_name": row.route_name,
                "status": row.route_status,
                "total_runs": row.total_runs,
            }
            for row in route_details
        ],
    }


# --------------------------------------------------
# 5. ATTENDANCE ANALYTICS
# --------------------------------------------------

@router.get("/attendance", response_model=AttendanceAnalytics)
def get_attendance_analytics(db: Session = Depends(get_db)):

    total_records = db.query(
        func.count(AttendanceEvent.attendance_id)
    ).scalar() or 0

    attendance_by_status = (
        db.query(
            AttendanceEvent.pickup_status,
            func.count(AttendanceEvent.attendance_id).label("total")
        )
        .group_by(AttendanceEvent.pickup_status)
        .all()
    )

    status_summary = {
        str(row.pickup_status): row.total
        for row in attendance_by_status
    }

    return {
        "total_attendance_records": total_records,
        "attendance_by_status": status_summary,
    }


# --------------------------------------------------
# 6. ZONE-WISE STUDENT DISTRIBUTION
# --------------------------------------------------

@router.get("/zones", response_model=ZoneAnalytics)
def get_zone_analytics(db: Session = Depends(get_db)):

    zone_details = (
        db.query(
            AddressZone.zone_id,
            AddressZone.zone_name,
            func.count(Student.student_id).label("total_students")
        )
        .outerjoin(
            Student,
            Student.zone_id == AddressZone.zone_id
        )
        .group_by(
            AddressZone.zone_id,
            AddressZone.zone_name
        )
        .all()
    )

    return {
        "total_zones": len(zone_details),
        "zone_wise_students": [
            {
                "zone_id": row.zone_id,
                "zone_name": row.zone_name,
                "total_students": row.total_students,
            }
            for row in zone_details
        ],
    }