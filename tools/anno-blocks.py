#!/usr/bin/env python3
"""anno-blocks — block anchors for a single-file page, and the call graph between them.

The problem this exists for: `memory-atlas.template.html` is one file of ~7.7k lines with
~260 top-level definitions and no table of contents. Reading it means scrolling, and pointing
at a place in it means quoting a line number that is wrong by the next commit.

The fix is an ANCHOR, not a line number. Every block carries `[A:slug]` in its header comment;
the slug never moves, so a pointer written today still resolves after the code above it grows.
Line numbers are always DERIVED — resolved by searching for the anchor at the moment you ask —
so nothing in the snapshot can go stale into a wrong answer. The snapshot is an index for
search, never the authority for position.

What a header states is computed from the code, not asserted by hand:
  defines     — top-level names introduced in this block
  -> calls    — names this block uses that another block defines (cross-block edges only)
  <- called by— blocks that use this block's names
  !!          — hand-written invariants; `sync` PRESERVES these and rewrites nothing else

Commands
  scan   [--json OUT]     resolve anchors → blocks.json (+ ~/topos snapshot for navigation)
  sync                    rewrite the computed lines of every header, keep the `!!` lines
  check                   fail if a header names something the file does not define
  show   <slug>           print one block: where it is NOW, what it touches, first lines
  list   [pattern]        anchors + titles + current line, one per row

Deterministic: no clock, no randomness — two runs on unchanged input produce identical output.
"""
import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
TEMPLATE = os.path.join(HERE, "memory-atlas.template.html")
SNAPSHOT = os.path.join(HERE, ".anno", "blocks.json")
# navigation home: `topos anno` reads this, so the anchors of every project land in one place
TOPOS_HOME = os.path.expanduser(os.environ.get("TOPOS_HOME", "~/topos/anno"))

ANCHOR_RE = re.compile(r"^\s*//\s*[─\-]{2}\s*\[A:([a-z0-9][a-z0-9-]*)\]\s*(.*?)\s*[─\-]*\s*$")
# legacy separators already in the file: `// ---- title ----`, `// ==== title ====`
SEP_RE = re.compile(r"^\s*//\s*(?:[-=]{4,}|[─—]{3,})\s*(.*?)\s*(?:[-=─—]{2,})?\s*$")
HEADER_LINE_RE = re.compile(r"^\s*//(\s|$)")
DEF_RE = re.compile(
    r"^\s{0,2}(?:async\s+)?(?:function\s+([\w$]+)"
    r"|(?:const|let|var)\s+([\w$]+)\s*=\s*(?:async\s*)?(?:function\b|\([^)=]*\)\s*=>|[\w$]+\s*=>)"
    r"|class\s+([\w$]+))")
IDENT_RE = re.compile(r"\b([A-Za-z_$][\w$]*)\s*\(")
JS_START = "<script>"


def slugify(title):
    s = re.sub(r"\(.*?\)", " ", title.lower())
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return "-".join(s.split("-")[:4]) or "block"


def js_range(lines):
    """Line span of the main script — CSS and markup carry no call graph."""
    starts = [i for i, l in enumerate(lines) if "<script>" in l and "__D3__" not in l]
    ends = [i for i, l in enumerate(lines) if "</script>" in l]
    if not starts or not ends:
        return 0, len(lines)
    lo = starts[-1]
    hi = max(e for e in ends if e > lo)
    return lo, hi


def parse_blocks(path=TEMPLATE):
    """Split the script into blocks at anchors (preferred) and legacy separators.

    Two-pass on purpose: a file mid-migration has both kinds, and a separator that has not
    been anchored yet must still produce a block — otherwise `sync` would silently drop the
    code between the last anchor and the next one into the previous block.
    """
    with open(path, encoding="utf-8") as f:
        lines = f.read().split("\n")
    lo, hi = js_range(lines)
    marks = []
    for i in range(lo, hi):
        m = ANCHOR_RE.match(lines[i])
        if m:
            marks.append({"line": i, "slug": m.group(1), "title": m.group(2).strip(), "anchored": True})
            continue
        m = SEP_RE.match(lines[i])
        if m and m.group(1) and len(m.group(1)) > 2:
            marks.append({"line": i, "slug": None, "title": m.group(1).strip(), "anchored": False})
    blocks = []
    for k, mk in enumerate(marks):
        end = marks[k + 1]["line"] if k + 1 < len(marks) else hi
        head_end = mk["line"] + 1
        while head_end < end and HEADER_LINE_RE.match(lines[head_end]):
            head_end += 1
        body = lines[head_end:end]
        defines, calls = [], set()
        for l in body:
            d = DEF_RE.match(l)
            if d:
                defines.append(d.group(1) or d.group(2) or d.group(3))
            for name in IDENT_RE.findall(l):
                calls.add(name)
        # Everything hand-written in the header is KEPT. Only the four computed lines are
        # regenerated — a `sync` that ate the prose explaining WHY a block exists would trade
        # the expensive half of a comment for the cheap half. Order is preserved as authored.
        notes = [l for l in lines[mk["line"] + 1:head_end]
                 if not re.match(r"^\s*//\s*(anno —|defines:|-> calls:|-> blocks:|<- called by:)", l)
                 and re.sub(r"^\s*//\s*", "", l).strip()]
        blocks.append({
            "slug": mk["slug"] or slugify(mk["title"]),
            "title": mk["title"],
            "anchored": mk["anchored"],
            "head": mk["line"], "head_end": head_end, "end": end,
            "lines": end - mk["line"],
            "defines": defines,
            "_calls_raw": calls,
            "notes": [re.sub(r"^\s*//\s*", "", n).rstrip() for n in notes],
        })
    # slugs must be unique: two "draw" separators would otherwise share one anchor
    seen = {}
    for b in blocks:
        s = b["slug"]
        if s in seen:
            seen[s] += 1
            b["slug"] = f"{s}-{seen[s]}"
        else:
            seen[s] = 1
    return lines, blocks


UBIQUITY = 8   # a name used by more blocks than this is infrastructure, not a relation


def cross_edges(blocks):
    """calls/called-by, cross-block only. A block calling its own function says nothing.

    Ubiquitous names are dropped from the graph on purpose. `esc`, `T`, `$`, `requestDraw`
    are called from nearly every block, so keeping them would make every `<- called by`
    read "almost everything" — true, and useless for navigation. They are listed once, as
    `uses:`, and the edges that remain are the ones that actually mean "this depends on that".
    """
    owner = {}
    for b in blocks:
        for d in b["defines"]:
            owner.setdefault(d, b["slug"])
    users = {}
    for b in blocks:
        for c in b["_calls_raw"]:
            if c in owner and owner[c] != b["slug"]:
                users.setdefault(c, set()).add(b["slug"])
    common = {c for c, us in users.items() if len(us) > UBIQUITY}
    for b in blocks:
        mine = set(b["defines"])
        cross = {c for c in b["_calls_raw"]
                 if c in owner and c not in mine and owner[c] != b["slug"]}
        b["calls"] = sorted(cross - common)
        b["uses"] = sorted(cross & common)
        b["calls_blocks"] = sorted({owner[c] for c in b["calls"]})
    for b in blocks:
        b["called_by"] = sorted({o["slug"] for o in blocks if b["slug"] in o["calls_blocks"]})
    for b in blocks:
        b.pop("_calls_raw", None)
    return {b["slug"]: b for b in blocks}


def header_text(b, width=100):
    """The header as it should read. `sync` writes exactly this, plus the kept `!!` lines."""
    bar = "─" * max(4, width - 12 - len(b["slug"]) - len(b["title"]))
    out = [f"// ── [A:{b['slug']}] {b['title']} {bar}",
           "// anno — what this block touches, and what touches it."]
    if b["defines"]:
        out.append("//   defines:       " + " · ".join(b["defines"][:10])
                   + (f" … +{len(b['defines']) - 10}" if len(b["defines"]) > 10 else ""))
    if b["calls"]:
        out.append("//   -> calls:      " + " · ".join(b["calls"][:10])
                   + (f" … +{len(b['calls']) - 10}" if len(b["calls"]) > 10 else ""))
    if b["calls_blocks"]:
        out.append("//   -> blocks:     " + " · ".join(f"[A:{s}]" for s in b["calls_blocks"][:8])
                   + (f" … +{len(b['calls_blocks']) - 8}" if len(b["calls_blocks"]) > 8 else ""))
    if b["called_by"]:
        out.append("//   <- called by:  " + " · ".join(f"[A:{s}]" for s in b["called_by"][:8])
                   + (f" … +{len(b['called_by']) - 8}" if len(b["called_by"]) > 8 else ""))
    for n in b["notes"]:
        out.append("//   " + n.lstrip())
    return out


def cmd_scan(args):
    lines, blocks = parse_blocks(args.file)
    cross_edges(blocks)
    payload = {
        "project": os.path.basename(args.file),
        "file": os.path.relpath(args.file, HERE),
        "blocks": [{k: v for k, v in b.items() if not k.startswith("_")} for b in blocks],
    }
    out = args.json or SNAPSHOT
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
    # the navigation copy: same bytes, in the place `topos anno` looks
    if not args.no_topos:
        os.makedirs(TOPOS_HOME, exist_ok=True)
        nav = dict(payload, root=HERE, abs_file=os.path.abspath(args.file))
        with open(os.path.join(TOPOS_HOME, "memory-atlas.json"), "w", encoding="utf-8") as f:
            json.dump(nav, f, ensure_ascii=False, indent=1)
    anchored = sum(1 for b in blocks if b["anchored"])
    print(f"blocks={len(blocks)} anchored={anchored} unanchored={len(blocks) - anchored} → {out}")
    return 0


def cmd_sync(args):
    lines, blocks = parse_blocks(args.file)
    cross_edges(blocks)
    for b in reversed(blocks):          # bottom-up: earlier spans keep their indices
        lines[b["head"]:b["head_end"]] = header_text(b)
    with open(args.file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"rewrote {len(blocks)} headers in {args.file}")
    return 0


def cmd_check(args):
    """A header that names a function nobody defines is the failure this whole layer targets:
    prose that describes a mechanism the file does not have. Fail loudly, with the anchor."""
    lines, blocks = parse_blocks(args.file)
    cross_edges(blocks)
    defined = {d for b in blocks for d in b["defines"]}
    bad = []
    # "backtick = identifier" does not hold: prose quotes preset names (`themes`, `synergy`),
    # config values and CSS classes in backticks too, and flagging those buries the one claim
    # that matters. A claim about a MECHANISM looks like one: camelCase, or written with ().
    CLAIM = re.compile(r"`([a-z][a-z0-9$_]*[A-Z][\w$]*)`|`([A-Za-z_$][\w$]*)\(\)`")
    for b in blocks:
        for m in CLAIM.finditer(" ".join(b["notes"])):
            name = m.group(1) or m.group(2)
            if name not in defined and name not in ("DATA", "CFG"):
                bad.append((b["slug"], name))
    dup = [b["slug"] for b in blocks if b["slug"].endswith(("-2", "-3", "-4"))]
    for slug, name in bad:
        print(f"broken claim: [A:{slug}] names `{name}` — no such definition", file=sys.stderr)
    if dup:
        print(f"note: auto-suffixed slugs (title collision): {' '.join(dup)}", file=sys.stderr)
    return 1 if bad else 0


def resolve(slug, path):
    """Line of an anchor RIGHT NOW — read off the file, never off the snapshot."""
    with open(path, encoding="utf-8") as f:
        for i, l in enumerate(f, 1):
            m = ANCHOR_RE.match(l)
            if m and m.group(1) == slug:
                return i
    return None


def cmd_show(args):
    lines, blocks = parse_blocks(args.file)
    cross_edges(blocks)
    hit = next((b for b in blocks if b["slug"] == args.slug), None)
    if not hit:
        near = [b["slug"] for b in blocks if args.slug in b["slug"]][:8]
        print(f"no anchor [A:{args.slug}]" + (f" — close: {' '.join(near)}" if near else ""), file=sys.stderr)
        return 1
    line = resolve(args.slug, args.file) or hit["head"] + 1
    print(f"[A:{hit['slug']}] {hit['title']}")
    print(f"  {os.path.relpath(args.file, HERE)}:{line}  ({hit['lines']} lines)")
    if hit["defines"]:
        print("  defines:      " + " · ".join(hit["defines"]))
    if hit["calls"]:
        print("  -> calls:     " + " · ".join(hit["calls"]))
    if hit["called_by"]:
        print("  <- called by: " + " · ".join(hit["called_by"]))
    for n in hit["notes"]:
        print("  " + n)
    return 0


def cmd_list(args):
    lines, blocks = parse_blocks(args.file)
    cross_edges(blocks)
    pat = args.pattern.lower() if args.pattern else None
    for b in blocks:
        hay = (b["slug"] + " " + b["title"] + " " + " ".join(b["defines"])).lower()
        if pat and pat not in hay:
            continue
        mark = " " if b["anchored"] else "·"
        print(f"{mark}{b['head'] + 1:5d}  [A:{b['slug']}]".ljust(46) + f"{b['title'][:60]}")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--file", default=TEMPLATE)
    sub = ap.add_subparsers(dest="cmd")
    p = sub.add_parser("scan"); p.add_argument("--json"); p.add_argument("--no-topos", action="store_true")
    sub.add_parser("sync")
    sub.add_parser("check")
    p = sub.add_parser("show"); p.add_argument("slug")
    p = sub.add_parser("list"); p.add_argument("pattern", nargs="?")
    args = ap.parse_args()
    fn = {"scan": cmd_scan, "sync": cmd_sync, "check": cmd_check,
          "show": cmd_show, "list": cmd_list}.get(args.cmd or "list")
    sys.exit(fn(args))


if __name__ == "__main__":
    main()
