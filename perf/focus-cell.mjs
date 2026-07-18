// focus-cell: one (viewport,dpr,K) cell, N repeated pan windows, per-repeat medians.
import { chromium } from 'playwright';
import { pathToFileURL } from 'url';
const FILE = process.argv[2];
const K = +(process.argv[3] || 1.0);
const REP = +(process.argv[4] || 5);
const browser = await chromium.launch({ args: ['--disable-frame-rate-limit', '--disable-gpu-vsync', '--enable-gpu-rasterization', '--ignore-gpu-blocklist', '--use-angle=gl-egl'] });
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 2 });
await page.addInitScript(() => {
  window.__perf = { drawMs: [], t: [] };
  const oRAF = window.requestAnimationFrame.bind(window);
  window.requestAnimationFrame = cb => oRAF(ts => {
    const t0 = performance.now(); cb(ts);
    window.__perf.drawMs.push(performance.now() - t0); window.__perf.t.push(t0);
  });
});
await page.goto(pathToFileURL(FILE).href, { waitUntil: 'load' });
await page.waitForTimeout(3200);
for (let i = 0; i < 80; i++) {
  const k = await page.evaluate(() => d3.zoomTransform(document.getElementById('canvas')).k);
  if (k > K * 0.97 && k < K * 1.05) break;
  const dy = k < K ? -Math.min(240, 500 * Math.log(K / k)) : Math.min(120, 500 * Math.log(k / K));
  await page.evaluate(d => { document.getElementById('canvas').dispatchEvent(new WheelEvent('wheel', { deltaY: d, clientX: innerWidth / 2, clientY: innerHeight / 2, bubbles: true, cancelable: true })); }, dy);
  await page.waitForTimeout(40);
}
const q = (a, p) => { const s = [...a].sort((x, y) => x - y); return s.length ? s[Math.min(s.length - 1, Math.floor(s.length * p))] : 0; };
const meds = [];
for (let rep = 0; rep < REP; rep++) {
  await page.evaluate(() => { window.__perf = { drawMs: [], t: [] }; });
  await page.mouse.move(960, 540); await page.mouse.down();
  for (let i = 0; i < 48; i++) { await page.mouse.move(960 + Math.sin(i / 6) * 130, 540 + Math.cos(i / 9) * 70, { steps: 1 }); await page.waitForTimeout(15); }
  await page.mouse.up();
  const m = await page.evaluate(() => {
    const P = window.__perf;
    return { js: P.drawMs.filter(v => v > 0.2), dt: P.t.slice(1).map((v, i) => v - P.t[i]).filter(v => v > 0.1 && v < 500) };
  });
  meds.push({ js: +q(m.js, 0.5).toFixed(2), dt: +q(m.dt, 0.5).toFixed(2), n: m.js.length });
  await page.waitForTimeout(300);
}
console.log(FILE.split('/').pop(), 'k' + K, JSON.stringify(meds));
console.log('median-of-medians js', q(meds.map(x => x.js), 0.5), 'dt', q(meds.map(x => x.dt), 0.5));
await browser.close();
