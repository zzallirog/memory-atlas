---
name: ntp-server
description: Local time source; keeps cert validation and logs sane.
tags: [tier-core]
---
Keeps [[cert-manager]] validation and every [[container-host]] log timestamp
sane. Patches only land inside [[maintenance-window-policy]] hours.
