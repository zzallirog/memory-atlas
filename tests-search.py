#!/usr/bin/env python3
"""tests-search — behavioural tests for the search path, run in a real browser.

Why this file exists: `memory-atlas --self-test` has 54 green tests and not one of them
executes a line of the page's JavaScript. v2.18.0 shipped an empty dropdown on every
two-word query with that suite passing, and the fix for it silently disabled the semantic
reranker — also with that suite passing. A suite that cannot fail on the bugs you actually
ship is a comfort, not a check.

These drive a headless Chrome over CDP and call the page's own `runSearch` / `queryTerms`,
so they fail when the shipped behaviour breaks, not when a copy of it breaks.

usage:
  python3 tests-search.py                     # builds the bundled demo vault, then tests
  python3 tests-search.py --page built.html   # test an already-built page
"""
import argparse
import importlib.util
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))

_spec = importlib.util.spec_from_file_location(
    "corpus_bench", os.path.join(HERE, "perf", "corpus-bench.py")
)
corpus_bench = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(corpus_bench)
Page = corpus_bench.Page


class Results:
    def __init__(self):
        self.passed = 0
        self.failed = []

    def check(self, name, cond, detail=""):
        if cond:
            self.passed += 1
            print("ok   %s" % name)
        else:
            self.failed.append((name, detail))
            print("FAIL %s%s" % (name, ("  — " + detail) if detail else ""))


def build_demo():
    out = os.path.join(tempfile.mkdtemp(prefix="atlas-test-"), "demo.html")
    subprocess.run(
        [os.path.join(HERE, "memory-atlas"), "--demo", "--no-open", "--out", out],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    return out


def run(page_path):
    r = Results()
    page = Page("file://" + os.path.abspath(page_path))
    try:
        page.wait_ready()

        # --- queryTerms: the shared splitting rule -------------------------------------
        terms = lambda q: page.js("queryTerms(%s)" % repr_js(q))

        r.check("queryTerms splits on whitespace",
                terms("alpha beta") == ["alpha", "beta"])

        # deduped: cov below counts DISTINCT terms, so repetition must not inflate it
        r.check("queryTerms dedupes repeats",
                terms("tree tree forest") == ["tree", "forest"],
                str(terms("tree tree forest")))

        # edge punctuation trimmed: pasting a quoted title must still find that title
        r.check("queryTerms trims edge punctuation",
                terms("«alpha beta»") == ["alpha", "beta"],
                str(terms("«alpha beta»")))

        # interior punctuation survives — these are real identifiers in this domain
        r.check("queryTerms keeps interior punctuation",
                terms("ida-box c++") == ["ida-box", "c++"],
                str(terms("ida-box c++")))

        # A dash is not wrapper punctuation, so it survives as a term — and dedupes like any
        # other. It still drags in most of a vault, which is a property of the query.
        r.check("queryTerms dedupes a repeated dash",
                terms("— —") == ["—"], str(terms("— —")))

        # When trimming empties every token, fall back to the raw parts: a query made only of
        # wrapper punctuation still has to search for something.
        r.check("queryTerms falls back when trimming empties everything",
                terms("... ,,,") == ["...", ",,,"], str(terms("... ,,,")))

        # --- the v2.18.0 bug: two-word query lit the canvas and emptied the list --------
        # Two words drawn from DIFFERENT notes: under contiguous-substring matching no note
        # contains the pair, so the pool was 0 while the canvas highlighted both sets.
        pair = page.js("""(() => {
          const a = nodes[0], b = nodes.find(n => n.label && n.label !== a.label);
          const w = s => String(s || '').split(/\\s+/).filter(x => x.length > 3)[0];
          return [w(a.label), w(b.label)];
        })()""")
        if pair and all(pair):
            q = "%s %s" % (pair[0], pair[1])
            res = page.js("""(() => { runSearch(''); runSearch(%s);
              return { pool: sHits.length, matched: matchSet ? matchSet.size : 0 }; })()"""
                          % repr_js(q))
            r.check("two-term query fills the dropdown, not just the canvas",
                    not (res["matched"] > 0 and res["pool"] == 0),
                    "canvas=%d pool=%d for %r" % (res["matched"], res["pool"], q))
        else:
            r.check("two-term query fills the dropdown, not just the canvas", False,
                    "could not derive a two-word query from this vault")

        # --- coverage ranking: both terms beats either term ----------------------------
        cov_ok = page.js("""(() => {
          const t = queryTerms('alpha beta');
          return t.length === 2;
        })()""")
        r.check("coverage rank has two distinct terms to work with", cov_ok)

        # --- exact phrase survives a double space --------------------------------------
        # `phrase` is built from normalised terms; building it from the raw string made
        # "alpha  beta" (two spaces) match nothing that "alpha beta" matches.
        r.check("double space normalises to the same terms",
                terms("alpha  beta") == terms("alpha beta"),
                "%s vs %s" % (terms("alpha  beta"), terms("alpha beta")))

        # --- semantic gate: must not be closed by a healthy lexical pool ----------------
        # The reranker used to run only when the pool was nearly empty. Once the pool fills,
        # that gate never opens. Assert the call happens regardless of pool size.
        sem = page.js("""(() => {
          if (typeof DATA === 'undefined' || !DATA.vecs) return { skip: true };
          let called = 0;
          const real = semanticPass;
          semanticPass = function(q) { called++; };            // stub: no network in a test
          runSearch('');
          runSearch(%s);
          const poolFull = sHits.length;
          semanticPass = real;
          return { skip: false, called, poolFull };
        })()""" % repr_js(pair[0] if pair and pair[0] else "alpha"))
        if sem.get("skip"):
            print("skip semantic gate — page built without --search-vecs")
        else:
            r.check("semantic pass runs even when the lexical pool is full",
                    sem["called"] > 0,
                    "called=%d with pool=%d" % (sem["called"], sem["poolFull"]))

        # --- and it gives up rather than retrying a doomed request per keystroke --------
        if not sem.get("skip"):
            giveup = page.js("""(() => {
              let called = 0;
              const real = semanticPass;
              semanticPass = function() { called++; };
              semFails = SEM_GIVEUP;                 // pretend it has already failed twice
              runSearch(''); runSearch(%s);
              const afterGiveup = called;
              semFails = 0;                          // ...and that a later attempt succeeded
              runSearch(''); runSearch(%s);
              const afterReset = called;
              semanticPass = real; semFails = 0;
              return { afterGiveup, afterReset };
            })()""" % (repr_js(pair[0] if pair and pair[0] else "alpha"),
                       repr_js(pair[0] if pair and pair[0] else "alpha")))
            r.check("semantic pass stops after repeated failures",
                    giveup["afterGiveup"] == 0, "called %d times" % giveup["afterGiveup"])
            r.check("a success resets the give-up counter",
                    giveup["afterReset"] > giveup["afterGiveup"],
                    "%d -> %d" % (giveup["afterGiveup"], giveup["afterReset"]))

        # --- --barH survives the panels-hidden state -----------------------------------
        # `v` hides #bar but not #hudFoot; deriving the height from a display:none element
        # put the foot pills above the top edge of the window.
        bar = page.js("""(() => {
          publishBarH();
          const before = getComputedStyle(document.documentElement).getPropertyValue('--barH');
          document.body.classList.add('panels-hidden');
          publishBarH();
          const during = getComputedStyle(document.documentElement).getPropertyValue('--barH');
          document.body.classList.remove('panels-hidden');
          publishBarH();
          return { before: before.trim(), during: during.trim(), vh: window.innerHeight };
        })()""")
        r.check("--barH holds its value while the bar is hidden",
                bar["before"] == bar["during"],
                "before=%s during=%s (viewport %dpx)"
                % (bar["before"], bar["during"], bar["vh"]))
        r.check("--barH never approaches the full viewport height",
                bar["during"] == "" or int(bar["during"].replace("px", "") or 0) < bar["vh"] / 2,
                "during=%s viewport=%d" % (bar["during"], bar["vh"]))

        # --- title parking round-trips, including a rewrite while parked ----------------
        park = page.js("""(() => {
          const el = document.createElement('button');
          el.setAttribute('data-hint', 'hint text');
          el.title = 'original';
          document.body.appendChild(el);
          parkTitle(el);
          const parked = el.title;                       // '' while the hint card is up
          setLiveTitle(el, 'rewritten');                 // a live update arrives mid-hover
          const stillParked = el.title;                  // must stay '' — no OS tooltip
          unparkTitle();
          const restored = el.title;                     // the NEWER string, not the stale one
          el.remove();
          return { parked, stillParked, restored };
        })()""")
        r.check("parked title hides the native tooltip", park["parked"] == "")
        r.check("a rewrite while parked does not un-park it",
                park["stillParked"] == "", "title=%r" % park["stillParked"])
        r.check("unpark restores the newest title, not the stale one",
                park["restored"] == "rewritten", "restored=%r" % park["restored"])

        # --- mouseleave must unpark too -------------------------------------------------
        leave = page.js("""(() => {
          const el = document.createElement('button');
          el.setAttribute('data-hint', 'hint');
          el.title = 'tip';
          document.body.appendChild(el);
          parkTitle(el);
          document.dispatchEvent(new MouseEvent('mouseleave'));
          const after = el.title;
          el.remove();
          return after;
        })()""")
        r.check("leaving the document restores the title", leave == "tip",
                "title=%r after mouseleave" % leave)

        return r
    finally:
        page.close()


def repr_js(s):
    import json as _j
    return _j.dumps(s)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--page", help="an already-built atlas page; default builds --demo")
    args = ap.parse_args()

    page_path = args.page or build_demo()
    print("page: %s\n" % page_path)
    r = run(page_path)
    print("\n%d passed, %d failed" % (r.passed, len(r.failed)))
    for name, detail in r.failed:
        print("  FAIL %s — %s" % (name, detail))
    sys.exit(1 if r.failed else 0)


if __name__ == "__main__":
    main()
