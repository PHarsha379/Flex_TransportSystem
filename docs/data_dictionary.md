# Data Dictionary (starter)

See `app/models/entities.py` for the initial SQLAlchemy field definitions.

| Entity | Primary key | Main relationships |
|---|---|---|
| AddressZone | zone_id | 1:N Student, 1:N Stop |
| Student | student_id | 1:N GuardianContact, 1:N Assignment, 1:N AttendanceEvent |
| GuardianContact | guardian_id | N:1 Student, 1:N Notification |
| Stop | stop_id | N:1 AddressZone, 1:N RouteStop, 1:N Assignment |
| Bus | bus_id | 1:N Route, 1:N RouteRun, 1:N BusCapacityHistory |
| Driver | driver_id | 1:N Route, 1:N RouteRun |
| Route | route_id | N:1 Bus, N:1 Driver, 1:N RouteStop, 1:N Assignment |
| RouteStop | route_stop_id | N:1 Route, N:1 Stop |
| Assignment | assignment_id | N:1 Student, N:1 Route, N:1 Stop, 1:N AttendanceEvent |
| AttendanceEvent | attendance_id | N:1 Student, N:1 Assignment |
| Notification | notification_id | N:1 GuardianContact, N:1 Student |
| RouteRun | run_id | N:1 Route, N:1 Bus, N:1 Driver |
