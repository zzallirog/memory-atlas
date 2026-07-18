export const meta = {
  name: 'atlas-tier-infer',
  description: 'Infer A/B/C taxonomy tiers + part_of parents for a flat psychology glossary (#4 engine)',
  phases: [
    { title: 'Spine',    detail: 'Opus derives tier-A subjects + tier-B themes from the full term list' },
    { title: 'Classify', detail: 'fan-out: each batch assigns every term a tier + part_of parent' },
    { title: 'Verify',   detail: 'Opus reconciles: coverage, part_of resolves, orphans, dedup' },
  ],
}

// Pass the manifest in: Workflow({scriptPath, args: {manifest: '<abs>/terms.json', count: N}}).
// It used to be a hardcoded absolute path from the machine it was written on — which both
// leaked that path into a public repo and made the script unrunnable anywhere else.
const MANIFEST = (args && args.manifest) || './terms.json'
const COUNT = args && args.count ? args.count : 334
const BATCH = 42
const nBatches = Math.ceil(COUNT / BATCH)

const SPINE_SCHEMA = {
  type: 'object', required: ['subjects', 'themes'], additionalProperties: false,
  properties: {
    subjects: { type: 'array', items: { type: 'object', required: ['name'], additionalProperties: false,
      properties: { name: { type: 'string' }, gloss: { type: 'string' } } } },
    themes: { type: 'array', items: { type: 'object', required: ['name', 'parent'], additionalProperties: false,
      properties: { name: { type: 'string' }, parent: { type: 'string' }, gloss: { type: 'string' } } } },
  },
}
const ASSIGN_SCHEMA = {
  type: 'object', required: ['assignments'], additionalProperties: false,
  properties: { assignments: { type: 'array', items: {
    type: 'object', required: ['term', 'tier', 'part_of'], additionalProperties: false,
    properties: { term: { type: 'string' }, tier: { type: 'string', enum: ['A', 'B', 'C'] }, part_of: { type: 'string' } } } } },
}
const FINAL_SCHEMA = {
  type: 'object', required: ['spine', 'leaves'], additionalProperties: false,
  properties: {
    spine: { type: 'array', items: { type: 'object', required: ['name', 'tier', 'part_of'], additionalProperties: false,
      properties: { name: { type: 'string' }, tier: { type: 'string', enum: ['A', 'B'] }, part_of: { type: 'string' } } } },
    leaves: { type: 'array', items: { type: 'object', required: ['term', 'tier', 'part_of'], additionalProperties: false,
      properties: { term: { type: 'string' }, tier: { type: 'string', enum: ['B', 'C'] }, part_of: { type: 'string' } } } },
    issues: { type: 'array', items: { type: 'string' } },
  },
}

const TYPING = `Typing model (intro-psychology taxonomy):
- Tier A = SUBJECT (top domain): e.g. Memory, Learning, Social Psychology, Sensation & Perception, Development, Biopsychology, Personality, Psychological Disorders, Cognition, Motivation & Emotion, Consciousness, Research Methods.
- Tier B = THEME distributing a subject: e.g. under Memory -> Encoding, Storage, Retrieval, Forgetting.
- Tier C = SUBTOPIC / type / detail of a theme: the concrete leaf terms.
part_of = the TAXONOMIC HOME (exactly ONE parent), membership NOT context. A term may relate by meaning to many foreign themes yet keeps one home. Keep the A-spine small (~10-14 subjects); every B theme has exactly one A parent; every leaf gets exactly one parent (a B theme preferred, an A subject only if no theme fits).`

phase('Spine')
const spine = await agent(
  `${TYPING}

Read the full flat glossary at ${MANIFEST} (JSON array of {term, def}, ${COUNT} intro-psychology terms, no hierarchy).
Derive the TAXONOMY SPINE for this corpus:
- subjects: ~10-14 tier-A domains that cover these terms.
- themes: tier-B themes, each with parent = one subject name (exact). Aim ~2-6 themes per subject, only themes the corpus actually needs.
Names must be clean canonical titles (e.g. "Sensation and Perception", "Classical Conditioning"). Subject and theme names must all be UNIQUE across the whole spine. Return ONLY the structured spine.`,
  { label: 'spine', phase: 'Spine', agentType: 'general-purpose', schema: SPINE_SCHEMA },
)
log(`spine: ${spine.subjects.length} subjects, ${spine.themes.length} themes`)
const spineJson = JSON.stringify(spine)

phase('Classify')
const batchResults = await parallel(
  Array.from({ length: nBatches }, (_, i) => () =>
    agent(
      `${TYPING}

SPINE (the only valid parents — a leaf's part_of MUST be one of these exact subject or theme names):
${spineJson}

Read ${MANIFEST} (JSON array of ${COUNT} {term, def}). Take ONLY the slice terms[${i * BATCH}:${Math.min((i + 1) * BATCH, COUNT)}] (0-indexed, that exact range).
For EACH term in your slice assign:
- tier: "C" for a concrete leaf (most terms), "B" only if the term itself IS a theme-level concept present in the spine themes.
- part_of: the EXACT name of its single taxonomic-home parent from the SPINE (prefer a B theme; use an A subject only if no theme fits).
Assign every term in your slice exactly once. part_of must be copied verbatim from the spine. Return ONLY the assignments for your slice.`,
      { label: `classify:${i * BATCH}-${Math.min((i + 1) * BATCH, COUNT) - 1}`, phase: 'Classify', agentType: 'general-purpose', schema: ASSIGN_SCHEMA },
    ),
  ),
)
const assignments = batchResults.filter(Boolean).flatMap(r => r.assignments)
log(`classify: ${assignments.length}/${COUNT} terms assigned across ${batchResults.filter(Boolean).length}/${nBatches} batches`)

phase('Verify')
const final = await agent(
  `${TYPING}

You are the reconciliation pass. Inputs:
SPINE = ${spineJson}
ASSIGNMENTS (${assignments.length} of ${COUNT} expected) = ${JSON.stringify(assignments)}

Produce the FINAL taxonomy mapping, fixing every defect:
1. Coverage: read ${MANIFEST} and ensure EVERY one of the ${COUNT} terms appears exactly once in leaves. Add any missing term (classify it yourself). Drop duplicates.
2. Resolvability: every leaf.part_of MUST equal a spine node name (a subject or a theme). Every theme.part_of MUST equal a subject name. Fix any part_of that does not resolve (reassign to the best-fitting existing spine node; do NOT invent new spine nodes unless a whole cluster is clearly missing a home — if so add a minimal theme).
3. Shape: A-spine small (~10-14). No node is its own parent. All spine names unique.
Output:
- spine: every subject (tier A, part_of "") and every theme (tier B, part_of = its subject).
- leaves: every one of the ${COUNT} terms with tier (B/C) and a resolving part_of.
- issues: short notes on what you fixed (orphans reassigned, terms added, themes merged).
Return ONLY the final structured mapping.`,
  { label: 'verify-reconcile', phase: 'Verify', agentType: 'general-purpose', effort: 'high', schema: FINAL_SCHEMA },
)
log(`final: ${final.spine.length} spine nodes, ${final.leaves.length} leaves, ${(final.issues || []).length} issues fixed`)

return final
