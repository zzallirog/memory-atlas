---
name: photo-server-corruption
description: A bad restore left the photo index half-migrated; thumbnails pointed at missing files.
tags: [tier-app]
---
[[photo-server]] database was restored from a [[nas-pool]] snapshot taken
mid-reindex. Rebuilt from scratch per the missing [[disaster-recovery-plan]].
