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
memory-atlas --self-test     # 27 unittest cases
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

- **2.3.0** (2026-07-09) — continuous LOD + lenses. Zoom is one continuous ramp instead of 4 discrete stages: label pills fade out in counter-phase as tile cards fade in (`TILE_W` crossfade window, own-card collision exempted), desc preview arrives earlier (`DESC_K` 4.5→3.0) and *grows into* the card (`descT` lerps card height + line alpha). Ego-blur background tamed: screen-radius cap + zoom fade (no more giant blurred blobs at close zoom). Blur perf: the muted background renders at **half CSS resolution** before the blur filter (~16× fewer pixels on dpr2 — fixes the ego-blur fps drop on Linux/Retina). Ego focus now shows *what's in the neighbors*: 2-line desc under each sharp neighbor, 3 under selected. **Temporal lens «ровесники»** — temporal proximity served through the lens engine instead of a 1600-edge layer: ⌚ in the node panel keeps same-time-window notes sharp, rest dissolves; click again widens 2→7→30d. Node panel: link rows carry 1-line desc previews of the target + relevance sort (ghosts last, degree first), new "nearby · detectors" section with kind+score, body-text snippet (tooltip too). Tag suggest/datalist now covers corpus frontmatter tags, not just own LS tags. Local usage telemetry (opens + transitions, localStorage) → `usage` color mode + open-count in panel. Editors: vscodium/zed/subl/obsidian + custom URL-scheme template (Linux xdg-handler friendly). Lens pill recentered (CSS zoom was shifting it), chips animate in.
- **2.2.0** (2026-07-08→09) — tag-lens ("blur + emptiness"), hover-preview cards, HUD bar-blocks, W2 generator portability (Obsidian vaults), W3 adaptive readability, EN i18n layer + RU/EN toggle, installer zipapp `.pyz` + synthetic demo vault.
- **2.1.0** (2026-07-08) — label declutter + axis decouple + perf. Greedy label collision culling by priority (selected > pin > hover > search > degree; losers are *not drawn* — kills the grid@zoom label smear), always-on backing plates for every drawn label, `lbl ρ` density slider = label-budget axis independent of spatial zoom (zoom auto-raises the budget, slider multiplies), tile cards get the same greedy declutter (losers fall back to dots), grid pitch 56→76 / zones dynamic column pitch + middle-ellipsis of long ids to the layout pitch. Perf: ego-blur background cached to an offscreen canvas (8.3ms → 0.6ms per drag frame; the per-frame repaint+blur re-raster was the 60→10fps drag lag). Context-aware `fit` (frames search/filter/pins/ego; ⌂/h = whole graph). Animation polish: labels fade in/out, tile↔dot crossfade on the LOD boundary, blur focus eases in.
- **2.0.0** (2026-07-08) — prod. Flexibility: 9 layouts (force/semantic/pack/ring/petals/radial/grid/zones/timeline), 7 task-presets, server-less regen-admin (⚙). Usability: clickable canvas labels + tile cards (`pick()` hit-tests drawn label rects, not just the dot), center declutter (degree-charge + auto-edge-α + free-space fit), crisp screen-space label render, spring magnet. First versioned + git-tracked release.
