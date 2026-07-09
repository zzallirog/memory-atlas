---
name: monitoring-blind-spot
description: Alert routing broke after a dashboard migration; nothing paged for three weeks.
tags: [sev-2]
---
[[monitoring-stack]] kept collecting metrics fine, but the notification
channel pointed at a decommissioned [[container-host]]. Same silent-failure
pattern as [[dns-outage]]; findings filed in [[monitoring-alerts-audit]].
