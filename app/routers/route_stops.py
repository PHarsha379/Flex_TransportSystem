from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Route, Stop, RouteStop
from app.schemas.route_stop import (
    RouteStopCreate,
    RouteStopUpdate,
    RouteStopResponse
)

router = APIRouter(
    prefix="/routes/{route_id}/stops",
    tags=["Route Stops"]
)


def get_route_or_404(route_id: str, db: Session):
    route = db.get(Route, route_id)

    if not route:
        raise HTTPException(404, "Route not found")

    return route


# ADD STOP TO ROUTE
@router.post("/", response_model=RouteStopResponse)
def add_route_stop(
    route_id: str,
    payload: RouteStopCreate,
    db: Session = Depends(get_db)
):
    route = get_route_or_404(route_id, db)

    stop = db.get(Stop, payload.stop_id)

    if not stop:
        raise HTTPException(404, "Stop not found")

    if stop.stop_status != "ACTIVE":
        raise HTTPException(400, "Stop is inactive")

    if not stop.is_approved:
        raise HTTPException(400, "Stop is not approved")

    existing_stop = db.query(RouteStop).filter(
        RouteStop.route_id == route_id,
        RouteStop.stop_id == payload.stop_id
    ).first()

    if existing_stop:
        raise HTTPException(409, "Stop already exists in this route")

    existing_sequence = db.query(RouteStop).filter(
        RouteStop.route_id == route_id,
        RouteStop.stop_sequence == payload.stop_sequence
    ).first()

    if existing_sequence:
        raise HTTPException(409, "Stop sequence already exists")

    if payload.estimated_arrival < route.start_time:
        raise HTTPException(
            400, "Stop arrival cannot be before route start time"
        )

    if payload.estimated_arrival > route.end_time:
        raise HTTPException(
            400, "Stop arrival cannot be after route end time"
        )

    if payload.stop_sequence == 1 and payload.travel_time_from_previous != 0:
        raise HTTPException(
            400, "First stop must have zero travel time"
        )

    new_route_stop = RouteStop(
        route_id=route_id,
        stop_id=payload.stop_id,
        stop_sequence=payload.stop_sequence,
        estimated_arrival=payload.estimated_arrival,
        travel_time_from_previous=payload.travel_time_from_previous
    )

    try:
        db.add(new_route_stop)
        db.commit()
        db.refresh(new_route_stop)
        return new_route_stop
    except Exception:
        db.rollback()
        raise


# GET ALL STOPS FOR A ROUTE
@router.get("/", response_model=list[RouteStopResponse])
def get_route_stops(
    route_id: str,
    db: Session = Depends(get_db)
):
    get_route_or_404(route_id, db)

    return db.query(RouteStop).filter(
        RouteStop.route_id == route_id
    ).order_by(RouteStop.stop_sequence).all()


# GET ONE ROUTE STOP
@router.get("/{route_stop_id}", response_model=RouteStopResponse)
def get_route_stop(
    route_id: str,
    route_stop_id: int,
    db: Session = Depends(get_db)
):
    route_stop = db.query(RouteStop).filter(
        RouteStop.route_id == route_id,
        RouteStop.route_stop_id == route_stop_id
    ).first()

    if not route_stop:
        raise HTTPException(404, "Route stop not found")

    return route_stop


# UPDATE ROUTE STOP
@router.put("/{route_stop_id}", response_model=RouteStopResponse)
def update_route_stop(
    route_id: str,
    route_stop_id: int,
    payload: RouteStopUpdate,
    db: Session = Depends(get_db)
):
    route_stop = db.query(RouteStop).filter(
        RouteStop.route_id == route_id,
        RouteStop.route_stop_id == route_stop_id
    ).first()

    if not route_stop:
        raise HTTPException(404, "Route stop not found")

    data = payload.model_dump(exclude_unset=True)

    new_sequence = data.get(
        "stop_sequence", route_stop.stop_sequence
    )

    duplicate = db.query(RouteStop).filter(
        RouteStop.route_id == route_id,
        RouteStop.stop_sequence == new_sequence,
        RouteStop.route_stop_id != route_stop_id
    ).first()

    if duplicate:
        raise HTTPException(409, "Stop sequence already exists")

    route = get_route_or_404(route_id, db)

    arrival = data.get(
        "estimated_arrival", route_stop.estimated_arrival
    )

    if not route.start_time <= arrival <= route.end_time:
        raise HTTPException(400, "Arrival time is outside route timings")

    for key, value in data.items():
        setattr(route_stop, key, value)

    try:
        db.commit()
        db.refresh(route_stop)
        return route_stop
    except Exception:
        db.rollback()
        raise


# REMOVE STOP FROM ROUTE
@router.delete("/{route_stop_id}")
def remove_route_stop(
    route_id: str,
    route_stop_id: int,
    db: Session = Depends(get_db)
):
    route_stop = db.query(RouteStop).filter(
        RouteStop.route_id == route_id,
        RouteStop.route_stop_id == route_stop_id
    ).first()

    if not route_stop:
        raise HTTPException(404, "Route stop not found")

    db.delete(route_stop)
    db.commit()

    return {"message": "Stop removed from route successfully"}