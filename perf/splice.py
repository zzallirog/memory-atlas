#!/usr/bin/env python3
"""splice — re-render a built atlas HTML with a (modified) template, reusing the
embedded DATA payload verbatim. A/B perf tooling: same data, different code.

usage: splice.py <built-vault.html> <template.html> <out.html>
"""
import os
import re
import sys


def main():
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    vault, tpl_path, out = sys.argv[1:4]
    src = open(vault, encoding="utf-8").read()
    i = src.index("const DATA = ")
    j = src.index("\n", i)
    payload = src[i + len("const DATA = "):j].rstrip().rstrip(";")
    if not payload.startswith("{"):
        sys.exit("splice: DATA payload not found (expected inline JSON object)")
    m = re.search(r"\? CFG\.lang : '(\w+)'", src)
    lang = m.group(1) if m else "ru"
    tpl = open(tpl_path, encoding="utf-8").read()
    # d3: env → vendor/ next to the template → vendor/ next to this script (repo layout)
    here = os.path.dirname(os.path.abspath(__file__))
    cands = [os.environ.get("ATLAS_D3"),
             os.path.join(os.path.dirname(os.path.abspath(tpl_path)), "vendor", "d3.v7.min.js"),
             os.path.join(here, "..", "vendor", "d3.v7.min.js")]
    d3p = next(c for c in cands if c and os.path.exists(c))
    d3 = open(d3p, encoding="utf-8").read()
    html = (tpl.replace("/*__D3__*/", d3)
               .replace('"__DATA__"', payload)
               .replace("'__LANG__'", f"'{lang}'"))
    for marker in ("__DATA__", "/*__D3__*/"):
        if marker in html:
            sys.exit(f"splice: marker {marker} survived — template/vault mismatch")
    open(out, "w", encoding="utf-8").write(html)
    print(f"{out} · {len(html)} bytes · lang={lang}")


if __name__ == "__main__":
    main()
