from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.models import GenerationRun

from app.schemas.generation import (
    GenerationRunCreate,
    GenerationRunUpdate
)

router = APIRouter(
    prefix="/generation-runs",
    tags=["Generation Management"]
)


# 1. Start a generation run
@router.post("/")
def start_generation(
    payload: GenerationRunCreate,
    db: Session = Depends(get_db)
):

    generation = GenerationRun(
        seed=payload.seed,
        generation_status="RUNNING",
        started_at=datetime.utcnow(),
        students_generated=0,
        buses_generated=0,
        stops_generated=0,
        routes_generated=0,
        assignments_generated=0
    )

    db.add(generation)
    db.commit()
    db.refresh(generation)

    return {
        "message": "Generation run started",
        "generation": generation
    }


# 2. Get all generation runs
@router.get("/")
def get_generation_runs(db: Session = Depends(get_db)):

    return db.query(GenerationRun).order_by(
        GenerationRun.started_at.desc()
    ).all()


# 3. Get generation run by ID
@router.get("/{generation_id}")
def get_generation(
    generation_id: int,
    db: Session = Depends(get_db)
):

    generation = db.get(GenerationRun, generation_id)

    if not generation:
        raise HTTPException(
            404,
            "Generation run not found"
        )

    return generation


# 4. Update generation counts
@router.patch("/{generation_id}/counts")
def update_generation_counts(
    generation_id: int,
    payload: GenerationRunUpdate,
    db: Session = Depends(get_db)
):

    generation = db.get(GenerationRun, generation_id)

    if not generation:
        raise HTTPException(404, "Generation run not found")

    if generation.generation_status != "RUNNING":
        raise HTTPException(
            400,
            "Only running generations can be updated"
        )

    updates = payload.model_dump(exclude_unset=True)

    for field, value in updates.items():
        setattr(generation, field, value)

    db.commit()
    db.refresh(generation)

    return generation


# 5. Complete generation
@router.patch("/{generation_id}/complete")
def complete_generation(
    generation_id: int,
    db: Session = Depends(get_db)
):

    generation = db.get(GenerationRun, generation_id)

    if not generation:
        raise HTTPException(404, "Generation run not found")

    if generation.generation_status != "RUNNING":
        raise HTTPException(
            400,
            "Generation is not running"
        )

    generation.generation_status = "COMPLETED"
    generation.completed_at = datetime.utcnow()

    db.commit()
    db.refresh(generation)

    return {
        "message": "Generation completed successfully",
        "generation": generation
    }


# 6. Mark generation as failed
@router.patch("/{generation_id}/fail")
def fail_generation(
    generation_id: int,
    error_message: str,
    db: Session = Depends(get_db)
):

    generation = db.get(GenerationRun, generation_id)

    if not generation:
        raise HTTPException(404, "Generation run not found")

    if generation.generation_status != "RUNNING":
        raise HTTPException(
            400,
            "Generation is not running"
        )

    generation.generation_status = "FAILED"
    generation.error_message = error_message
    generation.completed_at = datetime.utcnow()

    db.commit()
    db.refresh(generation)

    return {
        "message": "Generation marked as failed",
        "generation": generation
    }