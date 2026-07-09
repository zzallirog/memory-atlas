---
name: dns-server
description: Local resolver and ad-blocker for every VLAN except guest.
tags: [tier-core]
---
Split-horizon for internal names, forwards everything else upstream. Runs on
the same [[container-host]] as everything else; time sync leans on
[[ntp-server]]. Restarts scheduled under [[maintenance-window-policy]].
