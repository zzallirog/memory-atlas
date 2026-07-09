# memory-atlas — quickstart

Turn a folder of markdown notes (Obsidian or plain) into one self-contained
HTML graph. No server, offline, one file out. The point isn't "a graph" — it's
**overlap**: the tool surfaces links you never wrote by hand (a shared missing
note, overlapping tags, co-edits) on top of your explicit `[[wikilinks]]`.

## Requirements

- **Python 3** (3.8+). That's it. Check: `python3 --version`.
- A modern browser (the output opens itself).
- Ollama is **optional** — see "Semantic bridges" below. You don't need it.

Two equivalent ways to run every command below:

- from a clone of this repo: `./memory-atlas …` (or `python3 memory-atlas …`);
- from the single-file bundle: `python3 dist/memory-atlas.pyz …` — copy that
  one file anywhere, nothing else needed.

## 1. See the demo first

```
./memory-atlas --demo
```

A browser opens on a tiny synthetic vault: a **cooking** cluster and a
**chemistry** cluster that share no hand-written link. The tool draws two
bridges anyway:

- a dashed **ghost** node `maillard-reaction` that both zones reference but
  neither wrote as a file (`shared_ref`);
- a **tag** bridge between two notes that share tags across the two zones
  (`tag_overlap`).

That's the "aha": it found what the two clusters have in common.

Language: the UI defaults to English. The small **RU/EN** button in the bottom
bar toggles language (it fades out when idle — move the mouse to wake it). Your
choice is remembered and survives rebuilds.

## 2. Point it at your own vault

```
./memory-atlas --src ~/path/to/your/vault
```

- Each **top-level folder** in the vault becomes a colored **zone**. The
  overlap bridges are drawn *between* zones — so a vault organized into a few
  folders shows the most. A single flat folder still renders (wikilinks +
  ghost debts), just without cross-zone bridges.
- Obsidian vaults work out of the box: `.obsidian/`, `.trash/`, `node_modules/`
  are skipped; top-level `tags:` in frontmatter are read.
- Your notes stay yours: everything runs locally, the output is a static
  `file://` page on your machine. (The HTML embeds note titles/descriptions, so
  don't hand the generated file to anyone if the vault is private — regenerate,
  don't reshare.)

Start in your language:

```
./memory-atlas --src ~/vault --lang ru     # or --lang en (default)
```

## 3. Rebuild after editing notes

The HTML is a snapshot. Edit notes, rerun the same command, refresh the page.
Layout / colors / layers don't need a rebuild — they're live controls in the
left panel. Press **?** in the page for all keys.

## Semantic bridges (optional upgrade)

If you install [Ollama](https://ollama.com) and pull an embedding model:

```
ollama pull nomic-embed-text
./memory-atlas --src ~/vault
```

…a fifth detector adds **meaning** bridges (notes that read as similar even
with no shared tag or link). Without Ollama the generator prints one warning and
carries on — every other bridge still works.

## Useful flags

| flag | what |
|------|------|
| `--demo` | build the bundled demo vault |
| `--src DIR` | your vault |
| `--out FILE` | where to write the HTML (default: `./atlas-demo.html` for `--demo`, else the atlas cache dir — the build prints the path) |
| `--lang ru\|en` | starting UI language |
| `--no-open` | don't auto-open the browser |
| `--no-detectors` | wikilink graph only, fastest |
| `--help` | everything else |
