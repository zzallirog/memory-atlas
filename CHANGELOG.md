# Changelog

## 2.12.0

**Trilingual UI (RU · EN · UK).** Ukrainian joins the interface. The bar's language
button now cycles RU → EN → UK (reload-on-switch, settings survive).

- **`i18nUK` dictionary.** Every UI string, hint, toast and legend carries a Ukrainian
  translation — 326 keys, at parity with the EN overlay. RU stays the canonical markup;
  EN and UK are dictionary overlays applied on load.
- **3-way language button.** The bar button shows the next language and advances
  RU → EN → UK; the 10s idle auto-hide is unchanged.

## 2.11.2

Two fixes surfaced by Daniel ([n0mad-ai](https://github.com/n0mad-ai)) running the
atlas on a large external vault 🍺

- **Ghost detector ignores wikilinks inside code spans.** `[[links]]` written as
  syntax examples in fenced or inline code — notes that document the wikilink
  convention itself — no longer register as dangling ghosts.
- **`EMB_MODEL` is configurable via `$ATLAS_EMB_MODEL`.** A box running a different
  embedder (e.g. `embeddinggemma`) no longer 404s `/api/embed` and silently degrades
  to structural-only — set the env var and the semantic layer comes back.

## 2.11.0

**Fast at every frame, readable at every scale.** Two passes over the v2.10 reading
views after they met a real vault (1341 notes / 6.5k edges / 410 louvain topics).

### Performance (v2.10.1–v2.10.5)

Profiled, not guessed — CDP profiles, canvas-call counters, A/B on the same DATA
(harness now in `perf/`):

- Per-node text-layout memos under numeric stamps: building and hashing cache keys
  that embedded the full note body was ~55% of pan JS at card zoom.
- Card bodies render as content-keyed offscreen sprites (one `drawImage`), the
  `bodySnip` regex pass is cached — a measured 46ms JS cliff at the card threshold
  is gone.
- Edges stroke as per-style `Path2D` buckets; the blur background delta-blits a
  cached raster (panning under focus no longer re-rasters the whole muted graph).
- Ego-focus neighbors are plate chips (bodies on demand), not bare text lines.
- Data budget scales with viewport area / text-scale².
- Fixes: `#ofit`/`#langBtn` were unstyled AND click-dead (fell out of a hand-written
  CSS id list); the ego vignette was baked into the camera-tracking blur cache and
  flashed on re-raster — now screen-fixed.
- Measured (1920×1080, dpr2): draw callback 12.4→6.4ms at K=1.0, 15.8→9.4ms at
  K=2.3, 15.1→8.8ms at K=3.25; 1280×800 sits at 4-6ms across all zooms.

### Motion

- Magnet + wikilink particles ON by default at **zero idle cost**: rAF runs only
  while carriers exist, the magnet arms on cursor movement — a parked cursor burns
  nothing. Saved views carry motion state.

### Reading at scale (v2.10.6)

- **Capped group axis**: 410 topics no longer mint 410 spine headers / facet panels /
  hulls — top groups keep sections, the tail merges into one `…` group (grid 24,
  zones/dendro 18, others 12; zone/root/type/age untouched).
- **Density-LOD**: card/desc/body ramps run on `max(K, density-equivalent zoom)` from
  the node count in frame (≤16 = cards, ≤7 = full body preview) — reading distance is
  scale-free, whatever the layout inflated the world to.
- Node screen-radius floor (sub-pixel dendro-rim nodes were invisible and
  unclickable); dendro branch skeleton fills the empty disc; group titles capped in
  screen terms; ✦ orient animates as a smooth eased tween.

### Docs & bench

- `perf/` measurement harness (frame-bench matrix, focus-cell repeats, splice A/B,
  CDP pan profile) with methodology notes — including the measured anti-case where
  Path2D-bucketing circles cut canvas calls 20× and *added* 2ms.
- `docs/VIEWS.md`: "Reading at any scale" section + new shot.

## 2.10.0

**Reading, not just navigating.** The complaint this release answers: *"I can see the
graph, but I can't read my files."*

- **GROUP BY axis.** A new `group` select slices every grouping layout — `pack · ring ·
  petals · radial · grid · zones` and the three new views — by `zone / root / cluster /
  type / age`. Hull outlines, hull titles and force link distances follow the axis.
  Persists, travels in saved views and `?group=` deep links.
- **Three reading views**, where text is the first-class element:
  - `spine · list+arc` — the strongest notes of every group as a central readable list
    with section headers, the rest on a surrounding arc. Task preset **reading · list**.
  - `facets · panels` — group values as labeled perimeter mini-panels, the long tail in
    the center disc inside its group's wedge.
  - `dendro · tree` — a radial dendrogram (group ⊃ cluster ⊃ note), every leaf labeled
    outward from the rim.
- **Cards carry prose.** Node cards arrive earlier on the zoom ramp (K≥1.5) and show the
  note's own body text: word-wrapped lines, each a touch quieter, the last dissolving
  into transparency — an excerpt, not a chopped string. Ambient label budget ×2.5.
- List rows are never budget-culled (they are the reading surface); row counts are
  derived from screen physics so the fit-zoom pitch stays readable.
- New: [docs/VIEWS.md](docs/VIEWS.md) — how layouts × grouping × color compose.

## 2.9.0

**Provenance axis.** New pipeline module `memory-atlas-provenance` (the same external-
builder pattern as `--data`: the core stays kind-blind):

    memory-atlas --src ... --dump-data - | memory-atlas-provenance | memory-atlas --data - --out vault.html

- Git history → `moved_from` edges with arrowheads (ghost of the old name → the live
  note, rename chains collapse to the live end), `became` edges (same-commit
  delete+add merge/split heuristic, gated to small commits), `prov.gone` /
  `prov.archived` on ghosts whose file *used to exist* — true forgottenness vs
  never-written.
- Session touches → `usage`, `last_touch_days`, and a `forgotten ∈ [0,1]` metric per
  note (recency × engagement, mtime fallback).
- DATA CONTRACT v2.9: builders declare `edge_styles` (color/dash/arrow per kind) and
  `node_metrics` — the template renders styles, colorMode options and a threshold lens
  (legend click: *forgotten ≥ 0.6*) from data alone.
- Node panel gains a provenance block (renamed from/to, deleted, archived); ghost chips
  distinguish "never written" from "existed — deleted/archived".

## 2.8.0

- **Multi-root vaults**: repeatable `--src [name=]dir` — memory + wiki + snippets in one
  graph, cross-root wikilink resolve, per-root zone namespaces.
- `--dump-data -` — pure DATA JSON on stdout, the source end of the pipeline for
  external builders.
- `temporal_proximity` capped to each node's top-2 partners (was: n² haze on
  co-edited corpora).

## 2.7.0

- Edges off by default — the full connected-link overview tanked FPS; the layer is one
  keystroke (`9`) away.
- Earned zone-overlap on spatial layouts: petals converge where cross-zone bridges
  exist, colours mix in OKLab.

## 2.6.0

**Petals.** Zone hulls are now drawn as petals: a smooth closed curve with a radial
gradient fill (airy center, tinted rim) — the zone reads as a shape, not a wireframe
polygon. The `ring` layout, which used to skip hulls entirely (a convex hull would chord
straight across the center), now draws each zone as an **annular arc band** along its
stretch of the ring. The `petals` layout got the same care: zones are anchored on a
circle sized from the fattest petal, so the whole vault reads as one flower instead of
clumps in the corners.

**Layouts breathe with corpus size.** The ring radius adapts to the number of notes —
a small vault gets a compact ring instead of a handful of nodes flung to the viewport
edges, a dense one gets a thicker multi-row band instead of one overcrowded rim.
Grid/zones shelves widen their pitch on small corpora, so names survive without the
mid-ellipsis. The fit knows ring labels sit outside the ring and pads for them.

**Particles on wikilinks.** Flowing particles now ride plain `[[wikilinks]]` too, not
just detector edges — and since a wikilink is directed, the flow shows *who references
whom*. Dense corpora are deterministically subsampled (the old behavior silently killed
the whole layer past 600 edges).

**Your setup survives a reload.** Magnet and particles now restore with the rest of the
config by default (opt-out in settings if you prefer motion off at boot). A built-in
`⭐ standard · alive` view brings any corpus to the lively default in one click, and
saved views now carry their motion state. `zone` is the default color mode.

**Gallery, actually alive.** The five example vaults grew from 6-8 stub notes to 32-44
real ones (a smuggler-coast TTRPG campaign, a homelab with postmortems, six months of
reading, an Italian course, a Japan trip) with designed ghosts, tag overlaps and hubs —
the screenshots now look like a lived-in vault, and every one is still rebuildable from
the repo. New flagship shot: the campaign as a flower, `?layout=petals`.

**Cut:**
- The Louvain blob layer (soft cluster hulls) — it glitched over dense zones. Cluster
  data stays: `pack` layout and `color: cluster` still work.
- The petal rim glow (`shadowBlur`) shipped in early builds — it was the real drag/zoom
  fps cost, so the petals ship with the gradient fill only.

## 2.5.0

**✦ orient** — a new camera-group button. It rigidly rotates the current layout to
the angle whose bounding box best fills the viewport, so links don't fly off-screen and
the graph sits in-frame. Rotation is an isometry: `ring` stays `ring`, every layout's
non-crossings and intrinsic structure are preserved; only the orientation changes. The
button reports the real fill it achieved (base → best) — no cosmetic claim.

**Example gallery** — five runnable example vaults (campaign, homelab, italian, reading,
trip) with screenshots, so you can see the detectors and layouts on real-shaped notes
before pointing the tool at your own vault.

Also folds in the prior refine pass: `--data` accepts a ready-made graph JSON, the
session detector handles vaults living in a repo subdirectory (`--relative`), localized
preset toasts, a template/generator version handshake, and assorted layout fixes.

## 2.4.1

Refine pass: `--data` contract validator (broken external graphs fail at build time, not
as a dead page); session detector fixed for vaults living in a subdir of a git repo
(`git log --relative`); `--demo` also mutes the session detector (packaging commits ≠
sessions); preset toasts translate in EN mode; generator↔template version handshake
(`atlas-tpl` meta, warns on stale symlink pair); `maxN` "all" persists as a sentinel (a
grown corpus no longer comes back silently top-N-filtered); client semantic search honors
`ATLAS_OLLAMA`; `.pyz` compressed (590K → 195K); dead edge-hover code removed.

## 2.4.0

Public-release pass: EN comments/CLI, generic path autodetect, Windows toolchain + CI
matrix, locale-auto UI language, pin cards with preview + view capture.

## 2.3.0

Continuous zoom LOD, temporal lens, ego-blur at half resolution (fps), panel link
previews, usage telemetry, editor URL-schemes.

## 2.2.0

Tag-lens ("blur + emptiness"), hover-preview cards, HUD bar-blocks, generator portability
for Obsidian vaults, adaptive readability, EN i18n layer + RU/EN toggle, installer zipapp
+ synthetic demo vault.

## 2.1.0

Label declutter + density axis, ego-blur cache (60→10fps drag lag fixed), context-aware
fit.

## 2.0.0

First versioned release: 9 layouts, task presets, server-less regen admin.
