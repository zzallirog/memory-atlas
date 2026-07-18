#!/usr/bin/env python3
"""synth-corpus — deterministic markdown vaults of a chosen size, for the scaling curve.

The two real vaults this tool was built against are private, so their note counts, titles
and query vocabulary cannot carry the published numbers. A synthetic corpus can: it is
reproducible by anyone with this repo, it has no content to leak, and it is the only way a
reader can re-run the curve and get the same shape.

It is a MODEL of a vault, not a sample of one — link density, body length and the zone
split are parameters here and emergent there. Read the curve as scaling behaviour, not as
a prediction of wall-clock on your own notes.

usage:
  python3 synth-corpus.py --n 1000 --out /tmp/synth-1000
"""
import argparse
import os
import random

# Fixed vocabulary: the search classes in corpus-bench.py must hit predictable pools, so
# the words are drawn from this list rather than from anything real.
TOPICS = [
    "lattice", "harbor", "cinder", "meridian", "thicket", "quarry", "vellum",
    "current", "anvil", "beacon", "ravine", "tundra", "cobalt", "ember",
    "silt", "grove", "prism", "fathom", "lichen", "spindle",
]
QUALIFIERS = [
    "north", "deep", "quiet", "broken", "layered", "hollow", "bright",
    "slow", "narrow", "salt", "wild", "folded",
]
FILLER = (
    "The measurement stands or falls on whether the axis is the one the claim is about. "
    "A count that rises under a different partition was never the count in question. "
    "Notes here reference each other so the graph has structure to lay out. "
)


def build(n, out, seed=20260718, links=4, body_words=180):
    rnd = random.Random(seed)
    os.makedirs(out, exist_ok=True)
    names = []
    for i in range(n):
        t = TOPICS[i % len(TOPICS)]
        q = QUALIFIERS[(i // len(TOPICS)) % len(QUALIFIERS)]
        names.append("%s_%s_%04d" % (q, t, i))

    # An index file: the generator reads zone membership out of MEMORY.md, so a synthetic
    # vault without one lands every note in the same zone and the layout degenerates.
    half = n // 2
    with open(os.path.join(out, "MEMORY.md"), "w", encoding="utf-8") as f:
        f.write("# Memory — synthetic corpus (%d notes)\n\n## Index\n" % n)
        for nm in names[:half]:
            f.write("- [%s](%s.md) — synthetic\n" % (nm, nm))
    with open(os.path.join(out, "MEMORY-work.md"), "w", encoding="utf-8") as f:
        f.write("# Memory — work\n\n## Index\n")
        for nm in names[half:]:
            f.write("- [%s](%s.md) — synthetic\n" % (nm, nm))

    body_unit = FILLER.split()
    for i, nm in enumerate(names):
        targets = [names[rnd.randrange(n)] for _ in range(links)]
        words = [body_unit[rnd.randrange(len(body_unit))] for _ in range(body_words)]
        with open(os.path.join(out, nm + ".md"), "w", encoding="utf-8") as f:
            f.write("---\n")
            f.write("name: %s\n" % nm)
            f.write("description: synthetic note %d of %d\n" % (i + 1, n))
            f.write("metadata:\n  type: reference\n---\n\n")
            f.write(" ".join(words) + "\n\n")
            f.write(" ".join("[[%s]]" % t for t in targets) + "\n")
    return len(names)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--seed", type=int, default=20260718)
    ap.add_argument("--links", type=int, default=4)
    args = ap.parse_args()
    made = build(args.n, args.out, seed=args.seed, links=args.links)
    print("%d notes -> %s" % (made, args.out))


if __name__ == "__main__":
    main()
