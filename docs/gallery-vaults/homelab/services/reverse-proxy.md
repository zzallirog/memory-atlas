---
name: reverse-proxy
description: Single ingress for every internal service; TLS terminates here.
tags: [tier-edge]
---
Routes by hostname to everything behind it. Depends on [[edge-router]] port
forwards and the [[wildcard-cert]].
