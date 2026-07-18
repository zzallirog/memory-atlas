# tier-infer — validation run (2026-07-18)

Honest proxy validation of the #4 engine, run because the live ~2300-term vault it targets was
not in hand. The point of a proxy is to avoid a tautology: a synthetic glossary we author
would have its hierarchy baked in, so classifying it would prove nothing. Instead we used a
**real, externally-authored, flat** glossary — its A/B/C structure did not exist until the
engine inferred it.

## Corpus
- **334 terms** — *Introduction to Psychology* glossary, Open Education Alberta (Pressbooks),
  **CC BY**. One `.md` per term (`name:` + definition body). Flat: no `tier`, no `part_of`.
- Not redistributed here (third-party content); `parse_pb.py` rebuilds it from the public page.

## Inference (Workflow: spine → classify → verify)
- 10 agents, 0 errors, ~543k tokens, ~11.5 min wall.
- **spine**: 12 tier-A subjects + 49 tier-B themes.
- **classify**: 334/334 terms assigned across 8/8 batches.
- **verify** fixed 6 defects: added 2 terms missing from batch output, dropped 2 duplicate
  assignments, confirmed all 334 `part_of` resolve, spine shape in range (12 A, 49 B unique).

## Apply (collision-safe)
- spine: 53 notes created, **8 merged** into existing same-named tier-B leaves (no duplicate).
- leaves: 326 set, 8 merged-with-spine, **0 misses**. Total notes: 387.

## Measurement (the proof — regen, not self-report)
`memory-atlas --src vault --dump-data - --no-semantic-cross`:

| metric | value |
|---|---|
| nodes | 387 |
| `part_of` edges | **375** (only edge kind present) |
| node tiers | 12 A · 51 B · 324 C |
| A roots | Biopsychology, Cognition, Consciousness, Developmental, Learning, Memory, Motivation & Emotion, Personality, Psychological Disorders, Research Methods, Sensation & Perception, Social Psychology |
| **orphans** (non-root without a `part_of` edge up) | **0** |

Every one of the 375 non-root nodes resolves its `part_of` to a real parent. Zero ghosts,
zero orphans → the frontmatter contract holds end-to-end and the `taxonomy` preset renders a
clean radial A→B→C tree.

## Caveat / next
- Proxy scale (334) is ~1/7 of the 2300-term target. Algorithm is scale-invariant; cost ~linear.
- A real run needs that vault. Same pipeline; `apply_tiers.py` backs up before writing.

---

## When NOT to run this engine (2026-07-18, after meeting the real vault)

The target vault turned up on hand after all (2374 notes). **The engine was not used on it, and
should not have been.** Recording why, because the default reflex is to run the tool you built.

The engine infers a spine because a *flat* corpus has none. That corpus was not flat:

| layer | count | what it already was |
|---|---|---|
| `wiki/загальна/терміни/` | 2125 | a third-party dictionary (Шапарь), one flat glossary |
| `wiki/загальна/concepts/` | 120 | **the owner's own theme-level notes** — an authored B layer |
| `roadmap.md` | — | **the owner's own A layer**: course modules M1–M13, checked against Колобич |

So both tiers the engine exists to invent were already authored by the vault's owner, one of
them (M1–M13) as prose in a roadmap file rather than as frontmatter. Inferring a spine here
would have replaced that taxonomy with a plausible synonym of it, at ~30 Opus agents.

What was done instead: an authored mapping, zero inference, 16 tier-A subjects (M1–M13 + the
three the dictionary demanded: Особистість, Психологія діяльності, Спілкування), 103 concepts
as tier B, and the 2125 dictionary terms folded to tier C under their own hub note — the shape
the owner specified («Словник = 1 хаб-нод + 2300 нод, скрыты фильтром»). Measured by regen:
**2228 notes with `part_of`, 2228 resolve, 0 orphans**, and no parent note was materialized
because all 16 already existed as the owner's hub notes.

**Rule of thumb:** before running the inference, grep the vault for an authored structure —
a roadmap, a syllabus, a hub note, an existing topic layer. Infer only what nobody has written
down. A vault with an owner usually has one; a scraped or imported glossary usually does not.

**Measurement trap found the same day** (cost two wrong claims before it was caught): counting
`kind=part_of` edges does **not** measure resolution. The generator collapses a `part_of` edge
into an existing `wiki` edge between the same pair, so a fully-resolving vault can report 24
edges out of 2228. Measure *whether the pair is connected in the graph*, not the edge kind.
