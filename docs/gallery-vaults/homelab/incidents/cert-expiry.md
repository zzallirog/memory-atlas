---
name: cert-expiry
description: Wildcard cert silently expired; renewal cron had been failing for 60 days.
tags: [sev-2]
---
The [[wildcard-cert]] lapsed and [[reverse-proxy]] served warnings for a day.
Alert on renewal FAILURE, not on expiry. See [[postmortem-template]].
