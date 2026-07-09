---
name: slack-integration-bet
description: Bet a full sprint on Slack notifications despite only 6% of interviews requesting it.
type: decision
tags: [q2]
---
[[coworking-space-manager]] runs three properties from a shared Slack channel
and wanted booking pings there. We built it on top of [[team-schedules]] rather
than a standalone webhook. The integration only became possible once
[[sunset-v1-api]] retired the old event format.
