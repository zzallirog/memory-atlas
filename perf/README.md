# perf/ — memory-atlas render bench

Target: **60–120 fps no matter what** (zoom, window size, dpr, text scale).
This harness makes that claim testable and makes regressions visible.

## Tools

- **frame-bench.mjs** — a matrix (viewport × dpr × text scale × zoom-K); per cell:
  a scripted pan of ~50 frames, collecting
  - `js` — draw-callback time (rAF wrapper);
  - `dt` — real rAF-to-rAF frametime under `--disable-frame-rate-limit`:
    the full frame cost (JS + raster + composite). The gap `dt − js` = non-JS cost;
  - canvas call volumes (prototype patch): arc/fill/stroke/fillText/….
  Text scale is set by clicking the A−/A+ stepper (0.15/click from the 1.25 default).
  ```
  cd <dir-with-playwright-in-node_modules>
  node frame-bench.mjs --file ~/.cache/atlas/vault.html --label v2105 [--quick]
  ```
- **focus-cell.mjs** — one cell, N pan repeats, medians across repeats:
  run-to-run spread (thermals/background) is larger than many effects — what
  decides is time-ADJACENT repeats, not single runs.
  ```
  node focus-cell.mjs <vault.html> <K> <repeats>
  ```
- **splice.py** — re-render a BUILT vault.html with a modified template:
  same DATA, different code → an A/B that is honest about the data.
  ```
  python3 perf/splice.py ~/.cache/atlas/vault.html memory-atlas.template.html /tmp/vault-new.html
  ```
- **profile-pan.mjs** — CDP Profiler during a pan, top self-time functions.
  The first step of ANY perf work here — see the rule below.
- **ego-flash.mjs / visual-check.mjs** — visual probes (ego-blur flash, layout sanity).

## Methodology traps

- GPU raster in headless is NOT dead: with `--enable-gpu-rasterization
  --ignore-gpu-blocklist --use-angle=gl-egl` the renderer is the real hardware
  (e.g. radeonsi). The bench prints the GL renderer — if it says
  SwiftShader/llvmpipe, the raster share of `dt` is inflated; compare builds only.
- **Profile first, build second.** Case 2026-07-10: canvas call volume (~1450
  arc/fill/stroke per frame) looked like the obvious target; Path2D-bucketing the
  circles cut calls 20× and ADDED ~2ms at overview zoom (native dispatch was never
  the cost; recording the Path2D was). The real cost sat in the string KEYS of the
  text-metrics caches (a ~400-char body concat per node per frame, then hashed) —
  55% of pan JS. The CPU profile answers; intuition doesn't.
- Run-to-run spread is ±20-30% — any conclusion below that needs focus-cell repeats.
- Headless vsync medians (16.7/33.3ms) are quantization, not signal — unlock the
  frame-rate limiter before trusting `dt`.

## Result snapshot (v2.10.4 → v2.10.5, quick matrix, dpr2, adjacent runs)

Changes: per-node text-layout memos (tileMetrics/label pass — numeric stamps
instead of string keys), metrics-object reuse (GC), minimap dot sprite, hot-knob
DOM caches; the data budget normalized by viewport area and TS².
Numbers: `fb-*-final.json` in this directory (1920×1080 dpr2: k1.0 12.4→6.4ms,
k2.3 15.8→9.4ms, k3.25 15.1→8.8ms; 1280×800: 4-6ms across all zooms).
