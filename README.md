# memory-atlas

[![ci](https://github.com/zzallirog/memory-atlas/actions/workflows/ci.yml/badge.svg)](https://github.com/zzallirog/memory-atlas/actions/workflows/ci.yml)

> **A folder of notes → one HTML graph.** Python stdlib in, `file://` page out. No server, no cloud. The detectors draw the links you never wrote.

Turn a folder of markdown notes into **one self-contained interactive graph** — a single HTML file. No server, no build step, no cloud: Python 3 stdlib in, `file://` page out.

The point isn't "a graph of my wikilinks". It's **overlap**: the generator runs a set of detectors that surface links you never wrote by hand — a missing note two clusters both reference, overlapping tags, notes edited in the same sitting — and draws them on top of your explicit `[[wikilinks]]`.

![overview — four topic zones on a synergy ring, cross-zone bridges through the middle](docs/shots/overview.png)

*Four folders — chemistry, cooking, gardening, music — laid out on a zone-synergy ring. The dashed lines cutting across the center are bridges the detectors drew: notes in different folders that share a missing reference, a tag, or a co-edit. Nobody wrote those links by hand.*

## Quick start

```bash
git clone https://github.com/zzallirog/memory-atlas && cd memory-atlas
./memory-atlas --demo            # tiny synthetic vault, opens in your browser
./memory-atlas --src ~/my-vault  # your own notes
./memory-atlas --src ~/vault --src wiki=~/wiki   # several roots, one graph
```

Or the zero-clone route — one file, nothing else:

```bash
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
- **9 layouts** (force / semantic / pack / ring / petals / radial / grid / zones / timeline), morph animated, <kbd>[</kbd> <kbd>]</kbd> to cycle; task presets that set layout+color+layers in one pick.
- **Lenses instead of hairballs**: click a tag — only tagged notes stay sharp, the rest dissolves into blur. Same engine drives the ⌚ *temporal lens*: pick a note, see everything edited in the same time window (2→7→30 days). Detector edges are hidden by default and served through lenses — lines are noise until you ask.
- **Read in place**: hover previews, description snippets under neighbors when a note is focused, a full **browse** tab (three-pane reader over the same data), and a **dash** tab (zones, freshness, ghost debts, data health).
- **Continuous zoom LOD**: dots → labels → cards with description previews, one smooth ramp.
- **Local usage telemetry** (localStorage only): a `usage` color mode shows which notes *you* actually open.
- **UI in English or Russian** — RU/EN toggle in the bottom bar, choice persists.
- Pins, saved views, deep links (`?state=`), user-drawn edges, zone overrides, profile export/import — all persisted in your browser, exportable as one JSON.

## Privacy

Everything runs on your machine and the output is a static local page. The generated HTML **embeds note titles, descriptions and body text** — treat the built file like the vault itself: regenerate for others, don't reshare yours. The demo vault is synthetic.

<details>
<summary><b>Honest scope</b> — where the edges are rough</summary>

- Built first for the author's own memory corpus; foreign-vault support (Obsidian layouts, arbitrary zones) is tested on synthetic and real vaults but younger than the core.
- Up to 8 zones get distinct colors; more fall into a shared grey.
- The `semantic` layout uses PCA over embeddings — honest cosine geometry, weaker separation than UMAP would give.
- Rendering is 2D canvas, comfortable at a few hundred notes; thousands untested.

</details>

<details>
<summary><b>Layout of this repo</b></summary>

```
memory-atlas                  # generator (Python 3 stdlib, single file)
memory-atlas.template.html    # D3-canvas render template (must sit next to the generator)
vendor/d3.v7.min.js           # D3 v7 (ISC license), inlined into the output
demo/                         # synthetic two-zone demo vault
installer/build-pyz.sh        # packs everything into dist/memory-atlas.pyz
dist/memory-atlas.pyz         # prebuilt single-file bundle
docs/QUICKSTART.md            # the friendly walkthrough
```

`./memory-atlas --self-test` runs the built-in test suite. Press <kbd>?</kbd> inside the atlas for every key and edge type.

</details>

<details>
<summary><b>Development</b></summary>

- `dist/` is a build artifact (`python3 installer/build_pyz.py`), gitignored in dev; the published repo ships a prebuilt copy for the zero-clone route.
- Deployed locally as `~/bin` symlinks (generator + template travel as a PAIR — the generator warns on version skew).
- Durable off-machine backup channel: `git push origin main` (bare repo); Gitea intentionally skipped per backup topology.
- CI (`.github/workflows/ci.yml`): ubuntu/macos/windows × py3.8/3.12 — self-test + demo build + `.pyz` build.

</details>

## Changelog

Latest: **2.11.2 — reading at any scale** ([release](https://github.com/zzallirog/memory-atlas/releases/latest)). Full per-version history in **[CHANGELOG.md](CHANGELOG.md)**.

## License

MIT. Bundles [D3 v7](https://d3js.org) (ISC, © Mike Bostock).
