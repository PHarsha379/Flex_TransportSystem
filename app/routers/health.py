from fastapi import APIRouter
from sqlalchemy import text
from app.database import engine

router = APIRouter(tags=["Health"])


@router.get("/health")
def health():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"api": "healthy", "database": "connected"}
    except Exception as exc:
        return {"api": "running", "database": "unavailable", "detail": str(exc)}
