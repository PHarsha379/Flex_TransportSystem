from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AddressZone
from app.schemas.zone import (
    ZoneCreate,
    ZoneUpdate,
    ZoneResponse
)

router = APIRouter(
    prefix="/zones",
    tags=["Address Zones"]
)


# CREATE ZONE
@router.post("/", response_model=ZoneResponse)
def create_zone(
    payload: ZoneCreate,
    db: Session = Depends(get_db)
):
    existing_zone = db.query(AddressZone).filter(
        AddressZone.zone_name == payload.zone_name
    ).first()

    if existing_zone:
        raise HTTPException(
            status_code=409,
            detail="Zone name already exists"
        )

    new_zone = AddressZone(
        zone_name=payload.zone_name,
        latitude=payload.latitude,
        longitude=payload.longitude,
        zone_status=payload.zone_status
    )

    db.add(new_zone)
    db.commit()
    db.refresh(new_zone)

    return new_zone


# GET ALL ZONES
@router.get("/", response_model=list[ZoneResponse])
def get_zones(db: Session = Depends(get_db)):
    return db.query(AddressZone).all()


# GET ZONE BY ID
@router.get("/{zone_id}", response_model=ZoneResponse)
def get_zone(
    zone_id: int,
    db: Session = Depends(get_db)
):
    zone = db.get(AddressZone, zone_id)

    if not zone:
        raise HTTPException(
            status_code=404,
            detail="Zone not found"
        )

    return zone


# UPDATE ZONE
@router.put("/{zone_id}", response_model=ZoneResponse)
def update_zone(
    zone_id: int,
    payload: ZoneUpdate,
    db: Session = Depends(get_db)
):
    zone = db.get(AddressZone, zone_id)

    if not zone:
        raise HTTPException(
            status_code=404,
            detail="Zone not found"
        )

    update_data = payload.model_dump(exclude_unset=True)

    if "zone_name" in update_data:
        duplicate = db.query(AddressZone).filter(
            AddressZone.zone_name == update_data["zone_name"],
            AddressZone.zone_id != zone_id
        ).first()

        if duplicate:
            raise HTTPException(
                status_code=409,
                detail="Zone name already exists"
            )

    for key, value in update_data.items():
        setattr(zone, key, value)

    db.commit()
    db.refresh(zone)

    return zone


# DEACTIVATE ZONE
@router.patch("/{zone_id}/deactivate")
def deactivate_zone(
    zone_id: int,
    db: Session = Depends(get_db)
):
    zone = db.get(AddressZone, zone_id)

    if not zone:
        raise HTTPException(
            status_code=404,
            detail="Zone not found"
        )

    zone.zone_status = "INACTIVE"

    db.commit()

    return {
        "message": "Zone deactivated successfully",
        "zone_id": zone_id
    }