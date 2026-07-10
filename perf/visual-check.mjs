// visual-check: bar at two window widths, langBtn 10s dissolve, card-zoom frame A/B crop
import { chromium } from 'playwright';
import { pathToFileURL } from 'url';
const NEW = process.argv[2], OLD = process.argv[3];
const browser = await chromium.launch();

for (const [name, w, h] of [['wide', 2560, 1440], ['narrow', 1180, 760]]) {
  const page = await browser.newPage({ viewport: { width: w, height: h } });
  await page.goto(pathToFileURL(NEW).href, { waitUntil: 'load' });
  await page.waitForTimeout(2500);
  await page.screenshot({ path: `/tmp/vc-bar-${name}.png`, clip: { x: 0, y: h - 70, width: w, height: 70 } });
  if (name === 'wide') {
    // langBtn dissolve: wait past 10s idle, shoot the right side of the bar
    await page.waitForTimeout(9000);
    await page.screenshot({ path: '/tmp/vc-bar-dissolved.png', clip: { x: w - 620, y: h - 70, width: 620, height: 70 } });
  }
  await page.close();
}
// card-zoom look, same camera in old and new (visual regression eyeball)
for (const [tag, file] of [['new', NEW], ['old', OLD]]) {
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  await page.goto(pathToFileURL(file).href, { waitUntil: 'load' });
  await page.waitForTimeout(3200);
  for (let i = 0; i < 60; i++) {
    const k = await page.evaluate(() => d3.zoomTransform(document.getElementById('canvas')).k);
    if (k > 2.25 && k < 2.45) break;
    const dy = k < 2.33 ? -Math.min(240, 500 * Math.log(2.33 / k)) : Math.min(120, 500 * Math.log(k / 2.33));
    await page.evaluate(d => { document.getElementById('canvas').dispatchEvent(new WheelEvent('wheel', { deltaY: d, clientX: innerWidth / 2, clientY: innerHeight / 2, bubbles: true, cancelable: true })); }, dy);
    await page.waitForTimeout(40);
  }
  await page.waitForTimeout(600);
  await page.screenshot({ path: `/tmp/vc-cards-${tag}.png` });
  await page.close();
}
console.log('shots: /tmp/vc-bar-wide.png /tmp/vc-bar-narrow.png /tmp/vc-bar-dissolved.png /tmp/vc-cards-new.png /tmp/vc-cards-old.png');
await browser.close();
