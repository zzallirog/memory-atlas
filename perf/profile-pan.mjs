// CPU-profile the draw loop during a scripted pan; print top self-time functions.
import { chromium } from 'playwright';
import { pathToFileURL } from 'url';
const FILE = process.argv[2];
const K = +(process.argv[3] || 2.3);
const browser = await chromium.launch({ args: ['--disable-frame-rate-limit', '--disable-gpu-vsync', '--enable-gpu-rasterization', '--ignore-gpu-blocklist', '--use-angle=gl-egl'] });
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 2 });
await page.goto(pathToFileURL(FILE).href, { waitUntil: 'load' });
await page.waitForTimeout(3200);
for (let i = 0; i < 80; i++) {
  const k = await page.evaluate(() => d3.zoomTransform(document.getElementById('canvas')).k);
  if (k > K * 0.97 && k < K * 1.05) break;
  const dy = k < K ? -Math.min(240, 500 * Math.log(K / k)) : Math.min(120, 500 * Math.log(k / K));
  await page.evaluate(d => {
    const c = document.getElementById('canvas');
    c.dispatchEvent(new WheelEvent('wheel', { deltaY: d, clientX: innerWidth / 2, clientY: innerHeight / 2, bubbles: true, cancelable: true }));
  }, dy);
  await page.waitForTimeout(40);
}
const cdp = await page.context().newCDPSession(page);
await cdp.send('Profiler.enable');
await cdp.send('Profiler.setSamplingInterval', { interval: 100 });
await cdp.send('Profiler.start');
const [cx, cy] = [960, 540];
await page.mouse.move(cx, cy); await page.mouse.down();
for (let i = 0; i < 120; i++) {
  await page.mouse.move(cx + Math.sin(i / 6) * 130, cy + Math.cos(i / 9) * 70, { steps: 1 });
  await page.waitForTimeout(12);
}
await page.mouse.up();
const { profile } = await cdp.send('Profiler.stop');
const self = new Map();
const byId = new Map(profile.nodes.map(n => [n.id, n]));
for (const n of profile.nodes) {
  const name = (n.callFrame.functionName || '(anon)') + ' @' + n.callFrame.lineNumber;
  self.set(name, (self.get(name) || 0) + (n.hitCount || 0));
}
const total = [...self.values()].reduce((a, b) => a + b, 0);
const top = [...self.entries()].sort((a, b) => b[1] - a[1]).slice(0, 24);
console.log(`total samples ${total} (interval 100us) at k≈${K}`);
for (const [name, hits] of top) console.log(`${(hits / total * 100).toFixed(1).padStart(5)}%  ${(hits / 10).toFixed(1).padStart(7)}ms  ${name}`);
await browser.close();
