# YottaFlex – Student Transportation Management System

## 1. Project Overview

YottaFlex is a Smart Student Transportation Management System developed using **FastAPI, Python, MySQL, and SQLAlchemy**.

The system helps manage student transportation operations, including student registration, guardian information, buses, drivers, routes, route stops, trip scheduling, student assignments, attendance tracking, notifications, and route disruptions.

It also provides assignment optimization, analytics, data validation, and dataset export functionality.

## 2. Objectives

- Manage student and guardian information.
- Maintain bus and driver records.
- Create and manage transportation routes.
- Schedule daily route runs.
- Assign students to suitable routes and stops.
- Track student pickup attendance.
- Notify guardians about attendance and transportation issues.
- Record route disruptions and maintain audit logs.
- Optimize student transportation assignments.
- Generate analytics and export datasets.

## 3. Technology Stack

| Component | Technology |
|---|---|
| Programming Language | Python |
| Backend Framework | FastAPI |
| Database | MySQL |
| ORM | SQLAlchemy 2.0 |
| Data Validation | Pydantic |
| API Testing | Pytest |
| API Documentation | Swagger UI |
| Server | Uvicorn |

## 4. Project Structure

```text
student_transport_system/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   └── entities.py
│   │
│   ├── schemas/
│   │   ├── student.py
│   │   ├── guardian.py
│   │   ├── bus.py
│   │   ├── driver.py
│   │   ├── route.py
│   │   ├── route_run.py
│   │   ├── route_stop.py
│   │   ├── stop.py
│   │   ├── assignment.py
│   │   ├── attendance.py
│   │   ├── notification.py
│   │   ├── disruption.py
│   │   ├── audit.py
│   │   ├── analytics.py
│   │   ├── export.py
│   │   └── generation.py
│   │
│   ├── routers/
│   │   ├── students.py
│   │   ├── guardians.py
│   │   ├── buses.py
│   │   ├── drivers.py
│   │   ├── routes.py
│   │   ├── route_runs.py
│   │   ├── route_stops.py
│   │   ├── stops.py
│   │   ├── assignments.py
│   │   ├── attendance.py
│   │   ├── notifications.py
│   │   ├── disruptions.py
│   │   ├── audit.py
│   │   ├── analytics.py
│   │   ├── generations.py
│   │   ├── reallocation.py
│   │   └── health.py
│   │
│   ├── services/
│   │   ├── assignment_service.py
│   │   ├── optimization_service.py
│   │   └── audit_service.py
│   │
│   └── generators/
│       ├── master_generator.py
│       └── validate_dataset.py
│
├── tests/
│   ├── conftest.py
│   ├── test_students.py
│   ├── test_guardians.py
│   ├── test_buses.py
│   ├── test_drivers.py
│   ├── test_routes.py
│   ├── test_route_runs.py
│   ├── test_stops.py
│   ├── test_assignments.py
│   ├── test_attendance.py
│   ├── test_notifications.py
│   ├── test_disruptions.py
│   ├── test_audit.py
│   └── test_analytics.py
│
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## 5. Core Modules

### Master Data Management
- Student management
- Guardian contact management
- Bus management
- Driver management
- Stop management
- Zone management

### Route Management
- Create and manage routes.
- Associate buses and drivers with routes.
- Manage route stops and their sequence.
- Activate and deactivate routes.

### Route Run Management
- Schedule transportation trips.
- Manage departure and arrival times.
- Validate route operating dates and timings.
- Cancel scheduled route runs.

### Student Assignment Management
- Assign students to routes and stops.
- Validate assignment constraints.
- Check bus capacity and accessibility requirements.
- Generate optimized assignment proposals.

### Attendance Management
- Record student pickup attendance.
- Track attendance statuses.
- Retrieve attendance records by student.

### Notification Management
- Create guardian notifications.
- Track notification delivery status.
- Maintain attendance-related notifications.

### Disruption Management
- Report route disruptions.
- Track expected delays.
- Update and resolve disruptions.

### Audit Management
- Maintain audit logs.
- Track actions performed on system entities.
- Retrieve logs by actor, entity, and action.

### Analytics and Dashboard
- Student statistics.
- Bus utilization.
- Route statistics.
- Attendance analytics.
- Zone-wise student distribution.

### Data Export
- Export students as CSV.
- Export assignments as CSV.
- Export attendance as CSV.
- Export dataset as JSON.
- Export dataset as SQL.

## 6. Database Configuration

Create a MySQL database:

```sql
CREATE DATABASE student_transport_synthetic_db;
```

Configure the database connection using environment variables in a `.env` file:

```env
DATABASE_URL=mysql+pymysql://username:password@localhost:3306/student_transport_synthetic_db

RANDOM_SEED=20261022

DATA_YEAR=2026
```

Replace the username and password with your own MySQL credentials.

**Important:** Never upload your actual `.env` file or database credentials to GitHub.

## 7. Installation and Setup

### Step 1: Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
```

### Step 2: Navigate to the project directory

```bash
cd student_transport_system
```

### Step 3: Create a virtual environment

```bash
python -m venv venv
```

### Step 4: Activate the virtual environment

Windows:

```bash
venv\Scripts\activate
```

Linux / macOS:

```bash
source venv/bin/activate
```

### Step 5: Install dependencies

```bash
pip install -r requirements.txt
```

### Step 6: Configure environment variables

Create a `.env` file in the project root and configure the MySQL database connection.

### Step 7: Run the application

```bash
uvicorn app.main:app --reload
```

The application will run at:

```text
http://127.0.0.1:8000
```

## 8. API Documentation

FastAPI provides interactive API documentation through Swagger UI.

Open the following URL after starting the application:

```text
http://127.0.0.1:8000/docs
```

Alternative API documentation:

```text
http://127.0.0.1:8000/redoc
```

## 9. Synthetic Dataset Generation

The project includes a synthetic dataset generator for creating transportation data for testing and analysis.

The generated dataset includes:

| Entity | Generated Records |
|---|---:|
| Zones | 10 |
| Buses | 100 |
| Drivers | 100 |
| Stops | 300 |
| Routes | 100 |
| Route Runs | 100 |
| Students | 5,000 |
| Guardians | 5,000 |
| Assignments | 5,000 |
| Attendance | 5,000 |

The generator uses a configurable random seed to support reproducible dataset generation.

## 10. Data Validation

The dataset validation module checks:

- Expected record counts.
- Duplicate active student assignments.
- Bus capacity violations.
- Accessibility constraints.
- Route-stop assignment validity.
- Stop approval status.
- Zone compatibility.
- Pickup time window violations.
- Route-run bus and driver consistency.
- Attendance and assignment consistency.

Run the validation module using:

```bash
python -m app.generators.validate_dataset
```

## 11. Testing

The project uses Pytest for API testing.

Run all test cases:

```bash
python -m pytest -v
```

Run an individual test module:

```bash
python -m pytest tests/test_students.py -v
```

The test suite covers API functionality, input validation, database operations, error handling, and business rules.

## 12. Assignment Optimization

The optimization module generates suitable student transportation assignment proposals.

It considers:

- Zone compatibility.
- Pickup time window suitability.
- Bus capacity.
- Accessibility requirements.
- Route and stop availability.
- Load balancing.

The optimizer generates proposals without modifying the baseline dataset.

## 13. Future Enhancements

- Real-time GPS tracking of school buses.
- Live route monitoring.
- Automated guardian SMS notifications.
- Geographic distance-based route optimization.
- Role-based authentication and authorization.
- Interactive transportation dashboard.
- Cloud deployment and monitoring.

## 14. Conclusion

YottaFlex provides a structured backend solution for managing student transportation operations. It combines transportation management APIs, assignment optimization, attendance tracking, analytics, synthetic data generation, and automated testing into a single system.

The project is designed to support efficient transportation planning, improved operational visibility, and better student transportation management.

---

**Project:** YottaFlex – Student Transportation Management System  
**Backend:** FastAPI  
**Database:** MySQL  
**ORM:** SQLAlchemy 2.0  
**Testing:** Pytest
