# Changelog

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
