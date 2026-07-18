---
name: dns-outage
description: Resolver crashed under a malformed blocklist update; nothing on the LAN could resolve names.
tags: [sev-2]
---
[[dns-server]] wedged after a bad blocklist pull; every VLAN in [[vlan-map]]
lost resolution simultaneously. Third case for the [[postmortem-template]].
