from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.models import Route, RouteRun, RouteDisruption

from app.schemas.disruption import (
    DisruptionCreate,
    DisruptionUpdate,
    DisruptionStatusUpdate
)

router = APIRouter(
    prefix="/disruptions",
    tags=["Route Disruption Management"]
)


VALID_DISRUPTION_TYPES = [
    "BUS_BREAKDOWN",
    "TRAFFIC_DELAY",
    "ROAD_CLOSURE",
    "DRIVER_UNAVAILABLE",
    "WEATHER",
    "OTHER"
]


# 1. Report a disruption
@router.post("/")
def report_disruption(
    payload: DisruptionCreate,
    db: Session = Depends(get_db)
):

    route = db.get(Route, payload.route_id)

    if not route:
        raise HTTPException(
            404,
            "Route not found"
        )

    if payload.disruption_type not in VALID_DISRUPTION_TYPES:
        raise HTTPException(
            400,
            "Invalid disruption type"
        )

    if payload.run_id:

        run = db.get(RouteRun, payload.run_id)

        if not run:
            raise HTTPException(
                404,
                "Route run not found"
            )

        if run.route_id != payload.route_id:
            raise HTTPException(
                400,
                "Route run does not belong to this route"
            )

    disruption = RouteDisruption(
        route_id=payload.route_id,
        run_id=payload.run_id,
        disruption_type=payload.disruption_type,
        description=payload.description,
        reported_at=datetime.utcnow(),
        expected_delay_minutes=payload.expected_delay_minutes,
        disruption_status="OPEN"
    )

    db.add(disruption)
    db.commit()
    db.refresh(disruption)

    return {
        "message": "Disruption reported successfully",
        "disruption": disruption
    }


# 2. Get all disruptions
@router.get("/")
def get_disruptions(db: Session = Depends(get_db)):

    return db.query(RouteDisruption).order_by(
        RouteDisruption.reported_at.desc()
    ).all()


# 3. Get disruption by ID
@router.get("/{disruption_id}")
def get_disruption(
    disruption_id: int,
    db: Session = Depends(get_db)
):

    disruption = db.get(
        RouteDisruption,
        disruption_id
    )

    if not disruption:
        raise HTTPException(
            404,
            "Disruption not found"
        )

    return disruption


# 4. Get disruptions by route
@router.get("/route/{route_id}")
def get_route_disruptions(
    route_id: str,
    db: Session = Depends(get_db)
):

    route = db.get(Route, route_id)

    if not route:
        raise HTTPException(
            404,
            "Route not found"
        )

    return db.query(RouteDisruption).filter(
        RouteDisruption.route_id == route_id
    ).all()


# 5. Update disruption details
@router.put("/{disruption_id}")
def update_disruption(
    disruption_id: int,
    payload: DisruptionUpdate,
    db: Session = Depends(get_db)
):

    disruption = db.get(
        RouteDisruption,
        disruption_id
    )

    if not disruption:
        raise HTTPException(
            404,
            "Disruption not found"
        )

    if disruption.disruption_status == "RESOLVED":
        raise HTTPException(
            400,
            "Resolved disruption cannot be updated"
        )

    updates = payload.model_dump(exclude_unset=True)

    for field, value in updates.items():
        setattr(disruption, field, value)

    db.commit()
    db.refresh(disruption)

    return disruption


# 6. Update disruption status
@router.patch("/{disruption_id}/status")
def update_disruption_status(
    disruption_id: int,
    payload: DisruptionStatusUpdate,
    db: Session = Depends(get_db)
):

    disruption = db.get(
        RouteDisruption,
        disruption_id
    )

    if not disruption:
        raise HTTPException(
            404,
            "Disruption not found"
        )

    allowed_statuses = [
        "OPEN",
        "IN_PROGRESS",
        "RESOLVED"
    ]

    if payload.disruption_status not in allowed_statuses:
        raise HTTPException(
            400,
            "Invalid disruption status"
        )

    disruption.disruption_status = payload.disruption_status

    if payload.disruption_status == "RESOLVED":
        disruption.resolved_at = datetime.utcnow()

    else:
        disruption.resolved_at = None

    db.commit()
    db.refresh(disruption)

    return {
        "message": "Disruption status updated",
        "disruption": disruption
    }