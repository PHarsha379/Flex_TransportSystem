# Business Rules

1. Only active students can receive active assignments.
2. Only approved, active stops can be used for valid assignments.
3. A student's accessibility requirement must be met by the assigned vehicle.
4. Occupancy must not exceed the capacity effective for the route run date.
5. The assigned stop must be part of the assigned route.
6. Pickup arrival must fall within the student's configured pickup window.
7. A route sequence must have feasible travel times between consecutive stops.
8. Attendance events are append-only and unique per student, date, and assignment.
9. Notifications use synthetic guardian contacts and record delivery outcomes.
10. Changes to assignments, bus capacity, and route status must preserve history.
11. Ground-truth labels are stored separately from input datasets.
12. Unapproved addresses must not be exposed in operational outputs.
