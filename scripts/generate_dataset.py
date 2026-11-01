import random
from datetime import date, datetime, time, timedelta

from faker import Faker
from sqlalchemy import func

from app.database import SessionLocal, engine, Base
from app import models

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
    AttendanceEvent
)


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

SEED = 20261022
TOTAL_STUDENTS = 5000
TOTAL_BUSES = 100
TOTAL_STOPS = 300
TOTAL_DRIVERS = 100
TOTAL_ZONES = 10

SCHOOL_DATE = date(2026, 11, 2)

random.seed(SEED)

fake = Faker("en_IN")
Faker.seed(SEED)


# --------------------------------------------------
# DATABASE SESSION
# --------------------------------------------------

db = SessionLocal()


def check_empty_database():

    models = [
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
        AttendanceEvent
    ]

    for model in models:

        count = db.query(func.count("*")).select_from(model).scalar()

        if count:
            raise Exception(
                f"{model.__tablename__} is not empty. "
                "Use a clean synthetic database."
            )


# --------------------------------------------------
# 1. GENERATE ADDRESS ZONES
# --------------------------------------------------

def generate_zones():

    zones = []

    for i in range(1, TOTAL_ZONES + 1):

        zone = AddressZone(
            zone_name=f"ZONE-{i:03d}",
            latitude=16.50 + random.uniform(-0.05, 0.05),
            longitude=80.64 + random.uniform(-0.05, 0.05),
            zone_status="ACTIVE"
        )

        zones.append(zone)

    db.add_all(zones)
    db.flush()

    return zones


# --------------------------------------------------
# 2. GENERATE BUSES
# --------------------------------------------------

def generate_buses():

    buses = []

    for i in range(1, TOTAL_BUSES + 1):

        bus = Bus(
            bus_id=f"BUS-{i:06d}",
            registration_number=f"AP16AB{i:04d}",
            capacity=50,
            accessible=(i <= 20),
            bus_status="ACTIVE"
        )

        buses.append(bus)

    db.add_all(buses)

    return buses


# --------------------------------------------------
# 3. GENERATE DRIVERS
# --------------------------------------------------

def generate_drivers():

    drivers = []

    for i in range(1, TOTAL_DRIVERS + 1):

        driver = Driver(
            driver_id=f"DRV-{i:06d}",
            driver_name=fake.name(),
            license_number=f"DL2026{i:06d}",
            phone_number=f"9{random.randint(100000000, 999999999)}",
            driver_status="ACTIVE"
        )

        drivers.append(driver)

    db.add_all(drivers)

    return drivers


# --------------------------------------------------
# 4. GENERATE STOPS
# --------------------------------------------------

def generate_stops(zones):

    stops = []

    for i in range(1, TOTAL_STOPS + 1):

        zone_index = (i - 1) // 30

        stop = Stop(
            stop_id=f"STOP-{i:06d}",
            stop_name=f"Transport Stop {i:03d}",
            zone_id=zones[zone_index].zone_id,
            latitude=16.50 + random.uniform(-0.05, 0.05),
            longitude=80.64 + random.uniform(-0.05, 0.05),
            is_approved=True,
            approval_date=SCHOOL_DATE - timedelta(days=10),
            stop_status="ACTIVE"
        )

        stops.append(stop)

    db.add_all(stops)

    return stops


# --------------------------------------------------
# 5. GENERATE ROUTES AND ROUTE STOPS
# --------------------------------------------------

def generate_routes(buses, drivers, stops, zones):

    routes = []

    for i in range(TOTAL_BUSES):

        zone_index = i // 10
        local_route_index = i % 10

        route_id = f"ROUTE-2026-{i + 1:06d}"

        route = Route(
            route_id=route_id,
            route_name=f"Zone {zone_index + 1} Route {local_route_index + 1}",
            bus_id=buses[i].bus_id,
            driver_id=drivers[i].driver_id,
            start_time=time(6, 55),
            end_time=time(8, 0),
            route_status="ACTIVE",
            effective_from=SCHOOL_DATE,
            effective_to=None
        )

        db.add(route)
        db.flush()

        routes.append(route)

        # Each route has three stops.
        first_stop_index = zone_index * 30 + local_route_index * 3

        arrival_times = [
            time(7, 0),
            time(7, 20),
            time(7, 40)
        ]

        for j in range(3):

            route_stop = RouteStop(
                route_id=route_id,
                stop_id=stops[first_stop_index + j].stop_id,
                stop_sequence=j + 1,
                estimated_arrival=arrival_times[j],
                travel_time_from_previous=0 if j == 0 else 20
            )

            db.add(route_stop)

    return routes


# --------------------------------------------------
# 6. GENERATE ROUTE RUNS
# --------------------------------------------------

def generate_route_runs(routes, buses, drivers):

    runs = []

    for i, route in enumerate(routes):

        run = RouteRun(
            run_id=f"RUN-2026-{i + 1:06d}",
            route_id=route.route_id,
            bus_id=buses[i].bus_id,
            driver_id=drivers[i].driver_id,
            run_date=SCHOOL_DATE,
            trip_number=1,
            departure_time=time(6, 55),
            arrival_time=time(8, 0),
            run_status="SCHEDULED"
        )

        runs.append(run)

    db.add_all(runs)

    return runs


# --------------------------------------------------
# 7. GENERATE STUDENTS, GUARDIANS AND ASSIGNMENTS
# --------------------------------------------------

def generate_students_and_assignments(
    zones,
    stops,
    routes,
    runs
):

    students = []
    guardians = []
    assignments = []
    attendance_records = []

    student_counter = 1

    for route_index, route in enumerate(routes):

        zone_index = route_index // 10
        local_route_index = route_index % 10

        first_stop_index = zone_index * 30 + local_route_index * 3

        for student_number in range(50):

            student_id = f"STU-{student_counter:06d}"

            stop_number = student_number % 3

            stop = stops[first_stop_index + stop_number]

            arrival_times = [
                time(7, 0),
                time(7, 20),
                time(7, 40)
            ]

            scheduled_pickup = arrival_times[stop_number]

            # Accessibility-required students are assigned
            # only to routes with accessible buses.
            requires_accessibility = (
                route_index < 20
                and random.random() < 0.10
            )

            student = Student(
                student_id=student_id,
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                grade=random.randint(1, 12),
                synthetic_address=fake.street_address(),
                zone_id=zones[zone_index].zone_id,
                requires_accessibility=requires_accessibility,
                pickup_start=(
                    datetime.combine(SCHOOL_DATE, scheduled_pickup)
                    - timedelta(minutes=5)
                ).time(),
                pickup_end=(
                    datetime.combine(SCHOOL_DATE, scheduled_pickup)
                    + timedelta(minutes=5)
                ).time(),
                status="ACTIVE",
                created_at=datetime.utcnow()
            )

            students.append(student)

            guardian = GuardianContact(
                guardian_id=f"GDN-{student_counter:06d}",
                student_id=student_id,
                guardian_name=fake.name(),
                phone_number=(
                    f"9{random.randint(100000000, 999999999)}"
                ),
                email=fake.email(),
                is_primary=True,
                is_valid=True,
                contact_status="ACTIVE"
            )

            guardians.append(guardian)

            assignment_id = (
                f"ASN-{student_id}-{SCHOOL_DATE.year}"
            )

            assignment = Assignment(
                assignment_id=assignment_id,
                student_id=student_id,
                route_id=route.route_id,
                stop_id=stop.stop_id,
                run_id=runs[route_index].run_id,
                assigned_date=SCHOOL_DATE,
                effective_from=SCHOOL_DATE,
                effective_to=None,
                assignment_status="ACTIVE",
                assignment_score=None
            )

            assignments.append(assignment)

            attendance = AttendanceEvent(
                student_id=student_id,
                assignment_id=assignment_id,
                attendance_date=SCHOOL_DATE,
                pickup_status="PICKED_UP",
                pickup_time=scheduled_pickup,
                event_type="PICKUP",
                issue_type=None,
                created_at=datetime.utcnow()
            )

            attendance_records.append(attendance)

            student_counter += 1

    db.add_all(students)
    db.add_all(guardians)
    db.add_all(assignments)
    db.add_all(attendance_records)


# --------------------------------------------------
# MAIN GENERATION FUNCTION
# --------------------------------------------------

def generate_dataset():

    try:

        check_empty_database()

        print("Starting synthetic dataset generation...")

        zones = generate_zones()
        db.flush()

        buses = generate_buses()
        drivers = generate_drivers()
        db.flush()

        stops = generate_stops(zones)
        db.flush()

        routes = generate_routes(
            buses,
            drivers,
            stops,
            zones
        )

        db.flush()

        runs = generate_route_runs(
            routes,
            buses,
            drivers
        )

        db.flush()

        generate_students_and_assignments(
            zones,
            stops,
            routes,
            runs
        )

        db.commit()

        print("Dataset generated successfully!")

        print("Zones:", len(zones))
        print("Students:", TOTAL_STUDENTS)
        print("Buses:", len(buses))
        print("Drivers:", len(drivers))
        print("Stops:", len(stops))
        print("Routes:", len(routes))
        print("Route runs:", len(runs))
        print("Assignments:", TOTAL_STUDENTS)
        print("Attendance:", TOTAL_STUDENTS)

    except Exception as error:

        db.rollback()

        print("Generation failed:", str(error))

        raise

    finally:

        db.close()


if __name__ == "__main__":
    generate_dataset()