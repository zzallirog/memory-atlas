---
name: firewall-rules
description: Inbound/outbound ACLs enforced on the edge-router.
tags: [tier-edge]
---
Default-deny inbound; only [[reverse-proxy]] and [[wireguard-vpn]] get a
forward rule. Lives on [[edge-router]], audited alongside
[[port-forward-table]].
