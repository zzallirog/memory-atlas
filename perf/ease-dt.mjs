// ease-dt.mjs — do the paint-path eases run at the same speed on a slow machine?
//
// Hypothesis under test: the label and LOD eases advance PER FRAME with a bare
// constant (`densKS += (dT - densKS) * 0.22`, `la += (1 - la) * 0.3`,
// `n._la = la0 * 0.62`), so their duration is a function of frame RATE, not of
// wall-clock time. The magnet was already fixed this way (see repro-magnet-dt);
// this measures the same disease in the label/LOD path, before and after the
// `easeK()` conversion.
//
// Method is repro-magnet-dt's: same page, same scripted action, CDP CPU
// throttling to move the frame rate, and every sample taken at a fixed
// WALL-CLOCK offset. A dt-correct ease reaches the same value at the same
// wall-clock time at any rate; a per-frame ease stretches with the frame time.
//
// Reported metric: t95 — wall-clock ms until densKS has covered 95% of the
// distance to its target after one programmatic zoom, plus the frame count that
// bought it. Flat t95 across rates is the pass condition; the OLD build is
// expected to stretch roughly in proportion to the throttle.
//
// usage: node perf/ease-dt.mjs <out-dir> <old.html> <new.html> [rates...]
import { pathToFileURL } from 'url';
import fs from 'fs';
import { createRequire } from 'module';

const chromium = await (async () => {
  const cands = [process.env.PLAYWRIGHT_DIR, `${process.env.HOME}/.claude/ida/qa`,
    `${process.env.HOME}/claude-substrate/ida/qa`].filter(Boolean);
  for (const d of cands) {
    try { return createRequire(`${d}/x.js`)('playwright').chromium; } catch (e) {}
  }
  throw new Error('playwright not found; set PLAYWRIGHT_DIR');
})();

const OUT = process.argv[2];
const BUILDS = { old: process.argv[3], new: process.argv[4] };
const RATES = (process.argv.slice(5).length ? process.argv.slice(5) : ['1', '4', '8']).map(Number);
if (!OUT || !BUILDS.old || !BUILDS.new) {
  console.error('usage: node perf/ease-dt.mjs <out-dir> <old.html> <new.html> [rates...]');
  process.exit(1);
}
fs.mkdirSync(OUT, { recursive: true });

// wall-clock offsets after the zoom lands (ms)
const SAMPLES = Array.from({ length: 30 }, (_, i) => 50 + i * 50).concat([1800, 2400]);
const REPEATS = 3;   // run-to-run drift on a warm laptop is larger than some of the effects here
const LAUNCH = { channel: 'chrome', args: ['--enable-gpu-rasterization', '--ignore-gpu-blocklist', '--no-sandbox'] };

const rows = [];
for (const [name, file] of Object.entries(BUILDS)) {
  for (const rate of RATES) {
   for (let rep = 0; rep < REPEATS; rep++) {
    let browser, page;
    for (let a = 0; a < 3 && !page; a++) {
      try {
        browser = await chromium.launch(LAUNCH);
        page = await browser.newPage({ viewport: { width: 1600, height: 1000 }, deviceScaleFactor: 1 });
      } catch (e) {
        try { await browser?.close(); } catch (_) {}
        await new Promise(r => setTimeout(r, 1500));
      }
    }
    if (!page) { console.log(`SKIP ${name} rate ${rate}: browser would not start`); continue; }

    const errs = [];
    page.on('pageerror', e => errs.push(String(e)));
    await page.goto(pathToFileURL(file).href, { waitUntil: 'load' });
    await page.waitForTimeout(4000);

    // quiet the scene: no magnet, no particles — only the label/LOD ease may move
    await page.evaluate(() => {
      const on = id => document.getElementById(id)?.classList.contains('on');
      if (on('magnet')) document.getElementById('magnet').click();
      if (on('particles')) document.getElementById('particles').click();
      // edges ON: a cheap frame is not slowed by CPU throttling at all, and then the
      // throttle rate is not the axis it looks like — the FRAME INTERVAL is, so make
      // the frame expensive enough that the throttle actually moves it (repro-magnet-dt's
      // trick), and report against the interval this run really ran at.
      if (!on('edgesOn')) document.getElementById('edgesOn').click();
      sim.alpha(0); sim.stop();
    });
    await page.waitForTimeout(1200);

    const cdp = await page.context().newCDPSession(page);
    await cdp.send('Emulation.setCPUThrottlingRate', { rate });
    await page.waitForTimeout(800);

    // frame counter + baseline
    await page.evaluate(() => {
      window.__f = 0;
      const oRAF = window.requestAnimationFrame.bind(window);
      window.requestAnimationFrame = cb => oRAF(ts => { window.__f++; cb(ts); });
    });

    // One programmatic zoom, centred ON a node. densTargetK returns 0 when fewer than one
    // node is in frame, so a zoom into empty space gives the ease nothing to travel — the
    // first version of this harness measured exactly that and reported a flat zero.
    const start = await page.evaluate(() => {
      const k0 = d3.zoomTransform(canvas).k;
      const cx = nodes.reduce((a, n) => a + n.x, 0) / nodes.length;
      const cy = nodes.reduce((a, n) => a + n.y, 0) / nodes.length;
      let best = nodes[0], bd = Infinity;
      for (const n of nodes) { const d = Math.hypot(n.x - cx, n.y - cy); if (d < bd) { bd = d; best = n; } }
      const k = k0 * 12;   // deep enough that ≤7 notes stay in frame: densTargetK's full-body step
      d3.select(canvas).call(zoom.transform,
        d3.zoomIdentity.translate(W / 2 - k * best.x, H / 2 - k * best.y).scale(k));
      requestDraw();
      return { k0, dens: typeof densKS === 'number' ? densKS : null, f: window.__f };
    });
    if (start.dens === null) { console.log(`SKIP ${name}/${rate}: densKS not reachable`); await browser.close(); continue; }

    const t0 = Date.now();
    const trace = [];
    for (const s of SAMPLES) {
      const wait = s - (Date.now() - t0);
      if (wait > 0) await page.waitForTimeout(wait);
      const v = await page.evaluate(() => ({
        dens: densKS, target: typeof densTargetK === 'function' ? null : null, f: window.__f,
      }));
      trace.push({ t: Date.now() - t0, dens: v.dens, frames: v.f - start.f });
    }
    // settle value = last sample (the ease is asymptotic; 2.6s is far past any of them)
    const end = trace[trace.length - 1].dens;
    const last = trace[trace.length - 1];
    const dt = last.frames ? +(last.t / last.frames).toFixed(1) : null;   // mean interval over the whole window (idle frames included)
    const span = end - start.dens;
    let t95 = null, f95 = null;
    if (Math.abs(span) > 0.01) {
      for (const p of trace) {
        if (Math.abs(p.dens - start.dens) >= 0.95 * Math.abs(span)) { t95 = p.t; f95 = p.frames; break; }
      }
    }
    rows.push({ build: name, rate, rep, dt, dtLive: f95 ? +(t95 / f95).toFixed(1) : null, from: +start.dens.toFixed(3), to: +end.toFixed(3), t95, f95, errs: errs.slice(0, 3) });
    console.log(`${name.padEnd(4)} rate ${String(rate).padStart(2)}× rep${rep}  dtLive=${String(f95 ? (t95/f95).toFixed(1) : '—').padStart(6)}ms  t95=${t95 === null ? 'n/a' : t95 + 'ms'} (${f95} frames)${errs.length ? '  ERR ' + errs[0] : ''}`);
    await browser.close();
   }
  }
}

fs.writeFileSync(`${OUT}/ease-dt.json`, JSON.stringify({ rates: RATES, rows }, null, 2));
console.log(`\n→ ${OUT}/ease-dt.json`);
