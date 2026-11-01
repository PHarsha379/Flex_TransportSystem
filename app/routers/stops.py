from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Stop, AddressZone
from app.schemas.stop import StopCreate, StopUpdate, StopResponse

router = APIRouter(
    prefix="/stops",
    tags=["Stops"]
)


# CREATE STOP
@router.post("/", response_model=StopResponse)
def create_stop(
    payload: StopCreate,
    db: Session = Depends(get_db)
):
    zone = db.get(AddressZone, payload.zone_id)

    if not zone:
        raise HTTPException(404, "Address zone not found")

    if zone.zone_status != "ACTIVE":
        raise HTTPException(400, "Cannot create stop in an inactive zone")

    last_stop = db.query(Stop).order_by(Stop.stop_id.desc()).first()

    next_number = (
        int(last_stop.stop_id.split("-")[-1]) + 1
        if last_stop else 1
    )

    stop_id = f"STOP-{next_number:06d}"

    new_stop = Stop(
        stop_id=stop_id,
        stop_name=payload.stop_name,
        zone_id=payload.zone_id,
        latitude=payload.latitude,
        longitude=payload.longitude,
        is_approved=False,
        stop_status="ACTIVE"
    )

    try:
        db.add(new_stop)
        db.commit()
        db.refresh(new_stop)
        return new_stop
    except Exception:
        db.rollback()
        raise


# GET ALL STOPS
@router.get("/", response_model=list[StopResponse])
def get_stops(db: Session = Depends(get_db)):
    return db.query(Stop).order_by(Stop.stop_id).all()


# GET STOP BY ID
@router.get("/{stop_id}", response_model=StopResponse)
def get_stop(
    stop_id: str,
    db: Session = Depends(get_db)
):
    stop = db.get(Stop, stop_id)

    if not stop:
        raise HTTPException(404, "Stop not found")

    return stop


# UPDATE STOP
@router.put("/{stop_id}", response_model=StopResponse)
def update_stop(
    stop_id: str,
    payload: StopUpdate,
    db: Session = Depends(get_db)
):
    stop = db.get(Stop, stop_id)

    if not stop:
        raise HTTPException(404, "Stop not found")

    data = payload.model_dump(exclude_unset=True)

    if "zone_id" in data:
        zone = db.get(AddressZone, data["zone_id"])

        if not zone:
            raise HTTPException(404, "Address zone not found")

        if zone.zone_status != "ACTIVE":
            raise HTTPException(400, "Cannot move stop to an inactive zone")

    for key, value in data.items():
        setattr(stop, key, value)

    try:
        db.commit()
        db.refresh(stop)
        return stop
    except Exception:
        db.rollback()
        raise


# APPROVE STOP
@router.patch("/{stop_id}/approve", response_model=StopResponse)
def approve_stop(
    stop_id: str,
    db: Session = Depends(get_db)
):
    stop = db.get(Stop, stop_id)

    if not stop:
        raise HTTPException(404, "Stop not found")

    if stop.stop_status != "ACTIVE":
        raise HTTPException(400, "Cannot approve an inactive stop")

    stop.is_approved = True
    stop.approval_date = date.today()

    db.commit()
    db.refresh(stop)

    return stop


# DEACTIVATE STOP
@router.patch("/{stop_id}/deactivate")
def deactivate_stop(
    stop_id: str,
    db: Session = Depends(get_db)
):
    stop = db.get(Stop, stop_id)

    if not stop:
        raise HTTPException(404, "Stop not found")

    stop.stop_status = "INACTIVE"

    db.commit()

    return {
        "message": "Stop deactivated successfully",
        "stop_id": stop_id
    }