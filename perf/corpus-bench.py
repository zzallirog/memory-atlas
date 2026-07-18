#!/usr/bin/env python3
"""corpus-bench — search cost across corpora, measured in the page's own functions.

Why CDP and not a reimplementation: the thing under test is `runSearch()` as it ships.
A node-side copy of the ranking loop would measure the copy. This drives a real Chrome
over the DevTools protocol and calls the page's globals, so a regression in the template
shows up here and a regression in a rewrite of the template does not hide.

What it measures, per corpus × query-class:
  ms       — synchronous cost of runSearch(q): queryTerms + rebuildMatch (canvas filter)
             + buildDrop (pool build, coverage sort) + renderLens. The rAF draw it
             requests is NOT included — that is the render bench's axis (frame-bench.mjs).
  pool     — sHits.length: how many rows the dropdown actually has.
  matched  — matchSet.size: how many nodes the canvas lit up.
             pool==0 while matched>0 is the v2.18.0 empty-dropdown bug; it is a listed
             query class here precisely so it cannot come back unnoticed.
  rerank   — client-side semantic pass over the baked int8 vectors with a synthetic
             unit query vector. EXCLUDES the query-embedding round-trip to Ollama, which
             is network cost and does not scale with the corpus. Reported only if the
             page carries vecs (built with --search-vecs).

usage:
  python3 corpus-bench.py --corpus mac=/path/mac.html --corpus psy=/path/psy.html \
      --queries perf/corpus-queries.json [--reps 7] [--out results.json]
"""
import argparse
import json
import os
import shutil
import socket
import statistics
import subprocess
import sys
import tempfile
import time
import urllib.request

try:
    import websocket  # websocket-client
except ImportError:
    sys.exit("need websocket-client: pip3 install websocket-client")

CHROME = os.environ.get(
    "CHROME_BIN", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
)

# Query classes, not query strings: a corpus in Ukrainian and a corpus in Russian share no
# vocabulary, so the comparable unit is the SHAPE of the query. Per-corpus terms live in the
# --queries file; the class is what lines up across columns.
CLASSES = ["one-term", "two-term", "three-term", "punct-only", "no-hit"]


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


class Page:
    """One headless Chrome with one file:// tab, driven over CDP."""

    def __init__(self, url, port=None):
        self.port = port or free_port()
        self.profile = tempfile.mkdtemp(prefix="corpus-bench-")
        self.proc = subprocess.Popen(
            [
                CHROME,
                "--headless=new",
                "--remote-debugging-port=%d" % self.port,
                "--user-data-dir=%s" % self.profile,
                "--no-first-run",
                "--no-default-browser-check",
                "--disable-extensions",
                # a hidden window still lays out, and the search path reads element sizes
                "--window-size=1600,900",
                url,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        self.ws = None
        self.msg_id = 0
        self._connect()

    def _connect(self, timeout=60):
        deadline = time.time() + timeout
        target = None
        while time.time() < deadline:
            try:
                raw = urllib.request.urlopen(
                    "http://127.0.0.1:%d/json/list" % self.port, timeout=2
                ).read()
                for t in json.loads(raw):
                    if t.get("type") == "page" and t.get("webSocketDebuggerUrl"):
                        target = t["webSocketDebuggerUrl"]
                        break
                if target:
                    break
            except Exception:
                pass
            time.sleep(0.3)
        if not target:
            raise RuntimeError("chrome did not expose a page target")
        # a 5MB+ page can take a while to answer the first evaluate; do not race it.
        # suppress_origin: Chrome rejects a debugger socket that carries an Origin header
        # (403, "use --remote-allow-origins"). Dropping the header is the narrow fix; the
        # flag would open the debug port to every origin the browser can be pointed at.
        self.ws = websocket.create_connection(target, timeout=300, suppress_origin=True)
        self.send("Runtime.enable")

    def send(self, method, **params):
        self.msg_id += 1
        mid = self.msg_id
        self.ws.send(json.dumps({"id": mid, "method": method, "params": params}))
        while True:
            msg = json.loads(self.ws.recv())
            if msg.get("id") == mid:
                if "error" in msg:
                    raise RuntimeError("%s: %s" % (method, msg["error"]))
                return msg.get("result", {})

    def js(self, expr, await_promise=False):
        r = self.send(
            "Runtime.evaluate",
            expression=expr,
            returnByValue=True,
            awaitPromise=await_promise,
        )
        if r.get("exceptionDetails"):
            desc = r["exceptionDetails"].get("exception", {}).get("description")
            raise RuntimeError("page threw: %s" % desc)
        return r["result"].get("value")

    def wait_ready(self, timeout=180):
        """The page builds its graph asynchronously; do not time a half-built index."""
        deadline = time.time() + timeout
        last = None
        # `nodes`/`sHits` are top-level `const`/`let` in a classic script, so they are NOT
        # properties of `window` — probing `window.nodes` reports undefined on a page that is
        # perfectly ready. Name them bare and let the evaluate run in the same lexical scope.
        while time.time() < deadline:
            try:
                if self.js(
                    "typeof runSearch === 'function' && typeof nodes !== 'undefined'"
                    " && nodes.length > 0 && typeof sHits !== 'undefined'"
                ):
                    return
            except Exception as e:  # the tab is still parsing; retry
                last = e
            time.sleep(0.4)
        raise RuntimeError("page never became ready (%s)" % last)

    def close(self):
        try:
            if self.ws:
                self.ws.close()
        except Exception:
            pass
        self.proc.terminate()
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()
        shutil.rmtree(self.profile, ignore_errors=True)


MEASURE = """(() => {
  // clear first: buildDrop keeps a render cache keyed on the last query, and repeating the
  // same string would time the cache rather than the search.
  runSearch('');
  const t0 = performance.now();
  runSearch(%(q)s);
  const t1 = performance.now();
  return { ms: t1 - t0,
           pool: (typeof sHits === 'undefined' ? -1 : sHits.length),
           matched: (typeof matchSet === 'undefined' ? -1 : matchSet.size) };
})()"""

RERANK = """(() => {
  // `typeof DATA`, not `window.DATA`: DATA is a top-level const and never lands on window.
  // Probing the window property reported "no vectors" on a page that carried 768-dim vectors
  // for every node — a silent null that reads exactly like "this build has no semantics".
  if (typeof DATA === 'undefined' || !DATA.vecs || !DATA.vecs.ids) return null;
  const rows = normVecs();                    // dequant + normalise (cached after first call)
  const dim = DATA.vecs.dim;
  // A synthetic unit vector, not a real query embedding: this half of the semantic pass is
  // the one that scales with the corpus. The other half is one Ollama round-trip.
  const qv = new Array(dim).fill(1 / Math.sqrt(dim));
  const t0 = performance.now();
  let dotSink = 0;
  for (let i = 0; i < rows.length; i++) {
    let dot = 0; const r = rows[i];
    for (let j = 0; j < r.length; j++) dot += r[j] * qv[j];
    dotSink += dot;                           // keep the loop from being optimised away
  }
  const t1 = performance.now();
  return { ms: t1 - t0, vecs: rows.length, dim, model: DATA.vecs.model,
           sink: dotSink > -Infinity };
})()"""


def bench_corpus(name, path, queries, reps):
    url = "file://" + os.path.abspath(path)
    page = Page(url)
    try:
        page.wait_ready()
        stats = page.js(
            "({nodes: nodes.length, edges: (typeof edges!=='undefined'?edges.length:-1),"
            " vecs: !!(typeof DATA !== 'undefined' && DATA.vecs)})"
        )
        out = {
            "corpus": name,
            "file": os.path.abspath(path),
            "bytes": os.path.getsize(path),
            "nodes": stats["nodes"],
            "edges": stats["edges"],
            "has_vecs": stats["vecs"],
            "queries": [],
        }
        for cls in CLASSES:
            q = queries[cls]
            samples, pool, matched = [], None, None
            page.js(MEASURE % {"q": json.dumps(q)})  # warm-up, discarded
            for _ in range(reps):
                r = page.js(MEASURE % {"q": json.dumps(q)})
                samples.append(r["ms"])
                pool, matched = r["pool"], r["matched"]
            out["queries"].append(
                {
                    "class": cls,
                    "q": q,
                    "ms_med": round(statistics.median(samples), 3),
                    "ms_min": round(min(samples), 3),
                    "ms_max": round(max(samples), 3),
                    "pool": pool,
                    "matched": matched,
                }
            )
        out["rerank"] = page.js(RERANK)
        return out
    finally:
        page.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", action="append", required=True,
                    metavar="NAME=FILE.html", help="repeatable")
    ap.add_argument("--queries", required=True,
                    help="JSON: {corpus: {class: query}} — classes: %s" % ", ".join(CLASSES))
    ap.add_argument("--reps", type=int, default=7)
    ap.add_argument("--out", default="-")
    args = ap.parse_args()

    with open(args.queries, encoding="utf-8") as f:
        qmap = json.load(f)

    results = []
    for spec in args.corpus:
        if "=" not in spec:
            sys.exit("--corpus wants NAME=FILE, got %r" % spec)
        name, path = spec.split("=", 1)
        if name not in qmap:
            sys.exit("no query set for corpus %r in %s" % (name, args.queries))
        missing = [c for c in CLASSES if c not in qmap[name]]
        if missing:
            sys.exit("corpus %r missing query classes: %s" % (name, missing))
        print("... %s" % name, file=sys.stderr)
        results.append(bench_corpus(name, path, qmap[name], args.reps))

    blob = {
        "generated": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "reps": args.reps,
        "chrome": CHROME,
        "results": results,
    }
    text = json.dumps(blob, ensure_ascii=False, indent=2)
    if args.out == "-":
        print(text)
    else:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text + "\n")
        print("out: %s" % args.out, file=sys.stderr)


if __name__ == "__main__":
    main()
