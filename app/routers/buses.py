
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Bus
from app.schemas.bus import BusCreate, BusUpdate, BusResponse
from app.services.audit_service import create_audit_log

router = APIRouter(
    prefix="/buses",
    tags=["Buses"]
)


# CREATE BUS
@router.post("/", response_model=BusResponse)
def create_bus(
    payload: BusCreate,
    db: Session = Depends(get_db)
):
    existing = db.query(Bus).filter(
        Bus.registration_number == payload.registration_number
    ).first()

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Registration number already exists"
        )

    last_bus = db.query(Bus).order_by(
        Bus.bus_id.desc()
    ).first()

    if last_bus:
        next_number = int(last_bus.bus_id.split("-")[-1]) + 1
    else:
        next_number = 1

    bus_id = f"BUS-{next_number:06d}"

    new_bus = Bus(
        bus_id=bus_id,
        registration_number=payload.registration_number,
        capacity=payload.capacity,
        accessible=payload.accessible,
        bus_status=payload.bus_status
    )

    try:
        db.add(new_bus)

        db.flush()

        create_audit_log(
            db=db,
            actor_id="ADMIN-001",
            action="CREATE",
            entity_type="BUS",
            entity_id=new_bus.bus_id,
            old_values=None,
            new_values={
                "registration_number": new_bus.registration_number,
                "capacity": new_bus.capacity,
                "accessible": new_bus.accessible,
                "bus_status": new_bus.bus_status
            }
        )

        db.commit()
        db.refresh(new_bus)

        return new_bus

    except Exception:
        db.rollback()
        raise


# GET ALL BUSES
@router.get("/", response_model=list[BusResponse])
def get_buses(db: Session = Depends(get_db)):
    return db.query(Bus).order_by(Bus.bus_id).all()


# GET BUS BY ID
@router.get("/{bus_id}", response_model=BusResponse)
def get_bus(
    bus_id: str,
    db: Session = Depends(get_db)
):
    bus = db.get(Bus, bus_id)

    if not bus:
        raise HTTPException(
            status_code=404,
            detail="Bus not found"
        )

    return bus


# UPDATE BUS
@router.put("/{bus_id}", response_model=BusResponse)
def update_bus(
    bus_id: str,
    payload: BusUpdate,
    db: Session = Depends(get_db)
):
    bus = db.get(Bus, bus_id)

    if not bus:
        raise HTTPException(
            status_code=404,
            detail="Bus not found"
        )

    old_values = {
        "registration_number": bus.registration_number,
        "capacity": bus.capacity,
        "accessible": bus.accessible,
        "bus_status": bus.bus_status
    }

    updates = payload.model_dump(exclude_unset=True)

    if "registration_number" in updates:
        duplicate = db.query(Bus).filter(
            Bus.registration_number == updates["registration_number"],
            Bus.bus_id != bus_id
        ).first()

        if duplicate:
            raise HTTPException(
                status_code=409,
                detail="Registration number already exists"
            )

    try:
        for field, value in updates.items():
            setattr(bus, field, value)

        new_values = {
            "registration_number": bus.registration_number,
            "capacity": bus.capacity,
            "accessible": bus.accessible,
            "bus_status": bus.bus_status
        }

        create_audit_log(
            db=db,
            actor_id="ADMIN-001",
            action="UPDATE",
            entity_type="BUS",
            entity_id=bus.bus_id,
            old_values=old_values,
            new_values=new_values
        )

        db.commit()
        db.refresh(bus)

        return bus

    except Exception:
        db.rollback()
        raise


# DEACTIVATE BUS
@router.patch("/{bus_id}/deactivate")
def deactivate_bus(
    bus_id: str,
    db: Session = Depends(get_db)
):
    bus = db.get(Bus, bus_id)

    if not bus:
        raise HTTPException(
            status_code=404,
            detail="Bus not found"
        )

    if bus.bus_status == "INACTIVE":
        raise HTTPException(
            status_code=400,
            detail="Bus is already inactive"
        )

    old_values = {
        "registration_number": bus.registration_number,
        "capacity": bus.capacity,
        "accessible": bus.accessible,
        "bus_status": bus.bus_status
    }

    try:
        bus.bus_status = "INACTIVE"

        new_values = {
            "registration_number": bus.registration_number,
            "capacity": bus.capacity,
            "accessible": bus.accessible,
            "bus_status": bus.bus_status
        }

        create_audit_log(
            db=db,
            actor_id="ADMIN-001",
            action="DEACTIVATE",
            entity_type="BUS",
            entity_id=bus.bus_id,
            old_values=old_values,
            new_values=new_values
        )

        db.commit()

        return {
            "message": "Bus deactivated successfully",
            "bus_id": bus_id
        }

    except Exception:
        db.rollback()
        raise
