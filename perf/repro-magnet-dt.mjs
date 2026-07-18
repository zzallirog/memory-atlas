// repro-magnet-dt.mjs — BUG 2: "эго-магнит под низким фпс двигает ноды, не клеится"
//
// Hypothesis under test: magnetStep() integrates PER FRAME, not per elapsed dt
// (template.html:4208 lerp=0.24 / :4216 lerp=0.09, applied at :4224 with no dt factor;
// settle threshold :4227 is also a per-frame delta). If true, the same scene with the
// same parked cursor converges to DIFFERENT positions at the same wall-clock time
// depending on frame rate — and the pull ("sticking") never lands at low fps.
//
// Method: freeze the force sim (so n.x/n.y are constant and only the magnet offsets
// n._mx/n._my move), park the cursor a fixed distance from a chosen node, then sample
// the offset field at fixed WALL-CLOCK times under CDP CPU throttling rates.
// dt-correct integration => identical positions at equal wall-clock, any rate.
//
// usage: node repro-magnet-dt.mjs <out-dir> <vault.html> [rates...]   (default rates 1 4 6 10)
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
const FILE = process.argv[3];
const RATES = (process.argv.slice(4).length ? process.argv.slice(4) : ['1', '4', '6', '10']).map(Number);
fs.mkdirSync(OUT, { recursive: true });

// wall-clock sample points after the cursor parks (ms). PULL_DELAY is 1300ms,
// so >1300 samples are the "sticking" phase.
const SAMPLES = [300, 700, 1100, 1600, 2200, 3000, 4000, 5500];

const LAUNCH = {
  channel: 'chrome',
  args: ['--enable-gpu-rasterization', '--ignore-gpu-blocklist', '--no-sandbox'],
};

const runs = [];
for (const rate of RATES) {
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
  if (!page) { console.log(`SKIP rate ${rate}: browser would not start`); continue; }

  await page.goto(pathToFileURL(FILE).href, { waitUntil: 'load' });
  await page.waitForTimeout(4000);

  // magnet ON, particles OFF, edges ON (edges make frames expensive so throttling bites)
  await page.evaluate(() => {
    const on = id => document.getElementById(id)?.classList.contains('on');
    if (!on('magnet')) document.getElementById('magnet').click();
    if (on('particles')) document.getElementById('particles').click();
    if (!on('edgesOn')) document.getElementById('edgesOn').click();
  });
  await page.waitForTimeout(2500);

  // freeze the layout: only the magnet offsets may move from here on
  await page.evaluate(() => { sim.alpha(0); sim.stop(); });
  await page.waitForTimeout(500);

  // count magnet integration steps (= frames the magnet actually integrated)
  await page.evaluate(() => {
    window.__frames = 0;
    const orig = window.magnetStep;
    window.magnetStep = function () { window.__frames++; return orig.apply(this, arguments); };
  });

  // pick a target node near the middle of the cloud and park the cursor a fixed
  // WORLD distance from it (inside readR so it becomes the magnet's `best`)
  const target = await page.evaluate(() => {
    const vis = nodes.filter(n => visible(n));
    const cx = vis.reduce((a, n) => a + n.x, 0) / vis.length;
    const cy = vis.reduce((a, n) => a + n.y, 0) / vis.length;
    let best = null, bd = Infinity;
    for (const n of vis) { const d = Math.hypot(n.x - cx, n.y - cy); if (d < bd) { bd = d; best = n; } }
    // cursor 18 world units to the right of the node: inside readR (24/k), real pull distance
    const wx = best.x + 18, wy = best.y;
    return {
      id: best.id, nx: best.x, ny: best.y, wx, wy,
      sx: wx * transform.k + transform.x, sy: wy * transform.k + transform.y,
      k: transform.k, readR: Math.min(40, Math.max(12, 24 / transform.k)),
      magR: Math.min(160, Math.max(36, 90 / transform.k)),
    };
  });

  const cdp = await page.context().newCDPSession(page);
  if (rate > 1) await cdp.send('Emulation.setCPUThrottlingRate', { rate });

  // park the cursor and never move it again
  await page.mouse.move(target.sx, target.sy);
  await page.evaluate(() => { window.__frames = 0; window.__t0 = performance.now(); });

  const samples = [];
  let prev = 0;
  for (const t of SAMPLES) {
    await page.waitForTimeout(t - prev); prev = t;
    const s = await page.evaluate((tid) => {
      const tn = nodes.find(n => n.id === tid);
      let sum = 0, mx = 0, moved = 0;
      for (const n of nodes) {
        const d = Math.hypot(n._mx || 0, n._my || 0);
        sum += d * d; if (d > mx) mx = d;
        if (d > 0.5) moved++;
      }
      const px = (tn.x + (tn._mx || 0)) - cursorW[0], py = (tn.y + (tn._my || 0)) - cursorW[1];
      return {
        elapsed: Math.round(performance.now() - window.__t0),
        frames: window.__frames,
        magNode: magNode ? magNode.id : null,
        magActive,
        // how far the "sticking" node still is from the cursor, in SCREEN px
        stickGapPx: +(Math.hypot(px, py) * transform.k).toFixed(2),
        // whole displacement field, screen px
        rmsOffsetPx: +(Math.sqrt(sum / nodes.length) * transform.k).toFixed(3),
        maxOffsetPx: +(mx * transform.k).toFixed(2),
        movedNodes: moved,
        // full field for cross-rate diffing
        field: nodes.map(n => [+(n._mx || 0).toFixed(4), +(n._my || 0).toFixed(4)]),
      };
    }, target.id);
    samples.push(s);
  }

  const last = samples[samples.length - 1];
  const fps = +(last.frames / (last.elapsed / 1000)).toFixed(1);
  console.log(`\n=== CPU throttle x${rate}  (${fps} magnet-steps/s, ${last.frames} steps in ${last.elapsed}ms) ===`);
  for (const s of samples) {
    console.log(`  t=${String(s.elapsed).padStart(4)}ms  steps=${String(s.frames).padStart(4)}  ` +
      `stickGap=${String(s.stickGapPx).padStart(7)}px  rms=${String(s.rmsOffsetPx).padStart(6)}px  ` +
      `max=${String(s.maxOffsetPx).padStart(6)}px  moved=${s.movedNodes}  magActive=${s.magActive}`);
  }
  // ---- phase 2: MOVING cursor (the actual complaint: "не клеится", the stick breaks) ----
  // Once latched, sweep the cursor at a constant screen speed and watch whether the node
  // keeps up. Per-frame integration => trailing distance ~ speed/fps; when the trail
  // exceeds readR the node stops being `best`, magDwell resets and the latch DROPS.
  const sweeps = [];
  for (const speed of [60, 120, 240, 480]) {   // screen px/s
    // re-park and wait out PULL_DELAY so we start latched
    await page.mouse.move(target.sx, target.sy);
    await page.waitForTimeout(2600 * Math.max(1, rate / 4));
    const latchedBefore = await page.evaluate(t => magNode && magNode.id === t, target.id);

    const DUR = 2000;
    const t0 = Date.now();
    const trail = [];
    let lost = 0, ticks = 0;
    while (Date.now() - t0 < DUR) {
      const el = (Date.now() - t0) / 1000;
      await page.mouse.move(target.sx + speed * el, target.sy);
      const s = await page.evaluate(tid => {
        const tn = nodes.find(n => n.id === tid);
        const dx = (tn.x + (tn._mx || 0)) - cursorW[0], dy = (tn.y + (tn._my || 0)) - cursorW[1];
        return { gap: Math.hypot(dx, dy) * transform.k, held: magNode && magNode.id === tid };
      }, target.id);
      trail.push(+s.gap.toFixed(2)); ticks++; if (!s.held) lost++;
      await page.waitForTimeout(30);
    }
    const mean = +(trail.reduce((a, b) => a + b, 0) / trail.length).toFixed(2);
    const max = +Math.max(...trail).toFixed(2);
    sweeps.push({ speed, latchedBefore, meanTrailPx: mean, maxTrailPx: max,
      lostFrac: +(lost / ticks).toFixed(2) });
    console.log(`  sweep ${String(speed).padStart(3)}px/s: latched=${latchedBefore} ` +
      `meanTrail=${String(mean).padStart(6)}px maxTrail=${String(max).padStart(6)}px ` +
      `latchLost=${Math.round(100 * lost / ticks)}%`);
    // let it relax before the next speed
    await page.mouse.move(target.sx, target.sy);
    await page.waitForTimeout(800);
  }

  runs.push({ rate, fps, target, samples, sweeps });
  await page.close(); await browser.close();
}

// ---- cross-rate divergence at equal wall-clock ----
if (runs.length > 1) {
  const base = runs[0];
  console.log(`\n=== divergence vs baseline x${base.rate} (screen px, equal wall-clock) ===`);
  for (const r of runs.slice(1)) {
    const rows = [];
    for (let i = 0; i < SAMPLES.length; i++) {
      const a = base.samples[i], b = r.samples[i];
      if (!a || !b) continue;
      const k = base.target.k;
      let sum = 0, mx = 0;
      for (let j = 0; j < a.field.length; j++) {
        const d = Math.hypot(a.field[j][0] - b.field[j][0], a.field[j][1] - b.field[j][1]) * k;
        sum += d * d; if (d > mx) mx = d;
      }
      rows.push({ t: SAMPLES[i], rms: +Math.sqrt(sum / a.field.length).toFixed(3), max: +mx.toFixed(2),
        stickA: a.stickGapPx, stickB: b.stickGapPx });
    }
    console.log(` x${r.rate} (${r.fps}/s vs ${base.fps}/s):`);
    for (const q of rows)
      console.log(`   t=${String(q.t).padStart(4)}ms  fieldRMSΔ=${String(q.rms).padStart(6)}px  ` +
        `fieldMaxΔ=${String(q.max).padStart(6)}px   stickGap ${q.stickA}px -> ${q.stickB}px`);
  }
}
fs.writeFileSync(`${OUT}/magnet-report.json`,
  JSON.stringify(runs.map(r => ({ ...r, samples: r.samples.map(({ field, ...s }) => s) })), null, 2));
console.log('\nreport:', `${OUT}/magnet-report.json`);
