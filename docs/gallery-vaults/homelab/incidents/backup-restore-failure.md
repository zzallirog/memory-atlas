---
name: backup-restore-failure
description: Weekly restore drill failed silently for a month before anyone noticed.
tags: [tier-storage]
---
[[backups]] jobs reported green while the restore step over [[switch-stack]]
was quietly erroring against the offsite copy. Drill script now checked into
the missing [[disaster-recovery-plan]].
