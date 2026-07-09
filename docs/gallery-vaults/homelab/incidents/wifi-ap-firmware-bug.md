---
name: wifi-ap-firmware-bug
description: Auto-update pushed a firmware build that dropped 5GHz clients every few hours.
tags: [sev-3]
---
[[wifi-ap]] radios reset silently; [[home-assistant]] sensors looked
"offline" after falling back to 2.4GHz and timing out. Auto-update disabled
after.
