---
name: cert-manager
description: ACME client that renews the wildcard cert and pushes it to the reverse proxy.
tags: [tier-edge]
---
Renews the [[wildcard-cert]] monthly, well ahead of the 90-day expiry, and
ships it to [[reverse-proxy]]; [[auth-proxy]] depends on the same chain.
Missed-alert gap closed after [[monitoring-alerts-audit]].
