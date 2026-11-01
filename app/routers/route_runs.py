from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Route, RouteRun, Bus, Driver
from app.schemas.route_run import RouteRunCreate, RouteRunUpdate

router = APIRouter(
    prefix="/route-runs",
    tags=["Route Run Management"]
)


def generate_run_id(db: Session):
    last_run = (
        db.query(RouteRun)
        .order_by(RouteRun.run_id.desc())
        .first()
    )

    return last_run.run_id + 1 if last_run else 1

# 1. Create a route run
@router.post("/")
def create_route_run(
    payload: RouteRunCreate,
    db: Session = Depends(get_db)
):
    route = db.get(Route, payload.route_id)

    if not route:
        raise HTTPException(404, "Route not found")

    bus = db.get(Bus, route.bus_id)
    driver = db.get(Driver, route.driver_id)

    if not bus or bus.bus_status != "ACTIVE":
        raise HTTPException(400, "Bus is not active")

    if not driver or driver.driver_status != "ACTIVE":
        raise HTTPException(400, "Driver is not active")

    if route.route_status != "ACTIVE":
        raise HTTPException(400, "Route is not active")

    if payload.arrival_time <= payload.departure_time:
        raise HTTPException(
            400,
            "Arrival time must be after departure time"
        )

    if payload.run_date < date.today():
        raise HTTPException(
            400,
            "Cannot create a route run for a past date"
        )

    if payload.run_date < route.effective_from:
        raise HTTPException(
            400,
            "Route is not effective on this date"
        )

    if route.effective_to and payload.run_date > route.effective_to:
        raise HTTPException(
            400,
            "Route is not effective on this date"
        )

    if payload.departure_time < route.start_time:
        raise HTTPException(
            400,
            "Departure is earlier than the route start time"
        )

    if payload.arrival_time > route.end_time:
        raise HTTPException(
            400,
            "Arrival is later than the route end time"
        )

    existing_run = db.query(RouteRun).filter(
        RouteRun.route_id == payload.route_id,
        RouteRun.run_date == payload.run_date,
        RouteRun.trip_number == payload.trip_number
    ).first()

    if existing_run:
        raise HTTPException(
            409,
            "Trip number already exists for this route and date"
        )

    run = RouteRun(
        run_id=generate_run_id(db),
        route_id=route.route_id,
        bus_id=route.bus_id,
        driver_id=route.driver_id,
        run_date=payload.run_date,
        trip_number=payload.trip_number,
        departure_time=payload.departure_time,
        arrival_time=payload.arrival_time,
        run_status=payload.run_status
    )

    db.add(run)
    db.commit()
    db.refresh(run)

    return run


# 2. Get all route runs
@router.get("/")
def get_route_runs(db: Session = Depends(get_db)):
    return db.query(RouteRun).order_by(
        RouteRun.run_date,
        RouteRun.trip_number
    ).all()


# 3. Get route run by ID
@router.get("/{run_id}")
def get_route_run(
    run_id: str,
    db: Session = Depends(get_db)
):
    run = db.get(RouteRun, run_id)

    if not run:
        raise HTTPException(404, "Route run not found")

    return run


# 4. Get runs for a particular route
@router.get("/route/{route_id}")
def get_runs_by_route(
    route_id: str,
    db: Session = Depends(get_db)
):
    route = db.get(Route, route_id)

    if not route:
        raise HTTPException(404, "Route not found")

    return db.query(RouteRun).filter(
        RouteRun.route_id == route_id
    ).order_by(
        RouteRun.run_date,
        RouteRun.trip_number
    ).all()


# 5. Update route run
@router.put("/{run_id}")
def update_route_run(
    run_id: str,
    payload: RouteRunUpdate,
    db: Session = Depends(get_db)
):
    run = db.get(RouteRun, run_id)

    if not run:
        raise HTTPException(404, "Route run not found")

    updates = payload.model_dump(exclude_unset=True)

    new_departure = updates.get(
        "departure_time", run.departure_time
    )
    new_arrival = updates.get(
        "arrival_time", run.arrival_time
    )

    if new_arrival <= new_departure:
        raise HTTPException(
            400,
            "Arrival time must be after departure time"
        )

    route = db.get(Route, run.route_id)

    if new_departure < route.start_time or new_arrival > route.end_time:
        raise HTTPException(
            400,
            "Run times must be within route operating times"
        )

    for field, value in updates.items():
        setattr(run, field, value)

    db.commit()
    db.refresh(run)

    return run


# 6. Cancel route run
@router.patch("/{run_id}/cancel")
def cancel_route_run(
    run_id: str,
    db: Session = Depends(get_db)
):
    run = db.get(RouteRun, run_id)

    if not run:
        raise HTTPException(404, "Route run not found")

    if run.run_status == "COMPLETED":
        raise HTTPException(
            400,
            "Completed runs cannot be cancelled"
        )

    run.run_status = "CANCELLED"

    db.commit()

    return {
    "message": "Route run cancelled",
    "run_id": run.run_id
}