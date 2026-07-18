# Handoff — graph template topology + English-only comments (2026-07-18, ~11:30)

Scope of the NEXT session, written by the session that landed `955c7c3` + `497f8fc`.
Read this before touching anything; every anchor below was verified live, not recalled.

## The task

Two jobs, both **before** the push to public `gh/main`.

1. **Restructure `memory-atlas.template.html` into a block topology.** 434 KB in one
   sheet. This session had to locate functions with `python3 -c "s.find(...)"` three
   separate times because nothing is navigable by eye. The user's reason: "в будущем
   будет много правок". Wanted: grouped blocks, anchor comments, section headers.
2. **All code comments → English, across the whole line that goes public**: the
   generator, the template, `atlas-serve`, `atlas-import`. The repo is a public
   artifact; Russian comments do not ship.

### Start here, it is our own debt
The two commits this session landed carry **Russian comments and a Russian `--help`
string** (`--exclude-tag` / `--exclude-type` in `memory-atlas`, comments in
`build_graph`, `openShelf` and the search block in the template). That is the first
thing to translate — do not let it reach the push.

## State

- Branch `main`, tree clean, **not pushed**. `main == gh/main` as of last night's release.
- `955c7c3` — `--exclude-tag` / `--exclude-type`, ghost suppression, `title:` as `name:`.
- `497f8fc` — shelved appendix: off the canvas, still in browse + search.
- self-test **52/52** (`python3 memory-atlas --self-test`). Keep it green per commit.
- Version stays `2.13.1`; the generator↔template handshake (`VERSION` ==
  `<meta name="atlas-tpl">` == README changelog) is asserted by the self-test. A version
  bump touches three places — check before assuming two.

## What those commits do (and the numbers behind them)

A foreign vault can carry a reference appendix that outnumbers the knowledge. Measured
on the real 2370-note vault: one zone bucket, louvain 82 % in a single cluster, degree
median 1 against a hub at 2136. Filtering it out gives `141` nodes — the exact count the
vault's own author renders. Clusters `8` at 0.214 max share, degree median `11`,
generation `58 s → 7 s`.

Excluded notes are **shelved, not deleted**: absent from `nodes`/`edges` (detectors,
layout and clustering must never see them — that is where the 58 s went), rejoined in
`to_browse_data` and exposed as a `shelf` key (metadata only; bodies already travel once
inside `browse`). Search puts graph hits first, the appendix follows under its own
divider with reserved slots. `openShelf()` renders the entry in the right panel and
deliberately does **not** call `selectNode()` — camera, selection and graph stay put.

Artifact `1.97 → 6.19 MB`, load `6244 → 6328 ms`. Payload size is not what costs on load;
do not optimise bytes here without re-measuring.

## Anchors (verified this session)

| what | where |
|---|---|
| generator | `memory-atlas` — `build_graph()` L223, `to_browse_data()` L783, CLI flags ~L990 |
| template | `memory-atlas.template.html` — `CAT_AXIS`, `buildDrop`, `pickHit`, `openShelf`, `selectNode` |
| grep the template | **`grep -a`** — without `-a` it is detected as binary and greps silently return nothing (this session lost a step to exactly that) |
| i18n | three dicts keyed in Russian: RU source, EN, UK. New strings go in all three |
| editor server | `atlas-serve` |
| unpacked foreign vault | `arch:~/misha-wiki-full/wiki` (5.5 GB, mostly a Python venv) |
| smaller psychology-only copy | `arch:~/misha-vault/psychology` |
| live probes | `arch:~/claw-dashboard/frontend/{misha-probe,shelf-probe}.mjs` (Playwright lives there) |

## The foreign vault — facts, not inference

Its structure is documented **by its own author** in `psychology/CLAUDE.md`,
`index.md`, `roadmap.md` and the hub MOC `wiki/загальна/Загальна психологія.md`.
Two cold agents with no hints read it correctly in 8 and 11 tool calls. This session
did not, because it entered as a renderer — folders, tags, links — and measured instead
of reading the docs sitting in the root. **Read a foreign vault's own documentation
first.** That is the whole lesson of the session.

His live Obsidian graph filter, verbatim from `.obsidian/graph.json`:

```
path:psychology
  -path:"psychology/log.md"  -path:"psychology/index.md"
  -path:"psychology/roadmap.md"  -path:"psychology/CLAUDE.md"
  -path:"sources/"  -path:"терміни/"
```

`_scripts/graph-colors.json` → `themes`: **23** entries, 21 colours (`мовлення`/`мова`
and `емоції`/`почуття` share one), and `словник` is itself a theme in muted grey — the
appendix is toned down, not hidden. Note his `roadmap.md` says "8 тем-тегів"; the
registry says 23. **The config is the authority, his prose drifted** — same failure
class this session hit from the other side.

His deterministic script layer, all "counted, not inferred": `priority.py` (what to
write next, demand = pages linking a page that does not exist), `rank.py` (network
metrics), `terms.py` (term co-occurrence), `gaps.py`, `lint.py`, and
`ingest-pdf.sh` / `ingest-youtube.sh` which stop at `raw/_inbox/` on purpose —
"Does NOT touch the wiki — that is the assistant's job during ingest".

## Open, not decided

- **The merged editor: server verified, CLIENT NOT VERIFIED.** Decision was made — our
  editor is the base, his features come across. Ported from his `memory-atlas-live`:
  optimistic concurrency (`mtime` echoed by the client, 409 on stale, `force` override),
  atomic writes (temp + `os.replace` — a direct `write_text()` that dies mid-flight
  truncates the note), dotfile refusal, `raw/` immutability, a 64 MB body cap, and a
  typed `ApiErr` so a handler can answer with a real status instead of collapsing
  everything into 400.

  The server side is proven live — 13/13 against a real HTTP server: stale write refused
  with the body intact, `force` overriding deliberately, `raw/` 403, dotfile 400, escape
  refused, no `.atlas-tmp` residue. The script is `scratchpad/serve-test.py`; **move it
  into the repo** — right now it lives outside and will be lost.

  The client half (`startEdit` sends `cur.mtime`, `api()` carries `e.status`, 409 asks
  before overwriting) is written and the page loads clean, but the save path was
  **never driven end-to-end**. Three attempts failed on instrumentation, and here is
  what was learned so the next session does not repeat them: tabs are NOT `[data-tab]`;
  browse rows are NOT `[data-id]`; the browse module lives in its own IIFE, so `api()`
  is **not reachable from `page.evaluate`**. Either export a test hook or drive the real
  DOM (`#list` / `#prev` / `#bq` exist and are the browse surface). Until then, treat
  conflict protection as claimed-not-measured.
- **The graph goes fully unlit while a shelf entry is open.** Dimming on `panel-open` is
  normal (verified against a normal node), but a shelf entry sets no `selected`, so no
  hop labels survive and nothing is labelled. Fix is likely dropping the body-level
  `panel-open` class for shelf, which also drives panel and minimap layout — needs its
  own verify cycle, not a blind edit.
- **MOC-driven taxonomy is not built.** `tier` is still a constant `A` in that vault.
  The MOC gives two levels outright (6 sections → 23 concepts); `roadmap.md` names
  leaves for only 30 % (74 of 244). Deterministic parse first, LLM only for the tail —
  a 64-agent inference run over the whole corpus was explicitly refused.

## Rules on this line

- Comments in English. Typed commits. **No `Co-Authored-By` / "Generated with" trailers.**
- `--self-test` green before every commit; add a test with every behaviour change.
- Push only on the user's trigger. `main` is public — force is a red button.
- Verify live, do not reason: this session twice produced numbers from a broken
  measurement (an unquoted `$(find)` split on spaces; deleting a hub file that left its
  links behind as a ghost) and twice had to retract. Run it, then claim it.
