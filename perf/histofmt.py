#!/usr/bin/env python3
"""histofmt — render corpus-bench results as markdown with inline bar charts.

A table of milliseconds tells you the numbers; it does not tell you the SHAPE. The whole
question about a search path is whether it scales with the corpus or with the pool, and
that is a thing you see in bar lengths and read out of digits only afterwards. So the bars
are the point and the digits ride along.

Bars use eighth-blocks, so a value below one full cell still renders as something other
than nothing — a 0.3 ms bar that rounds to an empty string reads as "free", which is a
different claim than "small".

usage:
  python3 histofmt.py results.json                 # markdown to stdout
  python3 histofmt.py results.json --width 40
  python3 histofmt.py results.json --public        # drop query strings and file paths
"""
import argparse
import json
import sys

EIGHTHS = " ▏▎▍▌▋▊▉█"


def bar(value, vmax, width=28):
    """Eighth-block bar. Zero renders empty; anything positive renders at least a sliver."""
    if vmax <= 0:
        return ""
    frac = max(0.0, min(1.0, value / vmax))
    cells = frac * width
    full = int(cells)
    rem = cells - full
    out = "█" * full
    eighth = int(round(rem * 8))
    if eighth:
        out += EIGHTHS[eighth]
    if not out and value > 0:
        out = EIGHTHS[1]
    return out


def fmt_ms(v):
    if v >= 100:
        return "%.0f" % v
    if v >= 10:
        return "%.1f" % v
    return "%.2f" % v


def fmt_bytes(n):
    for unit in ("B", "KB", "MB"):
        if n < 1024 or unit == "MB":
            return "%.1f %s" % (n, unit) if unit != "B" else "%d B" % n
        n /= 1024.0


def chart(rows, width=28, unit="ms", value_fmt=fmt_ms):
    """rows: [(label, value)] -> fenced block of aligned bars."""
    if not rows:
        return "```\n(no data)\n```"
    vmax = max(v for _, v in rows)
    lab_w = max(len(l) for l, _ in rows)
    val_w = max(len(value_fmt(v)) for _, v in rows)
    out = ["```"]
    for label, v in rows:
        out.append(
            "%-*s │%-*s %*s %s"
            % (lab_w, label, width, bar(v, vmax, width), val_w, value_fmt(v), unit)
        )
    out.append("```")
    return "\n".join(out)


def table(headers, rows, align=None):
    align = align or ["---"] * len(headers)
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join(align) + "|"]
    for r in rows:
        out.append("| " + " | ".join(str(c) for c in r) + " |")
    return "\n".join(out)


def render(blob, width=28, public=False):
    res = blob["results"]
    reps = blob.get("reps", "?")
    md = []

    md.append("### Corpus scale")
    md.append("")
    md.append(
        table(
            ["corpus", "nodes", "edges", "page", "vectors"],
            [
                (
                    r["corpus"],
                    r["nodes"],
                    r["edges"],
                    fmt_bytes(r["bytes"]),
                    ("%s · %dd" % (r["rerank"]["model"], r["rerank"]["dim"]))
                    if r.get("rerank")
                    else "—",
                )
                for r in res
            ],
            align=["---", "--:", "--:", "--:", "---"],
        )
    )
    md.append("")

    # --- the headline: does lexical search scale with the corpus? ---
    md.append("### `runSearch()` — median of %s reps, two-term query" % reps)
    md.append("")
    rows = []
    for r in res:
        q = next((x for x in r["queries"] if x["class"] == "two-term"), None)
        if q:
            rows.append(("%s (%d)" % (r["corpus"], r["nodes"]), q["ms_med"]))
    md.append(chart(rows, width))
    md.append("")
    md.append(
        "Two-term is the load-bearing class: it walks every node, and on a miss in id and "
        "desc it falls through to the body. One term or three changes the constant, not the "
        "shape."
    )
    md.append("")

    # --- per class ---
    md.append("### By query class")
    md.append("")
    for r in res:
        md.append("**%s** — %d nodes" % (r["corpus"], r["nodes"]))
        md.append("")
        rows = [(q["class"], q["ms_med"]) for q in r["queries"]]
        md.append(chart(rows, width))
        md.append("")
        hdr = ["class", "ms med", "ms min–max", "pool", "canvas"]
        body = []
        for q in r["queries"]:
            body.append(
                (
                    q["class"] if public else "%s — `%s`" % (q["class"], q["q"]),
                    fmt_ms(q["ms_med"]),
                    "%s–%s" % (fmt_ms(q["ms_min"]), fmt_ms(q["ms_max"])),
                    q["pool"],
                    q["matched"],
                )
            )
        md.append(table(hdr, body, align=["---", "--:", "--:", "--:", "--:"]))
        md.append("")

    # --- the regression guard, stated as a check and not as prose ---
    md.append("### Pool-vs-canvas agreement")
    md.append("")
    md.append(
        "`pool = 0` while `canvas > 0` is the v2.18.0 empty-dropdown bug: the graph lit up "
        "and the list had nothing in it. It is checked here per corpus rather than described, "
        "because the version that shipped it also had a passing test suite."
    )
    md.append("")
    guard = []
    for r in res:
        bad = [
            q["class"]
            for q in r["queries"]
            if q["pool"] == 0 and q["matched"] > 0 and q["class"] != "punct-only"
        ]
        guard.append((r["corpus"], "FAIL: %s" % ", ".join(bad) if bad else "ok"))
    md.append(table(["corpus", "verdict"], guard))
    md.append("")

    # --- semantic rerank cost ---
    if any(r.get("rerank") for r in res):
        md.append("### Semantic rerank — client side, per query")
        md.append("")
        rows = [
            ("%s (%d vec)" % (r["corpus"], r["rerank"]["vecs"]), r["rerank"]["ms"])
            for r in res
            if r.get("rerank")
        ]
        md.append(chart(rows, width))
        md.append("")
        md.append(
            "Cosine over the baked int8 vectors, dequantised once and cached. **Excludes the "
            "query-embedding round-trip to Ollama** — that cost is a constant per keystroke-"
            "burst, not a function of corpus size, and it is the part that needs `atlas-serve`: "
            "from a `file://` page the request never leaves."
        )
        md.append("")

    return "\n".join(md)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("results")
    ap.add_argument("--width", type=int, default=28)
    ap.add_argument("--public", action="store_true",
                    help="omit query strings (they are vault vocabulary)")
    ap.add_argument("--out", default="-")
    args = ap.parse_args()

    with open(args.results, encoding="utf-8") as f:
        blob = json.load(f)
    md = render(blob, width=args.width, public=args.public)
    if args.out == "-":
        sys.stdout.write(md + "\n")
    else:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(md + "\n")
        print("out: %s" % args.out, file=sys.stderr)


if __name__ == "__main__":
    main()
