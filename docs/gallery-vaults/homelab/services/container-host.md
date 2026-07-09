---
name: container-host
description: Docker host running everything that isn't the NAS or the router.
tags: [tier-core]
---
Volumes live on [[nas-pool]]; metrics feed [[monitoring-stack]]. Runs
[[game-server]] and the rest of the stack; asset details tracked in
[[hardware-inventory]].
