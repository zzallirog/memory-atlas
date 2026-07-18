// frame-bench — honest frametime matrix for the memory-atlas render pipeline.
//
// Measures, per (viewport × dpr × text-scale × zoom-K) cell, during a scripted pan:
//   jsMed/jsP95 — draw-callback JS ms (rAF wrapper, the PERF-AUDIT-20260710 method)
//   dtMed/dtP95 — real rAF-to-rAF frame delta with the frame-rate limit OFF:
//                 full frame cost (JS + raster + composite) — the "frametime" axis
//                 the JS-only timing can't see. Headless Chromium rasters on CPU
//                 (Skia software) unless the GPU probe below says otherwise, so
//                 absolute dt overstates a live GPU — COMPARE builds, don't quote fps.
//   calls/frame — canvas primitive volumes (prototype patch): arc/fill/stroke/fillText/…
//
// usage: node frame-bench.mjs --file <vault.html> --label <name> [--out results.json] [--quick]
// (run from any dir whose node_modules has playwright)
import { chromium } from 'playwright';
import { pathToFileURL } from 'url';
import { writeFileSync } from 'fs';

const arg = (k, d) => { const i = process.argv.indexOf(k); return i > 0 ? process.argv[i + 1] : d; };
const FILE = arg('--file', `${process.env.HOME}/.cache/atlas/vault.html`);
const LABEL = arg('--label', 'build');
const OUT = arg('--out', `/tmp/frame-bench-${LABEL}.json`);
const QUICK = process.argv.includes('--quick');

const VIEWPORTS = QUICK ? [[1920, 1080], [1280, 800]] : [[2560, 1440], [1920, 1080], [1280, 800]];
const DPRS = QUICK ? [2] : [1, 2];
// TS is driven by clicking the A−/A+ stepper (0.15/click from the 1.25 default)
const TSS = QUICK ? [{ ts: 1.25, clicks: 0 }, { ts: 2.0, clicks: 5 }]
  : [{ ts: 0.8, clicks: -3 }, { ts: 1.25, clicks: 0 }, { ts: 2.0, clicks: 5 }];
const KS = [1.0, 1.58, 2.33, 3.25];

const INIT = () => {
  window.__perf = { drawMs: [], t: [] };
  window.__cnt = null;
  const oRAF = window.requestAnimationFrame.bind(window);
  window.requestAnimationFrame = cb => oRAF(ts => {
    const t0 = performance.now();
    cb(ts);
    window.__perf.drawMs.push(performance.now() - t0);
    window.__perf.t.push(t0);
  });
  const P = CanvasRenderingContext2D.prototype;
  for (const m of ['arc', 'fill', 'stroke', 'fillText', 'strokeText', 'drawImage',
    'measureText', 'createLinearGradient', 'createRadialGradient']) {
    const o = P[m];
    P[m] = function (...a) { if (window.__cnt) window.__cnt[m] = (window.__cnt[m] || 0) + 1; return o.apply(this, a); };
  }
};

const q = (a, p) => { const s = [...a].sort((x, y) => x - y); return s.length ? s[Math.min(s.length - 1, Math.floor(s.length * p))] : 0; };

async function zoomTo(page, target) {
  for (let i = 0; i < 80; i++) {
    const k = await page.evaluate(() => d3.zoomTransform(document.getElementById('canvas')).k);
    if (k > target * 0.97 && k < target * 1.05) return k;
    const dy = k < target ? -Math.min(240, 500 * Math.log(target / k)) : Math.min(120, 500 * Math.log(k / target));
    await page.evaluate(d => {
      const c = document.getElementById('canvas');
      c.dispatchEvent(new WheelEvent('wheel', { deltaY: d, clientX: innerWidth / 2, clientY: innerHeight / 2, bubbles: true, cancelable: true }));
    }, dy);
    await page.waitForTimeout(40);
  }
  return page.evaluate(() => d3.zoomTransform(document.getElementById('canvas')).k);
}

async function measurePan(page) {
  const [cx, cy] = await page.evaluate(() => [innerWidth / 2, innerHeight / 2]);
  const blocker = await page.evaluate(([x, y]) => { const el = document.elementFromPoint(x, y); return el && el.id !== 'canvas' ? (el.id || el.className) : null; }, [cx, cy]);
  if (blocker) throw new Error('pan point blocked by ' + blocker);
  await page.evaluate(() => { window.__perf = { drawMs: [], t: [] }; window.__cnt = {}; });
  await page.mouse.move(cx, cy);
  await page.mouse.down();
  for (let i = 0; i < 48; i++) {
    await page.mouse.move(cx + Math.sin(i / 6) * 130, cy + Math.cos(i / 9) * 70, { steps: 1 });
    await page.waitForTimeout(15);
  }
  await page.mouse.up();
  return page.evaluate(() => {
    const P = window.__perf;
    const heavy = P.drawMs.filter(v => v > 0.2);          // draw frames, not stray micro-callbacks
    const dts = P.t.slice(1).map((v, i) => v - P.t[i]).filter(v => v > 0.1 && v < 500);
    const cnt = {}; for (const [k, v] of Object.entries(window.__cnt || {})) cnt[k] = +(v / Math.max(1, heavy.length)).toFixed(1);
    window.__cnt = null;
    return { frames: heavy.length, js: heavy, dt: dts, cnt };
  });
}

const browser = await chromium.launch({
  args: ['--disable-frame-rate-limit', '--disable-gpu-vsync',
    '--enable-gpu-rasterization', '--ignore-gpu-blocklist', '--use-angle=gl-egl'],
});
const probe = await (async () => {
  const p = await browser.newPage();
  const r = await p.evaluate(() => {
    try {
      const gl = document.createElement('canvas').getContext('webgl');
      const d = gl.getExtension('WEBGL_debug_renderer_info');
      return gl.getParameter(d.UNMASKED_RENDERER_WEBGL);
    } catch (e) { return 'no-webgl: ' + e; }
  });
  await p.close(); return r;
})();
console.log(`# frame-bench · ${LABEL} · ${FILE}\n# GL renderer: ${probe}`);

const rows = [];
for (const [vw, vh] of VIEWPORTS) for (const dpr of DPRS) for (const T of TSS) {
  const ctx = await browser.newContext({ viewport: { width: vw, height: vh }, deviceScaleFactor: dpr });
  const page = await ctx.newPage();
  await page.addInitScript(INIT);
  await page.goto(pathToFileURL(FILE).href, { waitUntil: 'load' });
  await page.waitForTimeout(3200);
  const btn = T.clicks >= 0 ? '#tszPlus' : '#tszMinus';
  for (let i = 0; i < Math.abs(T.clicks); i++) { await page.click(btn, { force: true }); await page.waitForTimeout(40); }
  for (const K of KS) {
    const kReal = await zoomTo(page, K);
    await page.waitForTimeout(250);
    try {
      const m = await measurePan(page);
      const row = {
        label: LABEL, vw, vh, dpr, ts: T.ts, k: +kReal.toFixed(2),
        frames: m.frames,
        jsMed: +q(m.js, 0.5).toFixed(2), jsP95: +q(m.js, 0.95).toFixed(2),
        dtMed: +q(m.dt, 0.5).toFixed(2), dtP95: +q(m.dt, 0.95).toFixed(2),
        cnt: m.cnt,
      };
      rows.push(row);
      console.log(`${vw}x${vh} dpr${dpr} ts${T.ts} k${row.k}  js ${row.jsMed}/${row.jsP95}ms  dt ${row.dtMed}/${row.dtP95}ms  arc:${m.cnt.arc || 0} fill:${m.cnt.fill || 0} stroke:${m.cnt.stroke || 0} fillText:${m.cnt.fillText || 0} strokeText:${m.cnt.strokeText || 0} measure:${m.cnt.measureText || 0}`);
    } catch (e) {
      console.log(`${vw}x${vh} dpr${dpr} ts${T.ts} k~${K}  SKIP: ${e.message}`);
    }
  }
  await ctx.close();
}
writeFileSync(OUT, JSON.stringify({ label: LABEL, file: FILE, gl: probe, rows }, null, 1));
console.log('# saved', OUT);
await browser.close();
