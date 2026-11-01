from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Student
from app.schemas.student import StudentCreate, StudentRead

router = APIRouter(prefix="/students", tags=["Students"])


@router.post("/", response_model=StudentRead, status_code=201)
def create_student(payload: StudentCreate, db: Session = Depends(get_db)):
    if payload.pickup_end <= payload.pickup_start:
        raise HTTPException(400, "pickup_end must be later than pickup_start")
    if db.get(Student, payload.student_id):
        raise HTTPException(409, "Student ID already exists")
    student = Student(**payload.model_dump())
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


@router.get("/", response_model=list[StudentRead])
def list_students(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(Student).order_by(Student.student_id).offset(skip).limit(min(limit, 500)).all()


@router.get("/{student_id}", response_model=StudentRead)
def get_student(student_id: str, db: Session = Depends(get_db)):
    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(404, "Student not found")
    return student
