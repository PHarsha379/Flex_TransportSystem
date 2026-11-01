from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Student, GuardianContact
from app.schemas.guardian import GuardianCreate, GuardianUpdate

router = APIRouter(
    prefix="/guardians",
    tags=["Guardian Management"]
)


def generate_guardian_id(db: Session):
    last_guardian = (
        db.query(GuardianContact)
        .order_by(GuardianContact.guardian_id.desc())
        .first()
    )

    if last_guardian:
        last_number = int(last_guardian.guardian_id.split("-")[1])
        next_number = last_number + 1
    else:
        next_number = 1

    return f"GDN-{next_number:06d}"


# 1. Add guardian
@router.post("/")
def create_guardian(
    payload: GuardianCreate,
    db: Session = Depends(get_db)
):
    student = db.get(Student, payload.student_id)

    if not student:
        raise HTTPException(
            status_code=404,
            detail="Student not found"
        )

    if student.status != "ACTIVE":
        raise HTTPException(
            status_code=400,
            detail="Cannot add guardian to inactive student"
        )

    if payload.is_primary:
        existing_primary = db.query(GuardianContact).filter(
            GuardianContact.student_id == payload.student_id,
            GuardianContact.is_primary == True,
            GuardianContact.contact_status == "ACTIVE"
        ).first()

        if existing_primary:
            raise HTTPException(
                status_code=409,
                detail="Student already has a primary guardian"
            )

    guardian = GuardianContact(
        guardian_id=generate_guardian_id(db),
        student_id=payload.student_id,
        guardian_name=payload.guardian_name,
        phone_number=payload.phone_number,
        email=payload.email,
        is_primary=payload.is_primary,
        is_valid=payload.is_valid,
        contact_status=payload.contact_status
    )

    db.add(guardian)
    db.commit()
    db.refresh(guardian)

    return guardian


# 2. Get all guardians
@router.get("/")
def get_guardians(db: Session = Depends(get_db)):
    return db.query(GuardianContact).all()


# 3. Get guardian by ID
@router.get("/{guardian_id}")
def get_guardian(
    guardian_id: str,
    db: Session = Depends(get_db)
):
    guardian = db.get(GuardianContact, guardian_id)

    if not guardian:
        raise HTTPException(
            status_code=404,
            detail="Guardian not found"
        )

    return guardian


# 4. Get guardians by student ID
@router.get("/student/{student_id}")
def get_student_guardians(
    student_id: str,
    db: Session = Depends(get_db)
):
    student = db.get(Student, student_id)

    if not student:
        raise HTTPException(
            status_code=404,
            detail="Student not found"
        )

    return db.query(GuardianContact).filter(
        GuardianContact.student_id == student_id
    ).all()


# 5. Update guardian
@router.put("/{guardian_id}")
def update_guardian(
    guardian_id: str,
    payload: GuardianUpdate,
    db: Session = Depends(get_db)
):
    guardian = db.get(GuardianContact, guardian_id)

    if not guardian:
        raise HTTPException(
            status_code=404,
            detail="Guardian not found"
        )

    updates = payload.model_dump(exclude_unset=True)

    if updates.get("is_primary") is True:
        existing_primary = db.query(GuardianContact).filter(
            GuardianContact.student_id == guardian.student_id,
            GuardianContact.is_primary == True,
            GuardianContact.contact_status == "ACTIVE",
            GuardianContact.guardian_id != guardian_id
        ).first()

        if existing_primary:
            raise HTTPException(
                status_code=409,
                detail="Another primary guardian already exists"
            )

    for field, value in updates.items():
        setattr(guardian, field, value)

    db.commit()
    db.refresh(guardian)

    return guardian


# 6. Deactivate guardian
@router.patch("/{guardian_id}/deactivate")
def deactivate_guardian(
    guardian_id: str,
    db: Session = Depends(get_db)
):
    guardian = db.get(GuardianContact, guardian_id)

    if not guardian:
        raise HTTPException(
            status_code=404,
            detail="Guardian not found"
        )

    guardian.contact_status = "INACTIVE"
    guardian.is_primary = False

    db.commit()

    return {
        "message": "Guardian deactivated successfully",
        "guardian_id": guardian_id
    }


# 7. Update contact validity
@router.patch("/{guardian_id}/validity")
def update_guardian_validity(
    guardian_id: str,
    is_valid: bool,
    db: Session = Depends(get_db)
):
    guardian = db.get(GuardianContact, guardian_id)

    if not guardian:
        raise HTTPException(
            status_code=404,
            detail="Guardian not found"
        )

    guardian.is_valid = is_valid

    db.commit()

    return {
        "guardian_id": guardian_id,
        "is_valid": is_valid,
        "message": "Contact validity updated"
    }