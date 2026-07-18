---
name: timezone-handling
description: Rebuilt time zone handling shipped Jan 2025 after cross-region bookings landed on the wrong hour.
type: spec
tags: [q1]
---
Bookings now store the client's zone explicitly instead of inferring it from
IP. [[clinic-front-desk]] had telehealth appointments land an hour off before
the fix, and [[tutoring-agency]] hit the same bug across a three-zone tutor
roster. It shares booking-time logic with [[google-calendar-sync]].
