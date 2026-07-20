# memory-atlas

[![ci](https://github.com/zzallirog/memory-atlas/actions/workflows/ci.yml/badge.svg)](https://github.com/zzallirog/memory-atlas/actions/workflows/ci.yml)

Turn a folder of markdown notes into **one self-contained interactive graph** — a single HTML file. No server, no build step, no cloud: Python 3 stdlib in, `file://` page out.

The point isn't "a graph of my wikilinks". It's **overlap**: the generator runs a set of detectors that surface links you never wrote by hand — a missing note two clusters both reference, overlapping tags, notes edited in the same sitting — and draws them on top of your explicit `[[wikilinks]]`.

![overview — four topic zones on a synergy ring, cross-zone bridges through the middle](docs/shots/overview.png)

*The built-in demo vault — chemistry, cooking, gardening, music — on the zone-synergy ring. Solid lines are `[[wikilinks]]` somebody typed. The dashed one crossing from the cooking arc to the chemistry arc is not: nobody wrote a note called `maillard-reaction`, but `searing-steak` in `cooking/` and `amino-acids` in `chemistry/` both cite it, and that shared gap is a bridge the `shared_ref` detector drew. (Edges start hidden in the real page — press `9` or the EDGES chip. Lines are noise until you ask for them.)*

## Quick start

```bash
git clone https://github.com/zzallirog/memory-atlas && cd memory-atlas
./memory-atlas --demo            # tiny synthetic vault, opens in your browser
./memory-atlas --src ~/my-vault  # your own notes
./memory-atlas --src ~/vault --src ~/wiki --src ~/snippets   # several roots, one graph
```

`--src` is repeatable: the first root keeps its index-based zones, every extra root becomes
one zone of its own, and `[[links]]` resolve same-root first, then across roots — a link that
used to dangle as a ghost snaps to the real note in the other root. `--dump-data -` emits the
graph JSON instead of rendering (the source end for external pipeline builders).

Or pack it into a single file you can carry around — one `.pyz`, no repo:

```bash
python3 installer/build_pyz.py     # → dist/memory-atlas.pyz (stdlib, ~200K)
python3 dist/memory-atlas.pyz --demo
python3 dist/memory-atlas.pyz --src ~/my-vault
```

On **Windows** the same two routes work — the generator is stdlib Python and the output opens via the default browser:

```powershell
py memory-atlas --demo
py dist\memory-atlas.pyz --src C:\Users\you\vault
```

Requirements: **Python 3.8+ and a browser.** That's the whole list. macOS, Linux and Windows are exercised in CI (self-test + demo build + `.pyz` build on all three). Obsidian vaults work out of the box (`.obsidian/`, `.trash/` skipped, frontmatter `tags:` read). Each top-level folder becomes a colored zone.

Full walkthrough: [docs/QUICKSTART.md](docs/QUICKSTART.md). More lives of the same tool — a worldbuilding campaign, a homelab runbook, reading notes, language study, trip planning — in the **[gallery](docs/GALLERY.md)**, each with a runnable example vault. How layouts, the **grouping axis** and the reading views compose: [docs/VIEWS.md](docs/VIEWS.md).

## What you get

![node focus — a ghost note referenced from two different zones](docs/shots/node-focus.png)

*Select a node and the rest blurs back. Here the selected node is `fermentation` — a **ghost** (no file), yet referenced from `composting` in the garden folder and `sourdough` in the kitchen folder. Two zones quietly leaning on the same un-written note is exactly the overlap the tool exists to surface.*

- **Overlap detectors** (build-time, all local): shared missing references (`shared_ref`), tag overlap (Jaccard), temporal co-editing, git co-commits, and — optionally, if you run [Ollama](https://ollama.com) — semantic similarity by embeddings. Without Ollama the generator prints one warning and carries on; every other bridge still works.
- **13 layouts** (force / semantic / pack / ring / petals / radial / grid / zones / timeline / spine / facets / dendro / matrix), morph animated, `[` `]` to cycle; task presets that set layout+color+layers in one pick. Two of them are data-gated and remove themselves rather than sit dead: `semantic` needs embeddings in the page, `timeline` needs dates.
- **Lenses instead of hairballs**: click a tag — only tagged notes stay sharp, the rest dissolves into blur. Same engine drives the ⌚ *temporal lens*: pick a note, see everything edited in the same time window (2→7→30 days). Detector edges are hidden by default and served through lenses — lines are noise until you ask.
- **Read in place**: hover previews, description snippets under neighbors when a note is focused, a full **browse** tab (three-pane reader over the same data), and a **dash** tab (zones, freshness, ghost debts, data health).
- **Continuous zoom LOD**: dots → labels → cards with description previews, one smooth ramp.
- **Local usage telemetry** (localStorage only): a `usage` color mode shows which notes *you* actually open.
- **UI in English or Russian** — RU/EN toggle in the bottom bar, choice persists.
- Pins, saved views, deep links (`?state=`), user-drawn edges, zone overrides, profile export/import — all persisted in your browser, exportable as one JSON.

## Privacy

Everything runs on your machine and the output is a static local page. The generated HTML **embeds note titles, descriptions and body text** — treat the built file like the vault itself: regenerate for others, don't reshare yours. The demo vault is synthetic.

The page also stamps **who built it**: the machine's hostname and the absolute path of the vault, shown in the footer, the browse header and the dash. That is useful for yourself — two hosts, two atlases, and you can tell which is which — and it is exactly what you do not want in a file you hand to someone else or drop into a bug report. Build those with **`--anon`**: no hostname, and the source reads as the vault's folder name instead of `/home/yourname/…`. (Anonymising drops editor-open for that file, which resolves note paths against the real root.) Every screenshot in this repo is built that way.

## Zones — your names, not ours

A zone is a coloured region of the map. By default every top-level folder in your vault
becomes one, laid out on a circle — nothing to configure.

If you want particular projects to be zones with a fixed place on the map (so the layout
stays put as the vault grows), declare them yourself. Drop `.atlas-zones.json` in the vault
root, or point `$ATLAS_ZONES` at one:

```json
{
  "folders": ["research", "journal", "clients"],
  "anchors": { "research": [-0.1, -0.75], "journal": [0.65, 0.65] }
}
```

- `folders` — top-level folders that become zones of their own.
- `anchors` — where each sits, in `[-1..1]` coordinates (`[0,0]` is the centre). Optional;
  anything you leave out is placed automatically.

Three ways to end up with a useful set of zones, in increasing order of effort:

1. **Do nothing.** Folders are zones. For most vaults this is the whole answer.
2. **Write the file by hand** once you know which projects you want pinned where.
3. **Let a model draft it.** Point any LLM you already use at your folder listing and ask
   for a `.atlas-zones.json` grouping them into 5–8 zones. It is a small, checkable file —
   read it before you keep it, and move an anchor if a zone sits somewhere you dislike.

If a vault has no structure worth pinning yet, that is a normal state: build the atlas
first, look at what clusters, and write the zones afterwards.

## Honest scope

- Built first for the author's own memory corpus; foreign-vault support (Obsidian layouts, arbitrary zones) is tested on synthetic and real vaults but younger than the core.
- Up to 8 zones get distinct colors; more fall into a shared grey.
- The `semantic` layout uses PCA over embeddings — honest cosine geometry, weaker separation than UMAP would give.
- Rendering is 2D canvas, comfortable at a few hundred notes; thousands untested.

## Layout of this repo

```
memory-atlas                  # generator (Python 3 stdlib, single file)
memory-atlas.template.html    # D3-canvas render template (must sit next to the generator)
vendor/d3.v7.min.js           # D3 v7 (ISC license), inlined into the output
demo/                         # synthetic two-zone demo vault
installer/build-pyz.sh        # packs everything into dist/memory-atlas.pyz
dist/memory-atlas.pyz         # prebuilt single-file bundle
docs/QUICKSTART.md            # the friendly walkthrough
docs/EVAL.md                  # what search costs per corpus, and how it was measured
tools/anno-blocks.py          # block anchors + the call graph between them (see below)
tests-search.py               # search behaviour, asserted in a real browser
perf/                         # benches: render frametime, and search cost per corpus
```

### Reading a 7k-line single file

The template is one file with ~260 top-level definitions. Every section carries an anchor in
its header — `// ── [A:bridges] bridges · betweenness ranking, lens and card` — and the header
under it states, computed from the code and not asserted by hand, what the block defines, what
it calls across block boundaries, and who calls it. Prose written by a human is preserved; only
those computed lines are regenerated.

```sh
python3 tools/anno-blocks.py list          # every anchor, its title and current line
python3 tools/anno-blocks.py show bridges  # one block: where it is NOW, what it touches
python3 tools/anno-blocks.py sync          # rewrite the computed header lines
python3 tools/anno-blocks.py check         # fail if a header names something nothing defines
python3 tools/anno-blocks.py scan          # refresh the local navigation snapshot
```

The anchor is the key, never the line number: positions are resolved by searching the file at
the moment you ask, so inserting code above a block does not turn an old pointer into a wrong
one. `--self-test` asserts anchors stay unique and that no separator is left unanchored.

`./memory-atlas --self-test` runs the built-in test suite — generator side only. It does not
execute a line of the page's JavaScript, so `python3 tests-search.py` is the other half: it
drives a headless browser and asserts the search behaviour that actually ships. Press `?` inside the atlas for every key and edge type.

## Development

- `dist/` is a build artifact (`python3 installer/build_pyz.py`) and is gitignored — build it when you want the single-file bundle.
- `tools/shoot-gallery.mjs` re-shoots every frame in the README and the gallery from the example vaults (`node tools/shoot-gallery.mjs [case…]`, needs Playwright and a local Chrome). The frames carry the version stamp and the whole HUD, so they go stale on their own — re-shoot them when the interface moves, not by hand.
- Deployed locally as `~/bin` symlinks (generator + template travel as a PAIR — the generator warns on version skew).
- Durable off-machine backup channel: `git push origin main` (bare repo); Gitea intentionally skipped per backup topology.
- CI (`.github/workflows/ci.yml`): ubuntu/macos/windows × py3.8/3.12 — self-test + demo build + `.pyz` build.

## Changelog

- **2.25.0** (2026-07-21) — **the ranking that degree cannot give you, and a file you can point at.** Every ranking in the atlas answered "how much hangs off this note". None answered "does the corpus route THROUGH it" — and those are different notes: on a real vault the top bridge turned out to be a glossary term with three outbound links, while the fattest hubs bridged nothing. The generator now computes **betweenness** (Brandes, exact below 700 notes, Brandes–Pich sampled above it with the estimate stated in the card rather than hidden), and ships it twice on purpose: `btw` normalised the standard way, comparable between corpora and printed next to degree; `bridge`, the same number rescaled to this corpus' maximum, which is what a `[0,1]` ramp and a "top decile" lens can actually use — an absolute cutoff means different things in a 400-note and a 1400-note vault. The panel gained an **ego star**: a list of neighbours is a set, and a set cannot show that four of them are neighbours of each other, which is the whole difference between a note inside a clique and a note holding two halves together. **Bookmarks** are deliberately not pins — a pin carries a captured view and a context payload, a bookmark carries "come back here" — and **Obsidian** stopped being one of eight mutually exclusive editor presets, because opening a note in your vault app and opening it in an editor are different verbs (its URI is now percent-encoded, which matters the moment a note is called `Здібності.md`). The **reader** grew into four columns — hierarchy · list · body · links — each foldable except the body, with the ego star and the Jaccard rail reusing the graph's own functions rather than a second implementation that would drift on the first edit. Every HUD section header is now its own switch, folded state persisted per corpus. **The file itself became navigable**: 74 blocks carry `[A:slug]` anchors, `tools/anno-blocks.py` computes the call graph between them into the headers, and the anchor — not a line number — is the pointer, resolved live so it cannot go stale. Two things found on the way and fixed: a raw NUL byte in the template made `grep` and `ripgrep` classify the whole file as binary and silently refuse to search it, and `--explain-io` now prints the entire read/write surface in one command, with the vault's read-only status pinned by a test that diffs every file's bytes and mtime across a full build rather than promised in a paragraph.

- **2.21.0** (2026-07-20) — **a release about motion, and one number that says why.** Three animations in this page set their speed by the frame RATE rather than by time, and each one was found by measuring rather than by watching. The **layout morph** was not dropping frames at all (p50 16.7ms over 11 transitions, 1566 frames) — so "it feels laggy" was never a rendering problem. What it lacked was a law: it *was* d3-force relaxation, forceX/forceY pulling at the targets while collide shoved nodes off them. It now eases on quintic smootherstep (C² at both ends — cubic only zeroes the first derivative, and that jump in acceleration is the snap you feel at the start), interpolates in POLAR coordinates about the target centroid along the shortest arc (ring → petals is geometrically a rotation, so rotate it rather than dragging the whole cloud through the middle), and staggers by starting radius. Measured on the same five transitions: frames moving *away* from the target 31/793 → **0/789**, largest single-frame step 429px → **116px**. It arrives slower (t95 ≈ 720-810ms against 190-357ms) and that is the trade, taken on purpose. The **camera** had nine call sites pinned at `.duration(450)` or `500` whatever the trip; a fixed duration does not set the speed, the distance does. Every flight now derives its duration from van Wijk & Nuij's optimal zoom path — d3 already interpolates along it, and the interpolator carries the path's length at unit velocity, which nobody was reading. Worst single-frame perceived step **2.124 → 0.427**, and durations finally track the trip (395ms for a nudge, 1060ms for a cross-corpus haul) instead of being pinned. The **label and LOD eases** were bare per-frame constants, so a fade took a fixed *number of frames*: 13 frames is half a second on a laptop and **6.5 seconds** on a machine that is struggling — a fade that gives up exactly when the machine does. They now advance on elapsed time and land in 3 frames at any throttle (`perf/ease-dt.mjs`, 512-node vault, CDP throttling 1×/6×/12×). What none of this claims: under a 12× throttle the wall-clock is no better, because the page schedules a frame roughly every 2s and an ease cannot land between frames. **New views**: `matrix` — rows are the grouping axis, columns a second one, and a cell's blob is its notes packed by phyllotaxis, so the mass you see IS the count; an empty cell is the finding. And the first tenant of the new **⚗ dev pill** (third in the HUD foot, off by default, persisted): `treemap`, where cell *area* is note count — matrix answers "where do I have nothing", treemap answers "what is most of this vault". Views behind that pill are built and not yet trusted; the pill removes and re-inserts their `<option>`, so the `[` `]` cycle, saved views and deep links follow without knowing a gate exists. A `strata` layer view was built with a real perspective camera and **reverted whole** two hours later — it looked crooked, and the revert took the camera, the orbit handlers, the fill shape and the i18n keys with it. Also: hull fills follow the layout's own geometry rather than wrapping a convex hull around everything (dendro had no fill and no group names at all), the tag legend's continuous axis gets a ramp instead of three fake categories, `trace` draws one accent route answering "how are these two connected", a contact strip shows the same corpus in three other forms beside the legend, and a preset names all four knobs instead of three. **Docs caught up with the code**: they still described the nine-layout era — there are thirteen (two of them data-gated: `semantic` needs embeddings, `timeline` needs dates), `matrix` was missing from the grouping-layout list in both the docs and the in-app hint, the group table listed five axes of seven and named the wrong default, and the four VIEWS frames had been hand-shot ten days earlier and were the last images still describing the pre-2.14 panel — they are cases in `tools/shoot-gallery.mjs` now, so they re-shoot with everything else.

- **2.20.0** (2026-07-18) — **the page stopped naming the machine that built it.** Every generated atlas stamped `platform.node()` and the absolute path of the vault into the footer, the browse header and the dash — in a file whose entire purpose is being self-contained and handed to someone. The Privacy section told you to "regenerate for others", which does not remove either. New **`--anon`**: no hostname, and the source shows as the vault's folder name rather than `/home/yourname/notes` (it trades away editor-open for that build, which resolves note paths against the real root). Found the way these things are found — re-shooting the gallery and reading `/Users/…` off my own screenshots. **The frames were describing a page that no longer exists.** The published set was shot at 2.4.1/2.6.0, before the 2.14 panel rebuild and the 2.18 HUD move, and it was shot with edges drawn — but edges have since become opt-in (they are noise until you ask), so captions like "everything routes through the matriarch" pointed at a fan of spokes that a reader following along would not see. Every frame is re-shot from the current build by **`tools/shoot-gallery.mjs`** — one taste for all thirteen (1400×900, rendered at 2× and published at 1×, English UI, edges on, pointer parked so no stray hover card, and long enough after the fit that its toast has faded), so the next release re-shoots with one command instead of by hand. The README hero now names the bridge it is pointing at: nobody wrote `maillard-reaction`, but `searing-steak` and `amino-acids` both cite it. Also: the `.pyz` "zero-clone route" told you to run `dist/memory-atlas.pyz` from a fresh clone, and `dist/` is gitignored and not in the published tree — the file was never there. It now says to build it. And the four pins strings the 2.19.0 merge left untranslated (the i18n drift-guard caught two; the other two live in `T()` calls, which that guard does not scan).

- **2.19.0** (2026-07-18) — an audit pass over the 2.18.0 fixes, and the first tests that actually run the page. **The search fix had switched the reranker off.** Restoring the two-word dropdown filled the candidate pool — and the semantic pass was gated on `sHits.length < 3`, a threshold calibrated back when that pool was empty on every two-word query. With the pool full the gate never opened again: measured in a browser, `semanticPass` was called **0 times** on a query whose pool held 6 rows. The commit that fixed recall would have quietly removed the one channel that finds a note whose words you did not type. It now runs whenever the page carries vectors, and reserves 3 of the 10 visible slots for hits only it can produce — a channel that appears solely when the other one fails is not a channel. **`--barH` was derived from a hidden element.** `v` hides the bar but not the HUD foot, and a `display: none` element reports an all-zero rect, so the variable resolved to `801px` on an `813px` viewport and put the foot's bottom edge above the top of the window — the fold pills left the screen. The value is now held when the bar is not laid out, and the observer watches the bar's children too: the measurement deliberately distrusts the container's own box, so watching only that box meant the exact case that staled the value was the case that fired no callback. **Title parking leaked both ways**: a control that rewrites its own `title` while hovered (the dice's page counter, the collisions row) un-parked itself behind the parking code's back — the OS tooltip returned on top of the hint card, and the stale string then overwrote the fresh one on exit; and leaving the document hid the card without restoring anything, so that control had no tooltip until an unrelated hover. Live rewrites now route through the stash, and every hide path tears down. Ranking: the exact-phrase boost was built from the raw query while the terms were normalised, so a double space — fast typing, or a paste — silently disabled it; coverage counted repeated terms instead of distinct ones, ranking by repetition while calling itself coverage; wrapper punctuation (quotes, brackets, sentence tails) is trimmed off token edges, so pasting a note's own title in quotes finds that note, while interior punctuation survives — the first version of that trim ate `c++` and the dashes off `--search-vecs`, which is why it is a test. The shelf's 200-cap ran over file order *before* ranking and started discarding both-term matches once OR'ed terms made most of a glossary qualify; it now cuts the ranked list. The `file://` semantic message named one cause as certain when the page cannot distinguish them — a blocked origin and a stopped daemon arrive as the same opaque error, and `OLLAMA_ORIGINS` allowing `file://` is a documented, working setup that the previous wording denied — so it names both. New: **`tests-search.py`** drives a real browser and asserts the shipped `runSearch`/`queryTerms`, because the 54-test suite that shipped 2.18.0 green executes no page JavaScript at all and could not have failed on any of this; **`perf/corpus-bench.py`** measures search cost per corpus through the page's own functions over CDP, with `perf/synth-corpus.py` for reproducible corpora and `perf/histofmt.py` rendering the result — see [`docs/EVAL.md`](docs/EVAL.md).

- **2.18.0** (2026-07-18) — a click-testing pass, driven through a real browser rather than read off the source, and the interface stops overstating what it can do. **The semantic channel now says which of four things is true** instead of degrading in silence: built and idle, computing, unreachable (Ollama not answering), or *not built into this page at all* — a page generated without `--search-vecs` carries no embedding table, so there is nothing to rerank against, and the dice is paging a substring list rather than re-sorting by meaning. It now says exactly that, and wears a dashed rim to match. When the page is served by the sidecar, that line offers a **build button**: `POST /api/regen {"vecs": true}` appends `--search-vecs` to the server's `--regen-cmd` (only if absent — pressing twice must not duplicate the flag) and reloads. On `file://` there is no button, because a static page cannot run the generator and a dead button would be worse than naming the flag. **The HUD foot left the scrollport.** As a `position: sticky` child of a scrolling panel it painted over whatever control happened to sit at the bottom, and its pills ate those clicks: reaching for the density slider silently re-folded the whole panel, the auto-hide pill's lower edge resolved to the status bar, and at 1280×720 the fold pill was completely covered — there was no mouse path left to collapse the HUD. It is now a sibling *below* the scroll area, so there is no overlap to steal from. **Ring-layout group titles stay on screen**: they were anchored in world space outside the ring and left the viewport on an ordinary scroll-to-zoom while their own nodes were still visible; they are clamped to the viewport now, and the label de-conflict nudge is bounded so it cannot walk them back out. Also: the search field coalesces keystrokes instead of running the whole pipeline per character, and a click landing inside that window no longer resolves against the previous query; hover-preview waits for the pointer to actually stop; double-clicking a result no longer closes the note it just opened; the pin card becomes visible when you pin something (`style.display = ''` cleared the inline value and fell straight back to the `#pinsCard { display: none }` rule); `Escape` leaves the browse tab, not only dash; the lens `💾` stores the search and isolate state it was showing, not a third of it; dragging across the canvas no longer paints selection artefacts over the chrome; and the search-miss log records rank within the whole pool rather than within the current dice page — the old form made its own `miss: rank > 10` unreachable, since that index never exceeded ten.

- **2.17.0** (2026-07-18) — search learns to admit it missed. Measured on a personal vault of ~2.4k notes, a link its author had written by hand made the top 10 of a search only a minority of the time — but for the large majority of those pairs the note *was* inside the candidate pool, so the ranking is the fixable part, not the retrieval. Three things follow. **The dice** (`🎲` in the search field) pages deeper into that already-computed pool instead of recomputing anything — the counter shows how deep you are. **The miss log** records what actually went wrong: the page writes every search to `localStorage` (including on `file://`, where there is no server), and posts to `/api/searchlog` when the sidecar is running, which appends a JSONL file *beside* the vault. A miss is a pick below rank 10, an abandoned query, or a dice roll. Nothing here ever writes into your vault — a link is only created when you accept one. `window.misslogExport()` downloads the log. **Hover-peek**: an auto-hidden left bar reopens when the pointer approaches the left edge, and while it is open it is raised above pinned cards. That last part is a rule, not a tweak — a transient surface must outrank a persistent one, because the persistent one is always there and would otherwise make the transient one permanently unclickable.

- **2.16.0** (2026-07-18) — the semantic layer stops guessing. Scored against hand-authored wikilinks as gold on a personal vault of ~2.4k notes (hub links excluded), recall@10 came out: `embeddinggemma` 0.171 · char-3gram tf-idf **0.169** · `bge-m3` 0.161 · `nomic-embed-text` 0.112. Three separate embedders only tie with character-trigram overlap, and the previous default lost to it — so the default is now `embeddinggemma`, `$ATLAS_EMB_FALLBACK` is tried only when the first model is not pulled on the host, and `$ATLAS_OLLAMA` may point at any machine (embed on a box with a GPU, build on a laptop). The lexical channel is now a channel: the two agree on only 58% of their top-10, so they are fused by reciprocal rank (`$ATLAS_LEXICAL_FUSE=0` to disable), which beat either alone — recall@10 0.179, recall@50 0.466, median rank 76 → 62. `--semantic-threshold` now defaults to a value calibrated from your corpus under your model instead of a fixed `0.75`: cosine scales are not comparable across embedders (that one cutoff kept ~13% of pairs under one model and 0.04% under another, i.e. changing the model silently emptied the layer). Also fixed: on a small vault the trigram channel returned nothing at all, because a document-frequency cutoff expressed as "half the corpus" threw away precisely the trigrams two notes shared.

- **2.15.0** (2026-07-18) — hiding a zone now re-places the graph. `layoutTargets()` computed every layout over `nodes.filter(n => !n.ghost)` — the whole corpus, filter or no filter — so the survivors of a hidden zone kept coordinates sized for the full set. On a vault whose bulk glossary is meant to be filtered away, the taxonomy view read as an empty canvas with a stray arc along the edge: the remaining notes were still strung around a circle drawn for the whole corpus. `fitView()` was innocent — it frames `visible()`; the coordinates were the stale part. Layouts now compute over the visible set (falling back to every non-ghost so an all-hidden view cannot divide by zero), and `toggleZone` recomputes a computed layout (`force` is left alone — it re-settles on its own). Verified on a live multi-thousand-node corpus, before/after, with the visibility state stamped into the frame.
- **2.14.0** (2026-07-18) — the hover-pin card and the right bar stop being two hand-written copies of one idea. Both now render the same blocks through shared builders (chips · actions · tags · meta · links · detector neighbours) and share one delegated click vocabulary, so a link, a tag-lens or `⧉ path` behaves the same on either surface; panel section CSS is widened with `:is(#panel, .hpcard)` and a self-test fails if a second copy of the section markup appears. What the copies had cost: the pin had no section headers, rendered detector neighbours as an unlabelled count histogram, and its tag chips did not open the lens. Fixed alongside, each reproduced live first: `✕` never closed a pin (raising the card re-appended it to the DOM, which cancels the pending click); overlapping pins swallowed each other's controls (raise is a z-index counter now, `Esc` closes the topmost card, hit areas 13px → 22px); a freshly created pin was never persisted; pins floated over the browse reader; segmented bar buttons dropped their left border so the grey neighbour painted over the hovered accent ring; `RMB`-pin panned the camera even for a node already centred, and "centre" ignored the panels covering the canvas. New: hovering a card draws a hairline to the node it pins. Left bar: `⇤ автоскрытие / ⇥ закреплён` keeps the HUD up while a note is open (new `hudAuto` config key), the fold control moved into a sticky foot — unfolded, it used to scroll out of reach and became a one-way door — sections now reveal with a staggered fade, and the lens pill is actually centred (its entry animation was overwriting the `translateX(-50%)` that centred it).
- **2.13.1** (2026-07-18) — release: first tag to ship the prebuilt `dist/memory-atlas.pyz` as a downloadable asset (the zero-clone route the README promises); rolls up the 07-18 editor polish (reader-mode, hover-pin cards, "категория · авто" unified axis, `--fast-regen`, uk locale fix) and the `atlas-serve` exec bit. No generator behaviour change vs 2.13.0.
- **2.13.0** (2026-07-18) — editor pass: hover-pin overhaul (aero-glass background so text never flickers, free placement + reload persistence via localStorage, distinct-link dedupe, open-in-right-bar button, in-card tag editing + per-detector edge counts, fold/copy controls); document import — `atlas-serve` `/api/import` converts arbitrary files to markdown via markitdown (or keeps them as-is), with an import panel in the new-note UI (see `docs/IMPORT-FORMATS.md` for the tested format matrix and what degrades).
- **2.12.0** (2026-07-11) — trilingual UI: Ukrainian (i18nUK) added; the bar language button cycles RU → EN → UK, RU stays canonical markup.
- **2.11.0** (2026-07-10) — release aggregate of the 07-10 wave: frametime pass v2.10.1-v2.10.5 (perf) + scale pass v2.10.6 (features) + perf/ bench harness; published to GitHub with rebuilt dist.
- **2.10.6** (2026-07-10) — scale pass: the group axis is cardinality-capped per layout (410 louvain topics minted 410 spine headers / facet panels / hulls — the text-wall screens; top groups keep sections, the tail merges into one … group routed to the arc/disc, hulls skip it); density-LOD (scale-free reading: few notes in frame = card previews with body, whatever the layout inflated the world to — «3-6 on screen» zoom now exists on every view); node screen-radius floor (sub-pixel rim nodes were invisible and unclickable); dendro branch skeleton (the crown no longer rings an empty disc); group-title fonts capped in screen terms (giant CAPS stopped growing with zoom); ✦ orient is a smooth eased tween (the 6 random jumps read as no animation at all).
- **2.8.0** (2026-07-09) — multi-root vaults: repeatable `--src [NAME=]DIR` (first root = primary index zones, extras one zone each, cross-root `[[link]]` resolve kills ghosts, readable parent-dir ids on stem collisions, per-root editor paths via `DATA.roots`); `--dump-data FILE|-` (DATA JSON out, pipeline source end); `temporal_proximity` now caps node DEGREE at top-k=2 (the per-source cap let hub notes collect a rose dash from everyone — ~1250 → ~250 edges).
- **2.4.1** (2026-07-09) — refine pass: `--data` contract validator (broken external graphs fail at build time, not as a dead page); session detector fixed for vaults living in a subdir of a git repo (`git log --relative`); `--demo` also mutes the session detector (packaging commits ≠ sessions); preset toasts translate in EN mode; generator↔template version handshake (`atlas-tpl` meta, warns on stale symlink pair); `maxN` "all" persists as a sentinel (a grown corpus no longer comes back silently top-N-filtered); client semantic search honors `ATLAS_OLLAMA`; `.pyz` compressed (590K → 195K); dead edge-hover code removed.
- **2.4.0** (2026-07-09) — public-release pass: EN comments/CLI, generic path autodetect, Windows toolchain + CI matrix, locale-auto UI language, pin cards with preview + view capture.
- **2.3.0** (2026-07-09) — continuous zoom LOD, temporal lens, ego-blur at half resolution (fps), panel link previews, usage telemetry, editor URL-schemes.
- **2.2.0** (2026-07-08→09) — tag-lens ("blur + emptiness"), hover-preview cards, HUD bar-blocks, generator portability for Obsidian vaults, adaptive readability, EN i18n layer + RU/EN toggle, installer zipapp + synthetic demo vault.
- **2.1.0** (2026-07-08) — label declutter + density axis, ego-blur cache (60→10fps drag lag fixed), context-aware fit.
- **2.0.0** (2026-07-08) — first versioned release: 9 layouts, task presets, server-less regen admin.

## License

MIT. Bundles [D3 v7](https://d3js.org) (ISC, © Mike Bostock).
