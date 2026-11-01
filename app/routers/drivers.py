from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Driver
from app.schemas.driver import (
    DriverCreate,
    DriverUpdate,
    DriverResponse
)

router = APIRouter(
    prefix="/drivers",
    tags=["Drivers"]
)


# CREATE DRIVER
@router.post("/", response_model=DriverResponse)
def create_driver(
    payload: DriverCreate,
    db: Session = Depends(get_db)
):
    existing = db.query(Driver).filter(
        Driver.license_number == payload.license_number
    ).first()

    if existing:
        raise HTTPException(
            status_code=409,
            detail="License number already exists"
        )

    last_driver = db.query(Driver).order_by(
        Driver.driver_id.desc()
    ).first()

    next_number = (
        int(last_driver.driver_id.split("-")[-1]) + 1
        if last_driver else 1
    )

    driver_id = f"DRV-{next_number:06d}"

    new_driver = Driver(
        driver_id=driver_id,
        driver_name=payload.driver_name,
        license_number=payload.license_number,
        phone_number=payload.phone_number,
        driver_status=payload.driver_status
    )

    try:
        db.add(new_driver)
        db.commit()
        db.refresh(new_driver)
        return new_driver
    except Exception:
        db.rollback()
        raise


# GET ALL DRIVERS
@router.get("/", response_model=list[DriverResponse])
def get_drivers(db: Session = Depends(get_db)):
    return db.query(Driver).order_by(Driver.driver_id).all()


# GET DRIVER BY ID
@router.get("/{driver_id}", response_model=DriverResponse)
def get_driver(
    driver_id: str,
    db: Session = Depends(get_db)
):
    driver = db.get(Driver, driver_id)

    if not driver:
        raise HTTPException(404, "Driver not found")

    return driver


# UPDATE DRIVER
@router.put("/{driver_id}", response_model=DriverResponse)
def update_driver(
    driver_id: str,
    payload: DriverUpdate,
    db: Session = Depends(get_db)
):
    driver = db.get(Driver, driver_id)

    if not driver:
        raise HTTPException(404, "Driver not found")

    data = payload.model_dump(exclude_unset=True)

    if "license_number" in data:
        duplicate = db.query(Driver).filter(
            Driver.license_number == data["license_number"],
            Driver.driver_id != driver_id
        ).first()

        if duplicate:
            raise HTTPException(
                status_code=409,
                detail="License number already exists"
            )

    for key, value in data.items():
        setattr(driver, key, value)

    try:
        db.commit()
        db.refresh(driver)
        return driver
    except Exception:
        db.rollback()
        raise


# DEACTIVATE DRIVER
@router.patch("/{driver_id}/deactivate")
def deactivate_driver(
    driver_id: str,
    db: Session = Depends(get_db)
):
    driver = db.get(Driver, driver_id)

    if not driver:
        raise HTTPException(404, "Driver not found")

    driver.driver_status = "INACTIVE"
    db.commit()

    return {
        "message": "Driver deactivated successfully",
        "driver_id": driver_id
    }