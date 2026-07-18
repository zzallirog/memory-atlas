// repro-edges.mjs — BUG 1: "при большом количестве еджей линии между нодами глючат"
// Sweeps vaults of increasing edge count; per vault:
//   - counts edges actually submitted to the renderer + Path2D subpath count + stroke() calls
//   - burst-screenshots N frames of a STATIC scene (no camera motion, sim settled)
//   - numerically diffs consecutive frames (flicker) and measures ink (mean luma of edge layer)
//   - probes the alpha-accumulation mechanism directly on a scratch canvas in-page
//
// usage:  node repro-edges.mjs <out-dir> <vault.html> [<vault.html> ...]
// playwright is not vendored in this repo — resolved from the known local installs
// (or $PLAYWRIGHT_DIR); no node_modules symlink in the tree. See perf/README.md.
import { pathToFileURL } from 'url';
import fs from 'fs';
import { createRequire } from 'module';
const chromium = await (async () => {
  const cands = [process.env.PLAYWRIGHT_DIR, `${process.env.HOME}/.claude/ida/qa`,
    `${process.env.HOME}/claude-substrate/ida/qa`].filter(Boolean);
  for (const d of cands) {
    try { return createRequire(`${d}/x.js`)('playwright').chromium; } catch (e) {}
  }
  throw new Error('playwright not found; set PLAYWRIGHT_DIR to a dir containing node_modules/playwright');
})();

const OUT = process.argv[2];
const FILES = process.argv.slice(3);
fs.mkdirSync(OUT, { recursive: true });

// no bundled chromium in the ms-playwright cache on this box -> installed Chrome.
// NOTE: its GPU process segfaults under headless here and falls back to SwiftShader,
// so RASTER TIMINGS from this harness are not trustworthy. Correctness/pixel checks are.
const LAUNCH = {
  channel: 'chrome',
  args: ['--enable-gpu-rasterization', '--ignore-gpu-blocklist', '--disable-frame-rate-limit', '--no-sandbox'],
};
// one browser per vault: Chrome here is flaky about extra pages after a GPU crash
const results = [];
for (const FILE of FILES) {
  const tag = FILE.split('/').pop().replace(/\.html$/, '');
  let browser, page;
  for (let a = 0; a < 3 && !page; a++) {
    try {
      browser = await chromium.launch(LAUNCH);
      page = await browser.newPage({ viewport: { width: 1600, height: 1000 }, deviceScaleFactor: 1 });
    } catch (e) {
      console.log(`  launch attempt ${a + 1} failed: ${String(e).slice(0, 90)}`);
      try { await browser?.close(); } catch (_) {}
      await new Promise(r => setTimeout(r, 1500));
    }
  }
  if (!page) { console.log(`SKIP ${tag}: browser would not start`); continue; }

  // instrument BEFORE any script runs: count Path2D verbs and stroke() calls per frame
  await page.addInitScript(() => {
    window.__st = { strokes: 0, pathStrokes: 0, moveTo: 0, lineTo: 0, curveTo: 0, paths: 0 };
    const P = window.Path2D;
    window.Path2D = function (...a) {
      const p = new P(...a); window.__st.paths++;
      return p;
    };
    window.Path2D.prototype = P.prototype;
    for (const m of ['moveTo', 'lineTo', 'quadraticCurveTo']) {
      const key = m === 'quadraticCurveTo' ? 'curveTo' : m;
      const orig = P.prototype[m];
      P.prototype[m] = function (...a) { window.__st[key]++; return orig.apply(this, a); };
    }
    const C = CanvasRenderingContext2D.prototype;
    const os = C.stroke;
    C.stroke = function (...a) { window.__st.strokes++; if (a[0]) window.__st.pathStrokes++; return os.apply(this, a); };
  });

  await page.goto(pathToFileURL(FILE).href, { waitUntil: 'load' });
  await page.waitForTimeout(4000);

  // edges ON; particles + magnet OFF so the scene is genuinely static
  // (particles animate every frame and would masquerade as edge flicker)
  await page.evaluate(() => {
    const t = document.getElementById('edgesOn');
    if (t && !t.classList.contains('on')) t.click();
    for (const id of ['particles', 'magnet']) {
      const e = document.getElementById(id);
      if (e && e.classList.contains('on')) e.click();
    }
  });
  await page.waitForTimeout(2500);
  // let the force sim cool fully so the scene is STATIC (isolates flicker from motion)
  await page.evaluate(() => { try { sim.alpha(0); sim.stop(); } catch (e) {} });
  await page.waitForTimeout(800);

  const info = await page.evaluate(() => ({
    nodes: nodes.length,
    edges: edges.length,
    edgesOn: document.getElementById('edgesOn').classList.contains('on'),
    k: transform.k,
    alpha: sim.alpha(),
    ea: +document.getElementById('edgeAlpha').value,
  }));

  // one clean frame with counters zeroed => per-frame draw volume
  const perFrame = await page.evaluate(() => new Promise(res => {
    window.__st = { strokes: 0, pathStrokes: 0, moveTo: 0, lineTo: 0, curveTo: 0, paths: 0 };
    requestDraw();
    requestAnimationFrame(() => requestAnimationFrame(() => res({ ...window.__st })));
  }));

  // burst of frames on a static scene: any pixel delta = flicker, not motion.
  // read the CANVAS directly (page.screenshot goes through the compositor and stalls when
  // the page commits no new frame; the canvas bitmap is the actual render output anyway)
  const shots = [];
  const frames = [];
  for (let i = 0; i < 8; i++) {
    const f = await page.evaluate(() => new Promise(res => {
      requestDraw();
      requestAnimationFrame(() => requestAnimationFrame(() => {
        const d = ctx.getImageData(0, 0, canvas.width, canvas.height).data;
        // downsample to a 160x100 luma grid + exact ink sum (sensitive to 1px differences)
        const W = canvas.width, H = canvas.height, GW = 160, GH = 100;
        const grid = new Float64Array(GW * GH);
        let ink = 0;
        for (let y = 0; y < H; y++) {
          const gy = (y * GH / H) | 0;
          for (let x = 0; x < W; x++) {
            const p = (y * W + x) * 4;
            const l = 0.299 * d[p] + 0.587 * d[p + 1] + 0.114 * d[p + 2];
            ink += l;
            grid[gy * GW + ((x * GW / W) | 0)] += l;
          }
        }
        res({ ink: Math.round(ink), grid: Array.from(grid, v => Math.round(v)), png: canvas.toDataURL('image/png') });
      }));
    }));
    frames.push({ ink: f.ink, grid: f.grid });
    if (i < 3) {
      const p = `${OUT}/${tag}-f${i}.png`;
      fs.writeFileSync(p, Buffer.from(f.png.split(',')[1], 'base64'));
      shots.push(p);
    }
    await page.waitForTimeout(80);
  }
  // frame-to-frame delta on a STATIC scene: >0 means the same geometry rasterizes differently
  const flicker = [];
  for (let i = 1; i < frames.length; i++) {
    let d = 0, mx = 0;
    for (let j = 0; j < frames[i].grid.length; j++) {
      const q = Math.abs(frames[i].grid[j] - frames[i - 1].grid[j]);
      d += q; mx = Math.max(mx, q);
    }
    flicker.push({ dInk: frames[i].ink - frames[i - 1].ink, gridAbsDelta: d, maxCell: mx });
  }

  // ---- mechanism probe: does one stroke() over a multi-subpath Path2D accumulate alpha? ----
  // draws two overlapping translucent segments (a) as 2 separate strokes, (b) as 1 Path2D + 1 stroke
  // and reads the pixel at the crossing. Equal values => batching flattens density.
  const alphaProbe = await page.evaluate(() => {
    const c = document.createElement('canvas'); c.width = 100; c.height = 100;
    const g = c.getContext('2d');
    const paint = (batched) => {
      // opaque dark backdrop: read the composited LUMA, exactly like the atlas paints
      // translucent edges over its background
      g.globalCompositeOperation = 'source-over';
      g.fillStyle = '#000'; g.fillRect(0, 0, 100, 100);
      g.strokeStyle = 'rgba(255,255,255,0.20)'; g.lineWidth = 6;
      const N = 4;   // 4 overlapping strands, as in a dense edge tangle
      if (batched) {
        const p = new Path2D();
        for (let i = 0; i < N; i++) { p.moveTo(0, 50); p.lineTo(100, 50); }
        g.stroke(p);
      } else {
        for (let i = 0; i < N; i++) { g.beginPath(); g.moveTo(0, 50); g.lineTo(100, 50); g.stroke(); }
      }
      return g.getImageData(50, 50, 1, 1).data[0];   // luma of the overlap, over black
    };
    const perEdge = paint(false), batched = paint(true);
    return { perEdge, batched, ratio: +(perEdge / Math.max(1, batched)).toFixed(2) };
  });

  // ---- overlap census: how many drawn edges share a screen pixel (density of crossings) ----
  const overlap = await page.evaluate(() => {
    const W = innerWidth, H = innerHeight;
    const grid = new Int32Array(W * H / 64 | 0); // coarse 8x8 buckets
    const gw = Math.ceil(W / 8);
    let drawn = 0, buckets = new Set();
    const sx = n => n.x * transform.k + transform.x, sy = n => n.y * transform.k + transform.y;
    for (const e of edges) {
      const s = e.source, t = e.target;
      if (!visible(s) || !visible(t)) continue;
      drawn++;
      const x0 = sx(s), y0 = sy(s), x1 = sx(t), y1 = sy(t);
      const steps = Math.max(1, Math.hypot(x1 - x0, y1 - y0) / 8 | 0);
      for (let i = 0; i <= steps; i++) {
        const x = (x0 + (x1 - x0) * i / steps) / 8 | 0, y = (y0 + (y1 - y0) * i / steps) / 8 | 0;
        if (x < 0 || y < 0 || x >= gw || y >= H / 8) continue;
        const idx = y * gw + x;
        if (idx < grid.length) { grid[idx]++; buckets.add(idx); }
      }
    }
    let max = 0, sum = 0, hot = 0;
    for (const i of buckets) { max = Math.max(max, grid[i]); sum += grid[i]; if (grid[i] > 8) hot++; }
    return { drawn, cells: buckets.size, maxPerCell: max, meanPerCell: +(sum / (buckets.size || 1)).toFixed(2), hotCells: hot };
  });

  results.push({ tag, info, perFrame, alphaProbe, overlap, flicker, ink: frames.map(f => f.ink), shots });
  console.log(`\n=== ${tag} ===`);
  console.log('  graph      ', JSON.stringify(info));
  console.log('  per frame  ', JSON.stringify(perFrame));
  console.log('  alphaProbe ', JSON.stringify(alphaProbe), alphaProbe.perEdge === alphaProbe.batched ? '<-- IDENTICAL: batching flattens overlap alpha' : '(differs)');
  console.log('  overlap    ', JSON.stringify(overlap));
  console.log('  flicker    ', JSON.stringify(flicker.map(f => f.gridAbsDelta)), 'maxCell', Math.max(...flicker.map(f => f.maxCell)));
  await page.close();
  await browser.close();
}
fs.writeFileSync(`${OUT}/edges-report.json`, JSON.stringify(results, null, 2));
console.log('\nreport:', `${OUT}/edges-report.json`);
