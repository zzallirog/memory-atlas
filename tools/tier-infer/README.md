# tier-infer — LLM taxonomy inference for flat vaults (EDITOR-ROADMAP #4)

The generator renders a two-level taxonomy map (#8) from `tier:` + `part_of:`
frontmatter. A **flat** glossary (e.g. a ~2300-term psychology vault) carries
neither — every term sits at one level with no membership. This companion *infers*
them: flat term list → tier A/B/C + `part_of` parents, written back to frontmatter so
the `taxonomy` preset lays out a clean radial tree instead of a hairball.

It is LLM-heavy, so it lives **outside** the no-LLM stdlib core of `memory-atlas` — a
Claude Code Workflow you trigger, not part of the deterministic generator.

## Tier model (the target user's blueprint)
- **A** = subject (top domain): Memory, Learning, Social Psychology, …
- **B** = theme distributing a subject: Memory → Encoding, Storage, Retrieval, Forgetting.
- **C** = subtopic / detail: the concrete leaf terms.
- `part_of` = the taxonomic **home** (exactly one parent), membership *not* context. A term
  may relate by meaning to many foreign themes yet keeps one home.

## Pipeline (the "3 opuses")
1. **spine** — one Opus reads the whole term list → tier-A subjects (~10-14) + tier-B themes.
2. **classify** — fan-out batches: each term → `{tier, part_of}` against the spine.
3. **verify** — one Opus reconciles: full coverage, every `part_of` resolves, no orphans, dedup.

Returns a mapping `{spine, leaves, issues}`. `apply_tiers.py` writes it back — collision-safe
— and **materializes the spine notes** (parents must exist as real notes or `part_of` is a
silent ghost).

## Contract (verified against the generator, not assumed)
- Generator reads `name:` (**not** `title:`); node label = `name` or filename stem.
- `part_of:` resolves like a wikilink: `norm(part_of)` matched against `norm(name)` /
  filename-stem, where `norm = strip().lower().replace("-","_")` (spaces preserved).
- **Parents must exist as notes.** Spine A/B nodes are materialized; otherwise the child's
  `part_of` names nothing and no edge forms.
- A tier-B leaf whose `norm` collides with a same-named theme is **merged** into one node
  (no ghost duplicate, no data loss).

## Run
```sh
# 1. build a flat vault (example corpus: an open CC-BY psychology glossary)
curl -sL "<glossary-url>" -o gloss.html
python3 parse_pb.py gloss.html ./vault          # one note per term; name: + body

# 2. run the workflow (inside Claude Code)
#    Workflow({ scriptPath: 'tier_infer.wf.js',
#               args: { count: N, manifest: '<abs>/terms.json', vault: '<abs>/vault' } })
#    -> returns mapping; save it to mapping.json

# 3. apply (backs the vault up first)
python3 apply_tiers.py mapping.json ./vault

# 4. regen and view
./memory-atlas --src ./vault --out atlas.html   # switch to the `taxonomy` preset in-page
```

## Validation
See `RESULTS.md`. Validated on a **real** 334-term flat psychology glossary (open CC-BY,
not synthetic → the hierarchy was *not* baked in by us, so it is a non-tautological test):
**61 spine nodes, 375 `part_of` edges, 0 orphans** — 100 % of non-root nodes resolve.

> Not yet run on the live ~2300-term vault it was built for (that data sits on its owner's machine, not ours).
> The algorithm is scale-invariant; cost is ~linear (≈10 Opus agents / 334 terms).
