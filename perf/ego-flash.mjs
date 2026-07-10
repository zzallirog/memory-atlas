// ego-flash repro: select a hub (ego blur on), drag, burst-screenshot, report bright patches
import { chromium } from 'playwright';
import { pathToFileURL } from 'url';
import { execSync } from 'child_process';
const FILE = process.argv[2];
const browser = await chromium.launch({ args: ['--enable-gpu-rasterization', '--ignore-gpu-blocklist', '--use-angle=gl-egl'] });
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
await page.goto(pathToFileURL(FILE).href, { waitUntil: 'load' });
await page.waitForTimeout(3200);
// select a node via search (deterministic): type a known hub name, pick first result
await page.click('#search');
await page.type('#search', 'muscle', { delay: 20 });
await page.waitForTimeout(600);
await page.keyboard.press('Enter');
await page.waitForTimeout(1200);
const sel = await page.evaluate(() => document.querySelector('#panel h2')?.textContent || 'none');
console.log('selected:', sel);
// drag pan while ego blur is active, shoot every ~90ms
await page.mouse.move(700, 500); await page.mouse.down();
for (let i = 0; i < 22; i++) {
  await page.mouse.move(700 + Math.sin(i / 3) * 160, 500 + Math.cos(i / 4) * 90, { steps: 2 });
  await page.waitForTimeout(45);
  await page.screenshot({ path: `/tmp/ef-${String(i).padStart(2, '0')}.png` });
}
await page.mouse.up();
await browser.close();
// bright-patch scan: mean luma + max 32x32 block luma per frame (via python/PIL if present)
try {
  const out = execSync(`python3 - <<'PY'
from PIL import Image
import glob
rows=[]
for f in sorted(glob.glob('/tmp/ef-*.png')):
    im=Image.open(f).convert('L').resize((240,135))
    px=list(im.getdata())
    mean=sum(px)/len(px)
    # max 8x8 block on the 240x135 grid
    mx=0
    for by in range(0,128,8):
        for bx in range(0,232,8):
            s=0
            for y in range(8):
                s+=sum(px[(by+y)*240+bx:(by+y)*240+bx+8])
            mx=max(mx,s/64)
    rows.append((f.split('/')[-1],round(mean,1),round(mx)))
for r in rows: print(r)
PY`).toString();
  console.log(out);
} catch (e) { console.log('scan failed:', e.message.slice(0, 200)); }
