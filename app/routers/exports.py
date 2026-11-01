import csv
import io
import json

from datetime import date, datetime, time
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import (
    Student,
    Assignment,
    AttendanceEvent,
)

router = APIRouter(
    prefix="/export",
    tags=["Data Export"]
)


# --------------------------------------------------
# HELPER: CONVERT VALUES TO CSV/JSON SAFE VALUES
# --------------------------------------------------

def serialize_value(value):
    if isinstance(value, (date, datetime, time)):
        return value.isoformat()

    if isinstance(value, Decimal):
        return float(value)

    return value


def model_to_dict(obj):
    return {
        column.name: serialize_value(
            getattr(obj, column.name)
        )
        for column in obj.__table__.columns
    }


# --------------------------------------------------
# HELPER: GENERATE CSV
# --------------------------------------------------

def generate_csv(records, filename):
    output = io.StringIO()

    if not records:
        output.write("No records found\n")
    else:
        writer = csv.DictWriter(
            output,
            fieldnames=list(records[0].keys())
        )

        writer.writeheader()
        writer.writerows(records)

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


# --------------------------------------------------
# 1. EXPORT STUDENTS CSV
# --------------------------------------------------

@router.get("/students/csv")
def export_students_csv(db: Session = Depends(get_db)):

    students = db.query(Student).all()

    records = [
        model_to_dict(student)
        for student in students
    ]

    return generate_csv(
        records,
        "students.csv"
    )


# --------------------------------------------------
# 2. EXPORT ASSIGNMENTS CSV
# --------------------------------------------------

@router.get("/assignments/csv")
def export_assignments_csv(db: Session = Depends(get_db)):

    assignments = db.query(Assignment).all()

    records = [
        model_to_dict(assignment)
        for assignment in assignments
    ]

    return generate_csv(
        records,
        "assignments.csv"
    )


# --------------------------------------------------
# 3. EXPORT ATTENDANCE CSV
# --------------------------------------------------

@router.get("/attendance/csv")
def export_attendance_csv(db: Session = Depends(get_db)):

    attendance_records = db.query(AttendanceEvent).all()

    records = [
        model_to_dict(record)
        for record in attendance_records
    ]

    return generate_csv(
        records,
        "attendance.csv"
    )


# --------------------------------------------------
# 4. EXPORT COMPLETE DATASET JSON
# --------------------------------------------------

@router.get("/dataset/json")
def export_dataset_json(db: Session = Depends(get_db)):

    students = db.query(Student).all()
    assignments = db.query(Assignment).all()
    attendance = db.query(AttendanceEvent).all()

    dataset = {
        "students": [
            model_to_dict(student)
            for student in students
        ],

        "assignments": [
            model_to_dict(assignment)
            for assignment in assignments
        ],

        "attendance": [
            model_to_dict(record)
            for record in attendance
        ]
    }

    json_content = json.dumps(
        dataset,
        indent=4
    )

    return StreamingResponse(
        iter([json_content]),
        media_type="application/json",
        headers={
            "Content-Disposition":
                "attachment; filename=student_transport_dataset.json"
        }
    )


# --------------------------------------------------
# 5. EXPORT SQL INSERT STATEMENTS
# --------------------------------------------------

@router.get("/dataset/sql")
def export_dataset_sql(db: Session = Depends(get_db)):

    models = [
        Student,
        Assignment,
        AttendanceEvent,
    ]

    output = io.StringIO()

    output.write("-- Student Transportation Dataset SQL Export\n")
    output.write("-- Contains INSERT statements only\n\n")

    for model in models:

        records = db.query(model).all()

        table_name = model.__tablename__

        for record in records:

            columns = []
            values = []

            for column in model.__table__.columns:

                columns.append(f"`{column.name}`")

                value = getattr(record, column.name)

                if value is None:
                    values.append("NULL")

                elif isinstance(value, (datetime, date, time)):
                    values.append(
                        "'" + value.isoformat() + "'"
                    )

                elif isinstance(value, Decimal):
                    values.append(str(value))

                elif isinstance(value, bool):
                    values.append("1" if value else "0")

                elif isinstance(value, (int, float)):
                    values.append(str(value))

                else:
                    safe_value = str(value).replace("\\", "\\\\")
                    safe_value = safe_value.replace("'", "\\'")
                    values.append("'" + safe_value + "'")

            sql = (
                f"INSERT INTO `{table_name}` "
                f"({', '.join(columns)}) "
                f"VALUES ({', '.join(values)});\n"
            )

            output.write(sql)

        output.write("\n")

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="application/sql",
        headers={
            "Content-Disposition":
                "attachment; filename=student_transport_dataset.sql"
        }
    )