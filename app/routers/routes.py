from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date

from app.database import get_db
from app.models import Route, Bus, Driver
from app.schemas.route import RouteCreate, RouteUpdate, RouteResponse

router = APIRouter(
    prefix="/routes",
    tags=["Routes"]
)


# CREATE ROUTE
@router.post("/", response_model=RouteResponse)
def create_route(
    payload: RouteCreate,
    db: Session = Depends(get_db)
):
    bus = db.get(Bus, payload.bus_id)
    driver = db.get(Driver, payload.driver_id)

    if not bus:
        raise HTTPException(404, "Bus not found")

    if not driver:
        raise HTTPException(404, "Driver not found")

    if bus.bus_status != "ACTIVE":
        raise HTTPException(400, "Bus is not active")

    if driver.driver_status != "ACTIVE":
        raise HTTPException(400, "Driver is not active")

    if payload.end_time <= payload.start_time:
        raise HTTPException(400, "End time must be after start time")

    if (
        payload.effective_to
        and payload.effective_to < payload.effective_from
    ):
        raise HTTPException(400, "Invalid route effective dates")

    last_route = db.query(Route).order_by(Route.route_id.desc()).first()

    next_number = (
        int(last_route.route_id.split("-")[-1]) + 1
        if last_route else 1
    )

    route_id = f"ROUTE-{date.today().year}-{next_number:06d}"

    new_route = Route(
        route_id=route_id,
        route_name=payload.route_name,
        bus_id=payload.bus_id,
        driver_id=payload.driver_id,
        start_time=payload.start_time,
        end_time=payload.end_time,
        route_status="DRAFT",
        effective_from=payload.effective_from,
        effective_to=payload.effective_to
    )

    try:
        db.add(new_route)
        db.commit()
        db.refresh(new_route)
        return new_route
    except Exception:
        db.rollback()
        raise


# GET ALL ROUTES
@router.get("/", response_model=list[RouteResponse])
def get_routes(db: Session = Depends(get_db)):
    return db.query(Route).order_by(Route.route_id).all()


# GET ROUTE BY ID
@router.get("/{route_id}", response_model=RouteResponse)
def get_route(
    route_id: str,
    db: Session = Depends(get_db)
):
    route = db.get(Route, route_id)

    if not route:
        raise HTTPException(404, "Route not found")

    return route


# UPDATE ROUTE
@router.put("/{route_id}", response_model=RouteResponse)
def update_route(
    route_id: str,
    payload: RouteUpdate,
    db: Session = Depends(get_db)
):
    route = db.get(Route, route_id)

    if not route:
        raise HTTPException(404, "Route not found")

    data = payload.model_dump(exclude_unset=True)

    bus_id = data.get("bus_id", route.bus_id)
    driver_id = data.get("driver_id", route.driver_id)

    bus = db.get(Bus, bus_id)
    driver = db.get(Driver, driver_id)

    if not bus or bus.bus_status != "ACTIVE":
        raise HTTPException(400, "Selected bus does not exist or is inactive")

    if not driver or driver.driver_status != "ACTIVE":
        raise HTTPException(400, "Selected driver does not exist or is inactive")

    start_time = data.get("start_time", route.start_time)
    end_time = data.get("end_time", route.end_time)

    if end_time <= start_time:
        raise HTTPException(400, "End time must be after start time")

    effective_from = data.get("effective_from", route.effective_from)
    effective_to = data.get("effective_to", route.effective_to)

    if effective_to and effective_to < effective_from:
        raise HTTPException(400, "Invalid route effective dates")

    for key, value in data.items():
        setattr(route, key, value)

    try:
        db.commit()
        db.refresh(route)
        return route
    except Exception:
        db.rollback()
        raise


# ACTIVATE ROUTE
@router.patch("/{route_id}/activate", response_model=RouteResponse)
def activate_route(
    route_id: str,
    db: Session = Depends(get_db)
):
    route = db.get(Route, route_id)

    if not route:
        raise HTTPException(404, "Route not found")

    bus = db.get(Bus, route.bus_id)
    driver = db.get(Driver, route.driver_id)

    if not bus or bus.bus_status != "ACTIVE":
        raise HTTPException(400, "Bus is not active")

    if not driver or driver.driver_status != "ACTIVE":
        raise HTTPException(400, "Driver is not active")

    route.route_status = "ACTIVE"
    db.commit()
    db.refresh(route)

    return route


# DEACTIVATE ROUTE
@router.patch("/{route_id}/deactivate")
def deactivate_route(
    route_id: str,
    db: Session = Depends(get_db)
):
    route = db.get(Route, route_id)

    if not route:
        raise HTTPException(404, "Route not found")

    route.route_status = "INACTIVE"
    db.commit()

    return {
        "message": "Route deactivated successfully",
        "route_id": route_id
    }