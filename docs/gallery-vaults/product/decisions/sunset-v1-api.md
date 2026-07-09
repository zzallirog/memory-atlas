---
name: sunset-v1-api
description: Retired the v1 API in June 2025 after 18 months of parallel maintenance with v2.
type: decision
tags: [q2]
---
v1 still carried 9% of integration traffic, mostly [[google-calendar-sync]]
webhooks nobody had migrated. Killing it unblocked [[eu-data-residency]] region
tagging, which v1's schema had no field for. [[reporting-dashboard]] now shows
only v2 call volume.
