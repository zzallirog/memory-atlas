---
name: google-calendar-sync
description: Two-way Google Calendar sync launched as part of the reordered onboarding flow.
type: spec
tags: [q1]
---
It syncs both directions within 30 seconds and cleans up declined events
automatically. It moved earlier in onboarding per [[calendar-first-onboarding]],
and the webhook format only worked once [[sunset-v1-api]] retired the legacy
event schema. [[tutoring-agency]] uses it to push sessions to each tutor's
personal calendar.
