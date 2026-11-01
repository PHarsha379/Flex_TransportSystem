from app.database import SessionLocal
from app.models import Student
from app.services.optimization_service import optimize_student_assignment

db = SessionLocal()

try:
    student = db.query(Student).first()

    if student:
        result = optimize_student_assignment(
            db,
            student.student_id
        )

        print(result)
    else:
        print("No students found.")

finally:
    db.close()