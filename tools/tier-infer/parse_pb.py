#!/usr/bin/env python3
"""Parse Pressbooks 'Introduction to Psychology' glossary <dl> into a flat vault:
one .md per term (title = term, body = definition). Source CC BY (Open Ed Alberta).
Deterministic stdlib HTML parse of uniform <dt>/<dd> pairs."""
import html, re, os, sys, unicodedata
from html.parser import HTMLParser

SRC = sys.argv[1] if len(sys.argv) > 1 else "pb_gloss.html"
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.expanduser("~/atlas-tier-demo/vault")

class DL(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_dl = self.in_dt = self.in_dd = False
        self.cur_term = []
        self.cur_def = []
        self.pairs = []
    def handle_starttag(self, tag, attrs):
        if tag == "dl": self.in_dl = True
        elif self.in_dl and tag == "dt": self.in_dt = True; self.cur_term = []
        elif self.in_dl and tag == "dd": self.in_dd = True; self.cur_def = []
    def handle_endtag(self, tag):
        if tag == "dl": self.in_dl = False
        elif tag == "dt": self.in_dt = False
        elif tag == "dd":
            self.in_dd = False
            term = " ".join("".join(self.cur_term).split()).strip()
            defn = " ".join("".join(self.cur_def).split()).strip()
            if term and defn:
                self.pairs.append((term, defn))
    def handle_data(self, data):
        if self.in_dt: self.cur_term.append(data)
        elif self.in_dd: self.cur_def.append(data)

def slugify(t):
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode()
    t = re.sub(r"[^a-zA-Z0-9]+", "-", t).strip("-").lower()
    return t or "term"

raw = open(SRC, encoding="utf-8").read()
p = DL(); p.feed(raw)
pairs = p.pairs
os.makedirs(OUT, exist_ok=True)
seen = {}
written = 0
for term, defn in pairs:
    slug = slugify(term)
    if slug in seen:
        seen[slug] += 1; slug = f"{slug}-{seen[slug]}"
    else:
        seen[slug] = 0
    safe_term = term.replace('"', "'")
    body = html.unescape(defn)
    fm = (f"---\nname: \"{safe_term}\"\nsource: pressbooks-intro-psychology\n"
          f"license: CC-BY\n---\n\n{body}\n")
    open(os.path.join(OUT, f"{slug}.md"), "w", encoding="utf-8").write(fm)
    written += 1

# terms.json manifest for the tier-inference workflow (name + short def)
import json
manifest = [{"term": t, "def": html.unescape(d)[:220]} for t, d in pairs]
mpath = os.path.join(os.path.dirname(OUT), "terms.json")
json.dump(manifest, open(mpath, "w", encoding="utf-8"), ensure_ascii=False)
print(f"terms parsed: {len(pairs)}  written: {written}  out: {OUT}")
print(f"manifest: {mpath} ({len(manifest)} terms)")
for term, defn in pairs[:5]:
    print(f"  - {term[:40]:40} | {defn[:60]}")
