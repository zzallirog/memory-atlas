// shoot-gallery: rebuild every gallery frame from the example vaults, one taste.
//
// Why a script and not a hand pass: the frames carry the version stamp and the
// whole HUD, so they go stale on their own every release — the 07-09 set still
// showed v2.4.1 and a pre-2.14 panel. This makes a re-shoot one command.
//
//   npm i playwright        (or run from a dir that has it)
//   node tools/shoot-gallery.mjs [case…]     # no args = all
//
// Uses the system Chrome (channel: 'chrome') rather than a downloaded build:
// no 150MB fetch, and it is the browser the pages are actually read in.
//
// The taste, in one place so every frame shares it:
//   1400x900 logical, deviceScaleFactor 2 (retina — the old set was soft),
//   English UI, default HUD state (what a first-time reader really sees),
//   graph settled, then 'f' to fit the context into frame.

import { chromium } from 'playwright';
import { execFileSync } from 'child_process';
import { pathToFileURL } from 'url';
import { mkdirSync, existsSync } from 'fs';
import { dirname, resolve, join } from 'path';
import { fileURLToPath } from 'url';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const OUT = join(ROOT, 'docs/shots/gallery');
const TMP = '/tmp/atlas-gallery-build';

// Deterministic + offline: the bridges in these frames are wikilinks, shared
// ghosts and tag overlap only — same three flags GALLERY.md tells the reader.
// --anon keeps the author out of the published frames: the footer stamps the
// source path and the hostname, and these images are read by strangers.
const BUILD_FLAGS = ['--lang', 'en', '--anon', '--no-semantic-cross',
                     '--no-temporal-cross', '--no-session-cross', '--no-open'];

const CASES = [
  // the two frames README leads with — the demo vault, so a reader can reproduce
  // them with `./memory-atlas --demo` and nothing else
  { name: 'overview',           vault: 'demo', dir: 'docs/shots', q: '?layout=ring&color=zone' },
  { name: 'node-focus',         vault: 'demo', dir: 'docs/shots', q: '?node=fermentation' },

  { name: 'campaign-petals',    vault: 'campaign', q: '?layout=petals&color=zone' },
  { name: 'campaign-ghosts',    vault: 'campaign', q: '?layout=radial&color=zone' },
  { name: 'campaign-browse',    vault: 'campaign', q: '?tab=browse&node=ashfall_harbor', chrome: 'tab' },
  { name: 'homelab-ring',       vault: 'homelab',  q: '?layout=ring&color=zone' },
  { name: 'homelab-dash',       vault: 'homelab',  q: '?tab=dash', chrome: 'tab' },
  { name: 'reading-timeline',   vault: 'reading',  q: '?layout=timeline&color=heat' },
  { name: 'italian-taglens',    vault: 'italian',  q: '?state=eyJ2IjogMSwgImxheW91dCI6ICJmb3JjZSIsICJjb2xvciI6ICJ6b25lIiwgInRhZ3MiOiBbInZlcmJzIl19' },
  { name: 'trip-grid',          vault: 'trip',     q: '?layout=grid&color=zone' },
  { name: 'casefile-theories',  vault: 'casefile', q: '?state=eyJ2IjogMSwgImxheW91dCI6ICJwZXRhbHMiLCAiY29sb3IiOiAiY2x1c3RlciJ9' },
  { name: 'product-types',      vault: 'product',  q: '?state=eyJ2IjogMSwgImxheW91dCI6ICJmb3JjZSIsICJjb2xvciI6ICJ0eXBlIn0=' },
  { name: 'family-hub',         vault: 'family',   q: '?layout=radial&color=zone' },

  // 2.21 — the fill shape follows the layout, and one form is new
  { name: 'homelab-strata',     vault: 'homelab',  q: '?layout=strata&color=zone' },
  { name: 'campaign-dendro',    vault: 'campaign', q: '?layout=dendro&color=zone' },
];

const want = process.argv.slice(2);
const todo = want.length ? CASES.filter(c => want.includes(c.name) || want.includes(c.vault)) : CASES;
if (!todo.length) { console.error('no case matched:', want.join(' ')); process.exit(1); }

mkdirSync(TMP, { recursive: true });
mkdirSync(OUT, { recursive: true });

// one build per vault, reused by every case that reads it
const built = new Map();
const buildVault = (vault) => {
  if (built.has(vault)) return built.get(vault);
  const out = join(TMP, `${vault}.html`);
  process.stdout.write(`build ${vault} … `);
  if (vault === 'demo') {
    execFileSync(join(ROOT, 'memory-atlas'), ['--demo', '--out', out, ...BUILD_FLAGS],
      { cwd: ROOT, stdio: ['ignore', 'ignore', 'inherit'] });
    console.log('ok');
    built.set(vault, out);
    return out;
  }
  // cwd = repo root and a RELATIVE --src on purpose: the footer stamps the source
  // path verbatim, and an absolute one would ship the author's home directory
  // into every published frame.
  execFileSync(join(ROOT, 'memory-atlas'),
    ['--src', join('docs/gallery-vaults', vault), '--out', out, ...BUILD_FLAGS],
    { cwd: ROOT, stdio: ['ignore', 'ignore', 'inherit'] });
  console.log('ok');
  built.set(vault, out);
  return out;
};

const shot = [];
const browser = await chromium.launch({ channel: 'chrome' });
const ctx = await browser.newContext({
  viewport: { width: 1400, height: 900 },
  deviceScaleFactor: 2,
  reducedMotion: 'reduce',   // no half-played transition caught mid-frame
});

// Playwright launches Chrome with --no-startup-window, so the browser exits when
// its last page closes — closing each frame's page killed the run after the first
// one. This page is never closed until the end and holds the browser open.
const keepAlive = await ctx.newPage();

for (const c of todo) {
  const file = buildVault(c.vault);
  const page = await ctx.newPage();
  await page.goto(pathToFileURL(file).href + c.q, { waitUntil: 'load' });
  // the generator pre-ticks the sim before the first frame, so this is settle
  // time for layout morph + label de-conflict, not for the force layout itself
  // park the pointer away from the left edge first: hover-peek reopens the bar
  // when the cursor is near x=0, and a fresh page starts the pointer at (0,0)
  await page.mouse.move(1100, 300);
  await page.waitForTimeout(c.chrome === 'tab' ? 1800 : 3200);
  // Every graph frame is shot with edges drawn (key 9) and at full edge alpha.
  // The page ships with them off on purpose — lines are noise until you ask for
  // them — but these frames exist to show structure, and half the captions in
  // GALLERY.md describe something you can only see along an edge ("everything
  // routes through the matriarch" is a fan of spokes or it is nothing).
  const keys = c.chrome === 'tab' ? [] : ['9', ...(c.keys || [])];
  const sliders = c.chrome === 'tab' ? {} : { edgeAlpha: 1, ...(c.sliders || {}) };
  for (const k of keys) { await page.keyboard.press(k); await page.waitForTimeout(500); }
  for (const [id, v] of Object.entries(sliders)) {
    await page.evaluate(([id, v]) => {
      const el = document.getElementById(id);
      el.value = v; el.dispatchEvent(new Event('input', { bubbles: true }));
    }, [id, v]);
    await page.waitForTimeout(400);
  }
  if (c.chrome !== 'tab') {
    await page.keyboard.press('f');          // fit the context into frame
    // long enough for the eased fit AND for the toast the fit raises to fade —
    // a caught toast ("fit: 4 context nodes…") reads as a screenshot accident
    await page.waitForTimeout(3600);
  }
  await page.mouse.move(1399, 899);          // park the pointer: no stray hover card
  await page.waitForTimeout(250);
  const outDir = c.dir ? join(ROOT, c.dir) : OUT;
  mkdirSync(outDir, { recursive: true });
  const path = join(outDir, `${c.name}.png`);
  await page.screenshot({ path });
  shot.push(path);
  console.log(`shot ${c.name}`);
  await page.close();
}

await browser.close();

// Rendered at 2x, published at 1x: supersampling buys the antialiasing, the
// downscale keeps a page with eleven frames in it from costing 11MB. This runs
// AFTER the browser is gone on purpose — a synchronous child process inside the
// shooting loop blocks node's event loop, and Playwright talks to Chrome over a
// pipe: the first sips call killed the connection and every later page threw
// "Target page, context or browser has been closed".
for (const path of shot) execFileSync('sips', ['-Z', '1400', path, '--out', path], { stdio: 'ignore' });

console.log(`\n${shot.length} frame(s) → docs/shots/gallery/`);
