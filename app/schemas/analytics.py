from pydantic import BaseModel
from typing import Dict, List, Optional


# --------------------------------------------------
# 1. OVERVIEW RESPONSE
# --------------------------------------------------

class AnalyticsOverview(BaseModel):
    total_students: int
    active_students: int
    total_buses: int
    active_buses: int
    total_routes: int
    active_routes: int
    total_route_runs: int
    total_assignments: int
    total_attendance_records: int


# --------------------------------------------------
# 2. STUDENT ANALYTICS
# --------------------------------------------------

class StudentAnalytics(BaseModel):
    total_students: int
    active_students: int
    inactive_students: int
    students_requiring_accessibility: int


# --------------------------------------------------
# 3. BUS ANALYTICS
# --------------------------------------------------

class BusDetail(BaseModel):
    bus_id: str
    registration_number: str
    capacity: int
    assigned_students: int
    available_capacity: int
    utilization_percentage: float
    accessible: bool
    status: Optional[str] = None


class BusAnalytics(BaseModel):
    total_buses: int
    total_seat_capacity: int
    accessible_buses: int
    bus_details: List[BusDetail]


# --------------------------------------------------
# 4. ROUTE ANALYTICS
# --------------------------------------------------

class RouteDetail(BaseModel):
    route_id: str
    route_name: str
    status: Optional[str] = None
    total_runs: int


class RouteAnalytics(BaseModel):
    total_routes: int
    active_routes: int
    total_route_runs: int
    route_details: List[RouteDetail]


# --------------------------------------------------
# 5. ATTENDANCE ANALYTICS
# --------------------------------------------------

class AttendanceAnalytics(BaseModel):
    total_attendance_records: int
    attendance_by_status: Dict[str, int]


# --------------------------------------------------
# 6. ZONE ANALYTICS
# --------------------------------------------------

class ZoneStudentDetail(BaseModel):
    zone_id: int
    zone_name: str
    total_students: int


class ZoneAnalytics(BaseModel):
    total_zones: int
    zone_wise_students: List[ZoneStudentDetail]