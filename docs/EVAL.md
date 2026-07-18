# EVAL — what search costs, per corpus

Numbers here are produced by `perf/corpus-bench.py`, which drives a real headless Chrome over
the DevTools protocol and calls the page's own `runSearch()`. Nothing is re-implemented for the
bench: a node-side copy of the ranking loop would measure the copy, and the copy is exactly the
thing that cannot regress in the way the shipped page does.

## Read this before the bars

- **Wall-clock here is not a promise about your vault.** It is one laptop, one browser, one
  build. What transfers is the *shape* — how the cost moves as the corpus grows, and which
  query classes are cheap or expensive relative to each other.
- **`ms` is the synchronous search only.** `runSearch` also asks for a redraw; that frame is
  the render bench's subject (`perf/frame-bench.mjs`), not this one. Adding them would double
  count and hide which half moved.
- **The two real vaults are private**, so they appear as `vault-A` and `vault-B` with no titles
  and no query strings — a query is vault vocabulary. The synthetic corpora carry the
  reproducible part: `perf/synth-corpus.py --n N` builds them from a fixed seed, so anyone can
  re-run the curve and compare shapes rather than trust these digits.
- **The synthetic corpora are built `--no-semantic-cross`.** Their bodies are drawn from one
  small word pool, so nearly every pair clears the similarity threshold and the cross-detector
  degenerates into a near-complete graph. That is a property of the fake corpus, not of the
  detector, and leaving it on would have made the page weight and edge count meaningless. The
  two real vaults are built with the full default flags.
- **A query class, not a query.** Corpora in different languages share no vocabulary, so the
  comparable unit is the shape of the query. The classes are defined in
  `perf/corpus-queries.json`.

## Why this file exists at all

v2.18.0 shipped a search that lit up the graph and returned an empty dropdown for every
two-word query, with a 54-test suite passing. v2.18.1-as-drafted fixed that and, in the same
change, closed the gate that ran the semantic reranker — also with the suite passing. Both were
found by driving the page, not by reading it. `pool` and `canvas` are printed side by side below
for that reason: their disagreement is the failure mode, so it is a column rather than a claim.

### Corpus scale

| corpus | nodes | edges | page | vectors |
|---|--:|--:|--:|---|
| synth-250 | 250 | 1000 | 2.1 MB | embeddinggemma · 768d |
| synth-1000 | 1000 | 3995 | 6.2 MB | embeddinggemma · 768d |
| synth-4000 | 4000 | 15996 | 22.5 MB | embeddinggemma · 768d |
| vault-A | 497 | 2998 | 5.6 MB | embeddinggemma · 768d |
| vault-B | 2404 | 4202 | 15.3 MB | embeddinggemma · 768d |

### `runSearch()` — median of 7 reps, two-term query

```
synth-250 (250)   │██                           1.50 ms
synth-1000 (1000) │█████▍                       4.10 ms
synth-4000 (4000) │███████████████████▌         14.8 ms
vault-A (497)     │███████████▋                 8.80 ms
vault-B (2404)    │████████████████████████████ 21.3 ms
```

Two-term is the load-bearing class: it walks every node, and on a miss in id and desc it falls through to the body. One term or three changes the constant, not the shape.

### By query class

**synth-250** — 250 nodes

```
one-term   │████████████████████████████ 2.00 ms
two-term   │█████████████████████        1.50 ms
three-term │███████████████████████▊     1.70 ms
punct-only │██████████████               1.00 ms
no-hit     │█████▋                       0.40 ms
```

| class | ms med | ms min–max | pool | canvas |
|---|--:|--:|--:|--:|
| one-term | 2.00 | 0.90–2.50 | 10 | 62 |
| two-term | 1.50 | 1.20–2.50 | 10 | 161 |
| three-term | 1.70 | 1.30–2.10 | 10 | 155 |
| punct-only | 1.00 | 0.50–1.40 | 10 | 250 |
| no-hit | 0.40 | 0.30–1.10 | 0 | 0 |

**synth-1000** — 1000 nodes

```
one-term   │████████████▎                2.40 ms
two-term   │████████████████████▉        4.10 ms
three-term │████████████████████████████ 5.50 ms
punct-only │██████▋                      1.30 ms
no-hit     │█████▋                       1.10 ms
```

| class | ms med | ms min–max | pool | canvas |
|---|--:|--:|--:|--:|
| one-term | 2.40 | 2.20–4.60 | 10 | 220 |
| two-term | 4.10 | 3.60–6.30 | 10 | 528 |
| three-term | 5.50 | 4.40–6.20 | 10 | 653 |
| punct-only | 1.30 | 1.10–2.70 | 10 | 1000 |
| no-hit | 1.10 | 1.00–2.00 | 0 | 0 |

**synth-4000** — 4000 nodes

```
one-term   │████████████▍                7.70 ms
two-term   │███████████████████████▋     14.8 ms
three-term │████████████████████████████ 17.5 ms
punct-only │███████▌                     4.70 ms
no-hit     │████████                     5.00 ms
```

| class | ms med | ms min–max | pool | canvas |
|---|--:|--:|--:|--:|
| one-term | 7.70 | 6.70–11.4 | 10 | 947 |
| two-term | 14.8 | 13.8–17.6 | 10 | 2059 |
| three-term | 17.5 | 16.4–19.7 | 10 | 2478 |
| punct-only | 4.70 | 4.30–7.80 | 10 | 4000 |
| no-hit | 5.00 | 4.80–7.70 | 0 | 0 |

**vault-A** — 497 nodes

```
one-term   │██████████████████           8.40 ms
two-term   │██████████████████▊          8.80 ms
three-term │████████████████████████████ 13.1 ms
punct-only │███████████▏                 5.20 ms
no-hit     │████████████████████▊        9.70 ms
```

| class | ms med | ms min–max | pool | canvas |
|---|--:|--:|--:|--:|
| one-term | 8.40 | 7.90–9.60 | 10 | 245 |
| two-term | 8.80 | 8.40–12.4 | 10 | 316 |
| three-term | 13.1 | 12.1–14.4 | 10 | 103 |
| punct-only | 5.20 | 4.10–6.60 | 10 | 425 |
| no-hit | 9.70 | 8.70–12.3 | 0 | 0 |

**vault-B** — 2404 nodes

```
one-term   │███████████████████████████▉ 21.2 ms
two-term   │████████████████████████████ 21.3 ms
three-term │██████████████████████████▋  20.3 ms
punct-only │███████████████████          14.5 ms
no-hit     │██████████████████████▏      16.8 ms
```

| class | ms med | ms min–max | pool | canvas |
|---|--:|--:|--:|--:|
| one-term | 21.2 | 20.1–26.4 | 10 | 120 |
| two-term | 21.3 | 19.2–32.5 | 10 | 266 |
| three-term | 20.3 | 19.1–25.3 | 10 | 353 |
| punct-only | 14.5 | 14.0–17.7 | 10 | 2369 |
| no-hit | 16.8 | 16.7–18.8 | 0 | 0 |

### Pool-vs-canvas agreement

`pool = 0` while `canvas > 0` is the v2.18.0 empty-dropdown bug: the graph lit up and the list had nothing in it. It is checked here per corpus rather than described, because the version that shipped it also had a passing test suite.

| corpus | verdict |
|---|---|
| synth-250 | ok |
| synth-1000 | ok |
| synth-4000 | ok |
| vault-A | ok |
| vault-B | ok |

### Semantic rerank — client side, per query

```
synth-250 (250 vec)   │███████████▎                 2.10 ms
synth-1000 (1000 vec) │██████████████               2.60 ms
synth-4000 (4000 vec) │████████████████████████████ 5.20 ms
vault-A (425 vec)     │███████████████▋             2.90 ms
vault-B (2369 vec)    │█████████████████▎           3.20 ms
```

Cosine over the baked int8 vectors, dequantised once and cached. **Excludes the query-embedding round-trip to Ollama** — that cost is a constant per keystroke-burst, not a function of corpus size, and it is the part that needs `atlas-serve`: from a `file://` page the request never leaves.

## What the shape actually says

The headline chart is labelled by node count, and reading it as "cost scales with nodes" is the
mistake it invites. Compare the tables: one of the real vaults has fewer than half the nodes of a
synthetic corpus and costs more per query than it does. The reason is in the search itself — a
term that misses `id` and `desc` falls through to the note BODY, so what the loop actually walks
is total body text, and node count is only a proxy for that. The synthetic corpora hold short,
uniform bodies by construction; real notes do not.

Two consequences worth stating plainly:

- **Comparing your vault to these bars by note count will mislead you.** Compare by how much
  prose your notes carry.
- **The synthetic curve is a floor, not a forecast.** It isolates how the algorithm scales when
  body size is held constant. That is the useful thing to regression-test against, and it is not
  a prediction of what your own vault will feel like.

The `no-hit` class is where this is most visible: it can only be answered by scanning everything,
since nothing matches anywhere, so it prices the full walk with no early exits at all.

## Known and deliberate

- **The canvas and the dropdown still search different fields.** The canvas filter matches
  `id · label · desc · type · zone`; the dropdown pool matches `id · label`, `desc`, body — no
  `type`, no `zone`. So a query naming a zone dims the graph more widely than it fills the list.
  Aligning them would put every node of a zone into a ten-row list, which is a worse answer than
  the divergence. Named here rather than fixed, because an undocumented difference is the thing
  that reads as a bug.
- **Layout offsets around the bar are still partly constant.** `--barH` removed the two that had
  actually collided; `+62px`, `+20px` and the `-12` matching `#bar { bottom: 12px }` remain, and
  the last is a literal duplicate of a CSS value with no failure signal if one side changes.
  There is no reproduction today; it is held by discipline, not by structure.

## Reproducing

```sh
python3 perf/synth-corpus.py --n 1000 --out /tmp/synth-1000
./memory-atlas --src synth=/tmp/synth-1000 --search-vecs --no-semantic-cross \
    --no-open --out /tmp/synth-1000.html
python3 perf/corpus-bench.py --corpus synth-1000=/tmp/synth-1000.html \
    --queries perf/corpus-queries.json --out /tmp/results.json
python3 perf/make-eval-doc.py /tmp/results.json --out docs/EVAL.md
```

The raw numbers behind this page are checked in as `perf/corpus-bench-results.json` — with the
two private vaults' query strings removed, since those are vault vocabulary rather than results.

Behavioural assertions for the same code path — the ones that fail when search breaks rather
than when it slows down — live in `tests-search.py`.
