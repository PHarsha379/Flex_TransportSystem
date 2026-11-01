
import json
import random
from datetime import date, datetime, time, timedelta

from faker import Faker

from app.database import Base, engine, SessionLocal
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


fake = Faker("en_IN")

SEED = 20261022
SCHOOL_DATE = date(2026, 11, 2)
GENERATOR_VERSION = "1.0.0"


def generate_master_data(
    students=5000,
    buses=100,
    stops=300,
    zones=10,
    seed=SEED
):
    # -------------------------------
    # 1. VALIDATE GENERATOR PARAMETERS
    # -------------------------------

    if buses <= 0 or zones <= 0:
        raise ValueError("Buses and zones must be greater than zero")

    if students % buses != 0:
        raise ValueError("Students must be divisible by buses")

    if stops % buses != 0:
        raise ValueError("Stops must be divisible by buses")

    if buses % zones != 0:
        raise ValueError("Buses must be divisible by zones")

    random.seed(seed)
    fake.seed_instance(seed)

    students_per_route = students // buses
    stops_per_route = stops // buses
    routes_per_zone = buses // zones

    if stops_per_route < 2:
        raise ValueError("Each route must have at least two stops")

    db = SessionLocal()

    try:
        # -------------------------------
        # 2. CHECK DATABASE
        # -------------------------------

        Base.metadata.create_all(bind=engine)

        models_to_check = [
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
        ]

        for model in models_to_check:
            if db.query(model).first():
                raise RuntimeError(
                    f"{model.__tablename__} is not empty. "
                    "Use a separate empty synthetic database."
                )

        # -------------------------------
        # 3. CREATE GENERATION RUN
        # -------------------------------

        generation = GenerationRun(
            seed=seed,
            generator_version=GENERATOR_VERSION,
            parameters_json=json.dumps({
                "students": students,
                "buses": buses,
                "stops": stops,
                "zones": zones,
                "school_date": SCHOOL_DATE.isoformat()
            }),
            status="STARTED"
        )

        db.add(generation)
        db.flush()

        # -------------------------------
        # 4. CREATE ADDRESS ZONES
        # -------------------------------

        zones_data = []

        for i in range(1, zones + 1):
            zone = AddressZone(
                zone_id=i,
                zone_name=f"ZONE-{i:03d}",
                latitude=round(
                    16.5 + random.random() * 0.2, 7
                ),
                longitude=round(
                    80.5 + random.random() * 0.2, 7
                ),
                zone_status="ACTIVE"
            )

            zones_data.append(zone)

        db.add_all(zones_data)
        db.flush()

        # -------------------------------
        # 5. CREATE BUSES AND DRIVERS
        # -------------------------------

        buses_data = []
        drivers_data = []

        for i in range(1, buses + 1):

            # At least one-third of buses are accessible.
            bus = Bus(
                bus_id=f"BUS-{i:06d}",
                registration_number=f"SYN-{i:05d}",
                capacity=random.choice([50, 55, 60]),
                accessible=(i % 3 == 0),
                bus_status="ACTIVE"
            )

            driver = Driver(
                driver_id=f"DRV-{i:06d}",
                driver_name=fake.name(),
                license_number=f"SYN-LIC-{i:06d}",
                phone_number=f"+919000{i:06d}",
                driver_status="ACTIVE"
            )

            buses_data.append(bus)
            drivers_data.append(driver)

        db.add_all(buses_data)
        db.add_all(drivers_data)
        db.flush()

        # -------------------------------
        # 6. CREATE STOPS
        # -------------------------------

        stops_by_route = {}

        for route_number in range(1, buses + 1):

            zone_number = (
                (route_number - 1) // routes_per_zone
            ) + 1

            zone = zones_data[zone_number - 1]

            route_stops = []

            for j in range(1, stops_per_route + 1):

                stop_number = (
                    (route_number - 1) * stops_per_route
                ) + j

                stop = Stop(
                    stop_id=f"STOP-{stop_number:06d}",
                    stop_name=f"Pickup Stop {stop_number:03d}",
                    zone_id=zone.zone_id,
                    latitude=round(
                        float(zone.latitude)
                        + random.uniform(-0.01, 0.01), 7
                    ),
                    longitude=round(
                        float(zone.longitude)
                        + random.uniform(-0.01, 0.01), 7
                    ),
                    is_approved=True,
                    approval_date=date(2026, 1, 1),
                    stop_status="ACTIVE"
                )

                route_stops.append(stop)

            stops_by_route[route_number] = route_stops
            db.add_all(route_stops)

        db.flush()

        # -------------------------------
        # 7. CREATE ROUTES
        # -------------------------------

        routes_data = []

        for i in range(1, buses + 1):

            zone_number = ((i - 1) // routes_per_zone) + 1

            route = Route(
                route_id=f"ROUTE-2026-{i:06d}",
                route_name=f"School Route {i:03d}",
                bus_id=f"BUS-{i:06d}",
                driver_id=f"DRV-{i:06d}",
                start_time=time(7, 0),
                end_time=time(8, 30),
                route_status="ACTIVE",
                effective_from=SCHOOL_DATE
            )

            routes_data.append(route)

        db.add_all(routes_data)
        db.flush()

        # -------------------------------
        # 8. CREATE ROUTE STOPS
        # -------------------------------

        for i, route in enumerate(routes_data, start=1):

            route_stops = stops_by_route[i]

            for sequence, stop in enumerate(
                route_stops, start=1
            ):

                arrival_minutes = (sequence - 1) * 20

                arrival_time = (
                    datetime.combine(
                        SCHOOL_DATE, time(7, 0)
                    )
                    + timedelta(minutes=arrival_minutes)
                ).time()

                route_stop = RouteStop(
                    route_id=route.route_id,
                    stop_id=stop.stop_id,
                    stop_sequence=sequence,
                    estimated_arrival=arrival_time,
                    travel_time_from_previous=(
                        0 if sequence == 1 else 20
                    )
                )

                db.add(route_stop)

        db.flush()

        # -------------------------------
        # 9. CREATE ROUTE RUNS
        # -------------------------------

        runs_by_route = {}

        for route in routes_data:

            run = RouteRun(
                route_id=route.route_id,
                bus_id=route.bus_id,
                driver_id=route.driver_id,
                run_date=SCHOOL_DATE,
                trip_number=1,
                departure_time=route.start_time,
                arrival_time=route.end_time,
                run_status="SCHEDULED"
            )

            db.add(run)
            db.flush()

            # run_id is an auto-increment integer.
            runs_by_route[route.route_id] = run.run_id

        # -------------------------------
        # 10. CREATE STUDENTS
        # 11. CREATE GUARDIANS
        # 12. CREATE ASSIGNMENTS
        # 13. CREATE ATTENDANCE
        # -------------------------------

        students_data = []
        guardians_data = []
        assignments_data = []
        attendance_data = []

        student_number = 0

        for route_index, route in enumerate(
            routes_data, start=1
        ):

            bus = buses_data[route_index - 1]
            route_stops = stops_by_route[route_index]
            run_id = runs_by_route[route.route_id]

            for _ in range(students_per_route):

                student_number += 1

                student_id = f"STU-{student_number:06d}"

                # Accessibility-required students must
                # receive an accessible bus.
                requires_accessibility = (
                    bus.accessible and random.random() < 0.3
                )

                student = Student(
                    student_id=student_id,
                    first_name=fake.first_name(),
                    last_name=fake.last_name(),
                    grade=str(random.randint(1, 12)),
                    synthetic_address=fake.street_address(),
                    zone_id=(
                        (route_index - 1) // routes_per_zone
                    ) + 1,
                    requires_accessibility=requires_accessibility,
                    pickup_start=time(6, 30),
                    pickup_end=time(8, 0),
                    status="ACTIVE"
                )

                guardian = GuardianContact(
                    guardian_id=f"GDN-{student_number:06d}",
                    student_id=student_id,
                    guardian_name=fake.name(),
                    phone_number=f"+919100{student_number:06d}",
                    email=(
                        f"guardian{student_number:06d}"
                        "@example.test"
                    ),
                    is_primary=True,
                    is_valid=True,
                    contact_status="ACTIVE"
                )

                selected_stop = random.choice(route_stops)

                assignment_id = (
                    f"ASN-{student_id}-2026"
                )

                assignment = Assignment(
                    assignment_id=assignment_id,
                    student_id=student_id,
                    route_id=route.route_id,
                    stop_id=selected_stop.stop_id,
                    run_id=run_id,
                    assigned_date=SCHOOL_DATE,
                    effective_from=SCHOOL_DATE,
                    effective_to=None,
                    assignment_status="ACTIVE",
                    assignment_score=round(
                        random.uniform(80, 100), 2
                    )
                )

                # Find the scheduled arrival time of the
                # selected stop.
                stop_sequence = route_stops.index(
                    selected_stop
                )

                pickup_datetime = datetime.combine(
                    SCHOOL_DATE,
                    (
                        datetime.combine(
                            SCHOOL_DATE, time(7, 0)
                        )
                        + timedelta(minutes=stop_sequence * 20)
                    ).time()
                )

                attendance = AttendanceEvent(
                    student_id=student_id,
                    assignment_id=assignment_id,
                    attendance_date=SCHOOL_DATE,
                    pickup_status="PICKED_UP",
                    pickup_time=pickup_datetime,
                    event_type="PICKUP",
                    issue_type=None
                )

                students_data.append(student)
                guardians_data.append(guardian)
                assignments_data.append(assignment)
                attendance_data.append(attendance)

        # STEP 1: Insert students first
        db.add_all(students_data)
        db.flush()

        print("Students inserted:", len(students_data))


        # STEP 2: Insert guardian contacts
        db.add_all(guardians_data)
        db.flush()

        print("Guardians inserted:", len(guardians_data))


        # STEP 3: Insert assignments
        db.add_all(assignments_data)
        db.flush()

        print("Assignments inserted:", len(assignments_data))


        # STEP 4: Insert attendance events
        db.add_all(attendance_data)
        db.flush()

        print("Attendance inserted:", len(attendance_data))

        # -------------------------------
        # 14. COMPLETE GENERATION RUN
        # -------------------------------

        generation.status = "COMPLETED"

        db.commit()

        summary = {
            "generation_run_id": generation.generation_run_id,
            "seed": seed,
            "status": generation.status,
            "zones": len(zones_data),
            "buses": len(buses_data),
            "drivers": len(drivers_data),
            "stops": stops,
            "routes": len(routes_data),
            "route_runs": len(runs_by_route),
            "students": len(students_data),
            "guardians": len(guardians_data),
            "assignments": len(assignments_data),
            "attendance": len(attendance_data)
        }

        return summary

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":

    result = generate_master_data()

    print("\nDATASET GENERATION COMPLETED")
    print("----------------------------")

    for key, value in result.items():
        print(f"{key}: {value}")
