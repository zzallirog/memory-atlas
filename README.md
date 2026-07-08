# memory-atlas

Self-contained interactive graph of the memory layer — one HTML file, no server, no LLM at render time.

- `memory-atlas` — Python3 stdlib generator. Scans a memory dir (frontmatter + `[[wikilinks]]`), runs cross-zone detectors, inlines everything into a D3-canvas template.
- `memory-atlas.template.html` — 2D canvas render (glass HUD, Louvain clusters, 9 layouts, task-presets, regen-admin). Must sit next to the generator (`realpath(__file__)` resolution — symlink-safe).

## Run

```
memory-atlas                 # scan default memory dir → open ~/.mac-claw/atlas/memory-atlas.html
memory-atlas --no-open       # rebuild without launching a browser
memory-atlas --src DIR --out FILE
memory-atlas --data graph.json|-   # render an arbitrary graph (see DATA CONTRACT in generator docstring)
memory-atlas --self-test     # 25 unittest cases
memory-atlas --version
```

Deployed to `~/bin` as symlinks (both files) so the command is on PATH while the repo stays the single source of truth.

## Backup / sync

Not in Syncthing (`~/bin` and this dir are not shared folders). Durable off-machine channel = git push to the Arch bare:

```
git push arch main           # arch:backups/memory-atlas.git (bare) — reachable, off-machine
```

Gitea (Arch loopback:81) intentionally skipped — redundant per backup-topology note.

## Version

`VERSION` constant lives in `memory-atlas` (surfaced in the HUD footer and `--version`).

- **2.0.0** (2026-07-08) — prod. Flexibility: 9 layouts (force/semantic/pack/ring/petals/radial/grid/zones/timeline), 7 task-presets, server-less regen-admin (⚙). Usability: clickable canvas labels + tile cards (`pick()` hit-tests drawn label rects, not just the dot), center declutter (degree-charge + auto-edge-α + free-space fit), crisp screen-space label render, spring magnet. First versioned + git-tracked release.
