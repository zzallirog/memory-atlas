#!/usr/bin/env python3
"""make-eval-doc — render docs/EVAL.md from a corpus-bench results file.

The prose lives here rather than in the .md so the document cannot drift from the numbers
it describes: regenerate and both move together. What the prose must NOT do is restate a
number — anything quoted in a sentence would be a second copy to keep in sync, and the
copy is what goes stale.

usage:
  python3 perf/make-eval-doc.py results.json --out docs/EVAL.md
"""
import argparse
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("histofmt", os.path.join(HERE, "histofmt.py"))
histofmt = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(histofmt)

HEAD = """# EVAL — what search costs, per corpus

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

"""

TAIL = """
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
./memory-atlas --src synth=/tmp/synth-1000 --search-vecs --no-semantic-cross \\
    --no-open --out /tmp/synth-1000.html
python3 perf/corpus-bench.py --corpus synth-1000=/tmp/synth-1000.html \\
    --queries perf/corpus-queries.json --out /tmp/results.json
python3 perf/make-eval-doc.py /tmp/results.json --out docs/EVAL.md
```

The raw numbers behind this page are checked in as `perf/corpus-bench-results.json` — with the
two private vaults' query strings removed, since those are vault vocabulary rather than results.

Behavioural assertions for the same code path — the ones that fail when search breaks rather
than when it slows down — live in `tests-search.py`.
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("results")
    ap.add_argument("--out", default="-")
    ap.add_argument("--width", type=int, default=28)
    args = ap.parse_args()

    with open(args.results, encoding="utf-8") as f:
        blob = json.load(f)

    body = histofmt.render(blob, width=args.width, public=True)
    doc = HEAD + body + TAIL

    if args.out == "-":
        sys.stdout.write(doc)
    else:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(doc)
        print("out: %s" % args.out, file=sys.stderr)


if __name__ == "__main__":
    main()
