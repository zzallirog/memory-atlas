# memory-atlas — session handoff (2026-07-09)

Continuity doc for a fresh session. Everything built this session is on `main`;
debts (unbuilt work) are listed below with enough context to resume cold.

## TL;DR — state

- Repo: `~/src/memory-atlas` (git), branch **`main` @ `7589d17`**, VERSION **2.2.0**, tree clean.
- Generator: `memory-atlas` (Python stdlib, ~1030 lines, **32 self-tests green**). Template: `memory-atlas.template.html` (~3400 lines, D3-canvas, self-contained output).
- Prod-ready. Runs on Mac (native dev) and Arch (read-only mirror). Two feature docs in repo: `AUDIT.md` (full logic-flow audit + perf zones + pitfalls S1–S14), `INSTALLER-HANDOFF.md` (packaging for external user Daniel).
- Verify loop proven: `./memory-atlas --self-test` + headless Chrome `--dump-dom | grep data-ready` + screenshot eyeball.

## What shipped this session (commit trail on `main`)

Base entering session: `b0016e6` (Mac perf v2.1 + Arch audit/build pass: dash-tab, settings-sheet, profile export/import, `?state=` node-anchored, bug-sweep B1/B4-B18/B23/B24). Then:

- `319eb1f` **W3 adaptive readability** (Opus) — edgeAlpha slider default 1.0→0.5; `nodeF` fades unimportant nodes by on-screen density ("balls dissolve in clutter within view radius"); focus/pin/search/top-N hubs stay bright. Tunables: `EDGE_FADE_FLOOR` / `NODE_FADE_KNEE` / `NODE_FADE_FLOOR` in paintFrame.
- `684e842`..`8e21a12` **Fable ×5** — audit-sweep B2/B3/B8/B19/B21; hover-preview cards + CSS float-in (`@keyframes floatIn/panelIn/sheetIn`); **tag-lens ×20** ("blur + emptiness" — selecting a tag reuses the cached ego-blur engine: matched nodes sharp, rest dissolve, tap-on-emptiness selects nothing by design; hotkey `t`, ∪/∩ mode, tagSel carried in views + `?state=`); bar-blocks (HUD sections ВИД/ФОКУС/ПОДПИСИ/ПЛОТНОСТЬ/СЛОИ/МОУШН, segment groups); VERSION 2.2.0. Tunables: `LENS_BG_ALPHA=0.82`, `TAGC[]` palette.
- `2c4b0de` **installer handoff** (Opus) — see INSTALLER-HANDOFF.md.
- `9840dd0` **W2 generator portability** (Opus) — G7 (EXCLUDE_DIRS += .obsidian/.trash/node_modules/.stversions), G2 (frontmatter keys match top-level too `^\s*` + YAML-list tags + `metadata.state` emitted), G1 (DEFAULT_SRC resolves first NON-empty candidate), G10 (browse real mtime). +4 self-tests. **Clears installer P0 blockers for Obsidian vaults.**
- `7589d17` **fix** (Opus) — removed edge hover-highlight (Fable added it accidentally in hover pass; flickered on dense graph, read as "all links highlighting"). Node hover-preview intact.

## Infra: Arch mirror + aliases

- **Mac = sole native author.** Commit to `main`; Arch mirrors automatically.
- Arch mirror: `~/.local/bin/atlas-sync.sh` + systemd user timer `atlas-sync.timer` (`OnCalendar=*:0/20`). When home (Mac `192.168.88.127:22` reachable — TCP check, NOT ping: macOS stealth drops ICMP), it `git fetch mac` (remote `mac` = `zzalli@192.168.88.127:/Users/zzalli/src/memory-atlas`), hard-aligns to `mac/main`, regens `~/.mac-claw/atlas/memory-atlas-arch.html` with explicit `--src ~/.claude/projects/-home-zzalli/memory` (autodetect would grab empty `-Users-zzalli` on Arch).
- Aliases (fish functions, both hosts): Mac `atlas` (rebuild+open), `atlaso` (open only); Arch `atlas` (open mirror), `atlas-sync` (pull now + open).

## Verify loop (every coherent change)

```
cd ~/src/memory-atlas
./memory-atlas --self-test                        # must stay 32 green
./memory-atlas --out /tmp/t.html --no-open        # regen to SCRATCH, never ~/.mac-claw canonical (live mirror)
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless --disable-gpu --no-sandbox \
  --virtual-time-budget=6000 --dump-dom "file:///tmp/t.html" | grep -o 'data-ready="[01]"'   # want 1
# + --screenshot=/tmp/t.png --window-size=1600,1000, then LOOK at it (design regressions)
```
Gotcha: **`grep -a`** on the template — it binary-detects (inlined d3/font) and plain grep silently returns nothing. Deep-link `?layout=petals`, `?state=`, `?node=` for screenshotting interactive states.

---

## DEBTS (the backlog — resume here)

### A. Frontend tweaks (user-decided, not yet applied — was going to be "4 tweaks")
1. **Return ⚙ one-click rebuild to the bar.** Fable removed it (entry now via settings-sheet ⛭ + dash). User wants the quick bar button back — but resolve the near-identical ⚙/⛭ pair differently (distinct glyph/label, watch S12 tofu), don't drop the function.
2. **Pins through tag-lens = render as ego-background** (dim blur-bg style, like the ego underlay — not full bright, not hidden). Lens code = generalized `drawFocus`.
3. **Persist `tagAnd` (∪/∩ tag mode) in cfg** (KEYP), routed through a `setMode`-style helper (S11: programmatic setters must fire dependent re-renders). User will test both modes.
4. **Ghosts fade in lens = keep** (can't tag them). No change. Future: user wants a *separate vault with labels for ghosts* ("where is this / what is this") — ghost fate to be revisited.

### B. Generator gaps (deferred from W2, documented)
- **G3** emb-cache growth: cache is content-addressed (`sha256(model+text)`) so NO wrong-hit bug — only unbounded disk growth over time. Correct fix = per-src namespace OR LRU-with-timestamps (needs cache-format change + migration of existing ~5.5MB `~/.mac-claw/atlas/emb-cache.json`). NOT a one-liner (arch flagged the naive prune as a cross-corpus regression).
- **G4** `--data` validator: mini-validator (nodes[].id/zone/label present, edges ref existing ids) with clear exit — for the `--data` external-builder path + installer advanced use.
- **G5** version handshake: `TPL_V` `<meta>` in template + generator warns on template/generator skew (stale symlink = silent mismatch across hosts).

### C. Bug/doc debts (user has no strong opinion → builder's call)
- **B20** stem-collision signal: `a-b.md` + `a_b.md` → second is `a_b~2`, wikilinks resolve to first only. Warn exists (stderr); surface as a "collisions" signal in dash + emit to DATA (client is blind). Live example: `rail` (glados/RAIL vs bastra/RAIL).
- **B22** >8 zones fall to OTHER-grey + empty-zone hotkeys: fine for memory corpus (6 zones), document the "≤8 colored zones" contract for `--data`.
- **editorPref**: currently global across corpora — decide global vs per-corpus. (Leaning keep global.)

### D. Design threads (think, don't slam)
- **Robust zone-overlays across layouts** (user-raised, important). Hulls are suppressed in `semantic` layout (`showHulls = hulls && layoutName !== 'semantic'`, template ~1075) because nodes are positioned by *meaning* there → zones spatially mixed → a hull would smear over scattered points. User wants zone-domain overlays to render/overlay everywhere, but done right: **the map-building (layout) must be rethought so zone overlays lay out coherently** even under semantic. Naively removing the guard reproduces the mess. Real design work.
- **View-engine → share → view-bank** (from earlier). Views should inherit a single apply-machine; the share button emits a seed / `?state=` from that engine; foundation for a bank of views / seeds / matrix-templates. (Fable already made views + `?state=` carry filters+tagSel+camera node-anchored — build on that.)
- **Tag system further ×20**: Fable delivered the lens; more possible (tag-driven saved views exist via 💾-in-pill; quick-tag, tag legend, tag as first-class filter alongside zones).
- **Adaptive-render tuning**: `EDGE_FADE_FLOOR`/`NODE_FADE_KNEE`/`NODE_FADE_FLOOR`/`LENS_BG_ALPHA` are eyeball knobs — user tunes live.

### E. Docs / hygiene
- git-notes on the session's commits (annotate rationale).
- Version the `AUDIT.md` §9 x20-ideas (STATE-layer #1, fire-log heat #2, diff-mode #3, session-lineage #4) as tracked proposals.
- `README.md` v2.2 changelog (tag-lens, hover-preview, bar-blocks, W2 portability, arch mirror).
- **push `main` → bare** `arch:~/backups/memory-atlas.git` (backup channel; bare is stale — mirror pulls direct from Mac, but bare should track for durability per backup topology).

### F. Memory graft (requested, not done)
Arch session created/updated 2 memory notes; grab into Mac memory (`~/.claude/projects/-Users-zzalli/memory/`). **Mac = sole memory author** → GRAFT, don't overwrite:
- `proj_memory_atlas_graph.md`: Mac copy has richer history (v2.0/v2.1 sections + lessons: "Rust rejected by NUMBER not floor", deploy-surface-mismatch). Arch's copy CONDENSED those away. Author a fresh "prod v2.2 (07-09)" section onto the Mac copy; do not paste arch's condensed version. Scratch copy: `/private/tmp/claude-501/-Users-zzalli/f004aece-cd90-43a7-955c-d1733375bac2/scratchpad/arch-proj_memory_atlas_graph.md`.
- `atrium_modules_index.md` (NEW, arch auto-gen from `~/claw-dashboard/frontend/src/data/atrium-catalog.json`, 73 modules) — Atrium = `~/claw-dashboard/` published dashboard on Arch; useful as a **dash-tile-pattern reference** for the atlas dash-tab. Scratch: `.../scratchpad/arch-atrium_modules_index.md`. Wiki: `~/wiki/web/atrium.md`.

### G. Installer for Daniel (spec in INSTALLER-HANDOFF.md)
W2 already cleared P0 (G7/G2/G1 → Obsidian vaults work). Remaining: package as zipapp `.pyz` (stdlib, one file) or pipx; **synthetic** demo vault (NOT real notes — privacy, cores 05/08) with a hidden `shared_ref` bridge to showcase overlap without Ollama; bundle/curl d3 (`render()` inlines it from `~/.mac-claw/atlas/d3.v7.min.js`); graceful no-Ollama; quickstart README. Ship = outward step → clean demo data mandatory; PyPI/public = full claim-gate + VOICE-outward-en (Daniel = n0mad-ai/bastra).

## Guardrails (don't break)
- Mac perf zones: paintFrame label-declutter (~2560+), drawFocus/blurCanvas ego-blur cache (~2280–2440), tile-LOD (`drawTile`/`TILE_K`). W3 adaptive (edgeAlpha/nodeF) + Fable tag-lens (generalized drawFocus) live here — read AUDIT §0/§7.
- Pitfalls S11 (programmatic setters don't fire listeners → use a setMode helper), S12 (glyph tofu), S13 (design-pass: same-row baseline, sheets close on tab switch, narrow viewport <1240px), S14 (headless dpr=2 halves innerWidth).
- Regen for testing → scratch path, never `~/.mac-claw/atlas/*` (live mirror to Arch).
