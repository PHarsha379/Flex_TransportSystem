from fastapi import FastAPI
from app.routers import health, students, assignments
from app.database import Base, engine
from app.routers import zones
from app import models
from app.routers import stops
from app.routers import drivers
from app.routers import buses
from app.routers import routes
from app.routers import route_stops
from app.routers import guardians
from app.routers import route_runs
from app.routers import reallocation
from app.routers import attendance

from app.routers import notifications

from app.routers import analytics
from app.routers import disruptions
from app.routers import audit
from app.routers import exports

from app.routers import generations



app = FastAPI(
    title="Student Transportation Management System",
    description="Capacity-aware student transportation assignment and monitoring API",
    version="0.1.0",
)
Base.metadata.create_all(bind=engine)
app.include_router(health.router)
app.include_router(students.router)
app.include_router(assignments.router)
app.include_router(zones.router)
app.include_router(buses.router)
app.include_router(drivers.router)
app.include_router(stops.router)
app.include_router(routes.router)
app.include_router(route_stops.router)
app.include_router(guardians.router)
app.include_router(route_runs.router)
app.include_router(reallocation.router)
app.include_router(attendance.router)
app.include_router(notifications.router)
app.include_router(disruptions.router)
app.include_router(audit.router)
app.include_router(analytics.router)
app.include_router(exports.router)
app.include_router(generations.router)

@app.get("/")
def root():
    return {"name": "Student Transportation Management System", "status": "running"}
for route in app.routes:
    print(
        getattr(route, "methods", None),
        getattr(route, "path", None)
    )