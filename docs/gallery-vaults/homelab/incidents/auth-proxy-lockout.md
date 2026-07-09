---
name: auth-proxy-lockout
description: Expired intermediate cert broke SSO for every service behind it at once.
tags: [security]
---
[[auth-proxy]] rejected every session after [[cert-manager]] renewed the leaf
but not the intermediate. Same blind spot as [[cert-expiry]] wearing a
different certificate.
