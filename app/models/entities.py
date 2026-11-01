from datetime import datetime, date, time

from sqlalchemy import (
    Column,
    String,
    Integer,
    Date,
    DateTime,
    Time,
    Boolean,
    ForeignKey,
    Text,
    Numeric,
    UniqueConstraint
)

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class AddressZone(Base):
    __tablename__ = "address_zones"
    zone_id: Mapped[int] = mapped_column(primary_key=True)
    zone_name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    latitude: Mapped[float] = mapped_column(Numeric(10, 7), nullable=False)
    longitude: Mapped[float] = mapped_column(Numeric(10, 7), nullable=False)
    zone_status: Mapped[str] = mapped_column(String(20), default="ACTIVE")


class Student(Base):
    __tablename__ = "students"
    student_id: Mapped[str] = mapped_column(String(15), primary_key=True)
    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    grade: Mapped[str] = mapped_column(String(10), nullable=False)
    synthetic_address: Mapped[str] = mapped_column(String(255), nullable=False)
    zone_id: Mapped[int] = mapped_column(ForeignKey("address_zones.zone_id"), nullable=False)
    requires_accessibility: Mapped[bool] = mapped_column(Boolean, default=False)
    pickup_start: Mapped[time] = mapped_column(Time, nullable=False)
    pickup_end: Mapped[time] = mapped_column(Time, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    zone = relationship("AddressZone")


class GuardianContact(Base):
    __tablename__ = "guardian_contacts"
    guardian_id: Mapped[str] = mapped_column(String(15), primary_key=True)
    student_id: Mapped[str] = mapped_column(ForeignKey("students.student_id"), nullable=False)
    guardian_name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=False)
    email: Mapped[str] = mapped_column(String(100), nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=True)
    is_valid: Mapped[bool] = mapped_column(Boolean, default=True)
    contact_status: Mapped[str] = mapped_column(String(20), default="ACTIVE")


class Stop(Base):
    __tablename__ = "stops"
    stop_id: Mapped[str] = mapped_column(String(15), primary_key=True)
    stop_name: Mapped[str] = mapped_column(String(100), nullable=False)
    zone_id: Mapped[int] = mapped_column(ForeignKey("address_zones.zone_id"), nullable=False)
    latitude: Mapped[float] = mapped_column(Numeric(10, 7), nullable=False)
    longitude: Mapped[float] = mapped_column(Numeric(10, 7), nullable=False)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    approval_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    stop_status: Mapped[str] = mapped_column(String(20), default="ACTIVE")


class Bus(Base):
    __tablename__ = "buses"
    bus_id: Mapped[str] = mapped_column(String(15), primary_key=True)
    registration_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    accessible: Mapped[bool] = mapped_column(Boolean, default=False)
    bus_status: Mapped[str] = mapped_column(String(20), default="ACTIVE")


class Driver(Base):
    __tablename__ = "drivers"
    driver_id: Mapped[str] = mapped_column(String(15), primary_key=True)
    driver_name: Mapped[str] = mapped_column(String(100), nullable=False)
    license_number: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=False)
    driver_status: Mapped[str] = mapped_column(String(20), default="ACTIVE")


class Route(Base):
    __tablename__ = "routes"
    route_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    route_name: Mapped[str] = mapped_column(String(100), nullable=False)
    bus_id: Mapped[str] = mapped_column(ForeignKey("buses.bus_id"), nullable=False)
    driver_id: Mapped[str] = mapped_column(ForeignKey("drivers.driver_id"), nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    route_status: Mapped[str] = mapped_column(String(20), default="DRAFT")
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[date | None] = mapped_column(Date, nullable=True)


class RouteStop(Base):
    __tablename__ = "route_stops"
    __table_args__ = (UniqueConstraint("route_id", "stop_sequence"),)
    route_stop_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    route_id: Mapped[str] = mapped_column(ForeignKey("routes.route_id"), nullable=False)
    stop_id: Mapped[str] = mapped_column(ForeignKey("stops.stop_id"), nullable=False)
    stop_sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    estimated_arrival: Mapped[time] = mapped_column(Time, nullable=False)
    travel_time_from_previous: Mapped[int] = mapped_column(Integer, default=0)


class RouteRun(Base):
    __tablename__ = "route_runs"
    run_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    route_id: Mapped[str] = mapped_column(ForeignKey("routes.route_id"), nullable=False)
    bus_id: Mapped[str] = mapped_column(ForeignKey("buses.bus_id"), nullable=False)
    driver_id: Mapped[str] = mapped_column(ForeignKey("drivers.driver_id"), nullable=False)
    run_date: Mapped[date] = mapped_column(Date, nullable=False)
    trip_number: Mapped[int] = mapped_column(Integer, nullable=False)
    departure_time: Mapped[time] = mapped_column(Time, nullable=False)
    arrival_time: Mapped[time] = mapped_column(Time, nullable=False)
    run_status: Mapped[str] = mapped_column(String(20), default="SCHEDULED")


class Assignment(Base):
    __tablename__ = "assignments"
    assignment_id: Mapped[str] = mapped_column(String(40), primary_key=True)
    student_id: Mapped[str] = mapped_column(ForeignKey("students.student_id"), nullable=False)
    route_id: Mapped[str] = mapped_column(ForeignKey("routes.route_id"), nullable=False)
    stop_id: Mapped[str] = mapped_column(ForeignKey("stops.stop_id"), nullable=False)
    run_id: Mapped[int | None] = mapped_column(ForeignKey("route_runs.run_id"), nullable=True)
    assigned_date: Mapped[date] = mapped_column(Date, nullable=False)
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    assignment_status: Mapped[str] = mapped_column(String(20), default="ACTIVE")
    assignment_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)


class AttendanceEvent(Base):
    __tablename__ = "attendance_events"
    __table_args__ = (UniqueConstraint("student_id", "attendance_date", "assignment_id"),)
    attendance_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    student_id: Mapped[str] = mapped_column(ForeignKey("students.student_id"), nullable=False)
    assignment_id: Mapped[str] = mapped_column(ForeignKey("assignments.assignment_id"), nullable=False)
    attendance_date: Mapped[date] = mapped_column(Date, nullable=False)
    pickup_status: Mapped[str] = mapped_column(String(30), nullable=False)
    pickup_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    event_type: Mapped[str] = mapped_column(String(30), nullable=False)
    issue_type: Mapped[str | None] = mapped_column(String(60), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Notification(Base):
    __tablename__ = "notifications"
    notification_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    guardian_id: Mapped[str] = mapped_column(ForeignKey("guardian_contacts.guardian_id"), nullable=False)
    student_id: Mapped[str] = mapped_column(ForeignKey("students.student_id"), nullable=False)
    attendance_id: Mapped[int | None] = mapped_column(ForeignKey("attendance_events.attendance_id"), nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    notification_type: Mapped[str] = mapped_column(String(40), nullable=False)
    delivery_status: Mapped[str] = mapped_column(String(30), nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    issue_type: Mapped[str | None] = mapped_column(String(60), nullable=True)


class BusCapacityHistory(Base):
    __tablename__ = "bus_capacity_history"
    history_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    bus_id: Mapped[str] = mapped_column(ForeignKey("buses.bus_id"), nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[date | None] = mapped_column(Date, nullable=True)





class AssignmentHistory(Base):
    __tablename__ = "assignment_history"

    history_id = Column(Integer, primary_key=True, autoincrement=True)

    assignment_id = Column(String(30), nullable=False)

    old_route_id = Column(String(30), nullable=True)
    new_route_id = Column(String(30), nullable=True)

    old_stop_id = Column(String(30), nullable=True)
    new_stop_id = Column(String(30), nullable=True)

    old_status = Column(String(30), nullable=True)
    new_status = Column(String(30), nullable=True)

    changed_by = Column(String(100), nullable=True)
    change_reason = Column(String(255), nullable=True)

    changed_at = Column(
        DateTime,
        default=datetime.utcnow
    )







class RouteDisruption(Base):
    __tablename__ = "route_disruptions"

    disruption_id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    route_id = Column(
        String(20),
        ForeignKey("routes.route_id"),
        nullable=False
    )

    run_id = Column(
        Integer,
        ForeignKey("route_runs.run_id"),
        nullable=True
    )

    disruption_type = Column(String(50), nullable=False)
    description = Column(String(255), nullable=False)
    reported_at = Column(DateTime, default=datetime.utcnow)
    expected_delay_minutes = Column(Integer, default=0)
    disruption_status = Column(String(30), default="OPEN")
    resolved_at = Column(DateTime, nullable=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    audit_id = Column(Integer, primary_key=True, autoincrement=True)
    actor_id = Column(String(30), nullable=False)
    action = Column(String(50), nullable=False)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(String(50), nullable=False)
    old_values = Column(Text, nullable=True)
    new_values = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class GenerationRun(Base):
    __tablename__ = "generation_runs"

    generation_run_id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )
    seed: Mapped[int] = mapped_column(Integer, nullable=False)
    generator_version: Mapped[str] = mapped_column(
        String(20), nullable=False
    )
    parameters_json: Mapped[str] = mapped_column(Text, nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default="STARTED"
    )