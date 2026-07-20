# Views & grouping — how the left bar composes

The HUD is one sentence: **LAYOUT is the shape, GROUP is the cut, COLOR is the ink.**
Every control below composes with every other — pick a shape, slice it by an axis,
ink it by a third one. Nothing here needs a rebuild; it is all live.

## The grouping axis (v2.10)

`GROUP` slices every grouping layout — `pack · ring · petals · radial · grid ·
zones · spine · facets · dendro · matrix` — and the force layout's link distances follow it too
(same-group notes cluster, cross-group edges stretch). Hull outlines and hull titles
follow the chosen axis as well.

| group | what it slices by |
|---|---|
| `cat` | category · auto — zone or cluster, whichever the corpus actually has. **The default** |
| `zone` | memory zones (index membership / top dir) |
| `root` | vault root (`--src name=dir`) — origin in a multi-root vault |
| `cluster` | louvain topology topics |
| `type` | note type from frontmatter |
| `tier` | the note's own `tier:` frontmatter field — what the `taxonomy` preset picks |
| `age` | recency buckets (week / month / quarter / year / older) |

The chosen axis persists (config), travels in saved views and in `?state=` /
`?group=` deep links.

### How many groups you actually see (v2.23)

The axis decides how many groups exist; the **layout** decides how many of them it can show.
Past that ceiling the tail is folded into a single `…` pile that gets no outline and no title —
so the number next to `GROUP` prints `shown/total` and turns amber when it truncates (hover it
for how many went into the fold). `cluster` on a few-hundred-note vault is the usual case: 53
topics, 15 shown, 38 folded.

| layout | sections it holds |
|---|---|
| `grid` | 32 |
| `zones` · `dendro` | 24 |
| `treemap` | 20 |
| everything else | 16 |

### Zones that adapt to the corpus (v2.23)

A vault that declares its zones from **folders** (`.atlas-zones.json`, or any foreign vault —
see [IMPORT-FORMATS](IMPORT-FORMATS.md)) gets two automatic passes so the zones stay apart
visually as their number grows:

- **Seating.** Zone anchors are ordered around the circle by *bridge mass* — the zones with the
  most cross-links between them sit next to each other, so their bridges are short arcs instead
  of edges dragged across the whole disc under everyone else's cloud. Alphabetical order is the
  tiebreak, so a corpus with no cross-links is seated exactly as before.
- **Colour.** Slots 0–7 keep the validated categorical palette unchanged; each further group of
  eight is that palette on a fixed value ladder (lighter → darker → lightest). A fourteen-folder
  vault reads as fourteen zones instead of six colours and a grey mass.

Both passes apply to derived zones only. A vault using the built-in index-file zones keeps its
hand-tuned anchors and its existing colours.

## Reading views (v2.10)

Three list-shaped layouts where **text is the first-class element** — names are
always readable, not decoration over dots:

### spine · list + arc

The strongest notes of every group as a central readable list with section
headers; the rest of the corpus on a surrounding arc, edges connecting arc to
list. On a small vault the whole corpus fits the list — a literal table of
contents. Task preset: **reading · list**.

![spine view](shots/view-spine.png)

### facets · panels

Group values sit on the perimeter as labeled mini-panels (top notes each), the
long tail fills the center disc inside its group's wedge. The perimeter reads
like a facet browser: what values exist, what their anchors are.

![facets view](shots/view-facets.png)

### dendro · tree

A radial dendrogram (group ⊃ cluster ⊃ note): the whole vault as one labeled
tree crown, every leaf name anchored outward from the rim.

![dendro view](shots/view-dendro.png)

### grid × group

The classic shelves, sliced by any axis — e.g. `group=cluster` turns the shelf
blocks into topic shelves:

![grid by cluster](shots/view-grid-cluster.png)

## Counting views (v2.21)

### matrix · what exists, and where it is thin

Rows are the grouping axis, columns a second one (note type, or age buckets when
the rows are already types). A cell's blob is its notes packed by phyllotaxis and
its radius is `pitch·√n`, so the mass you see **is** the count. A graph answers
*what links to what*; this answers *what do I have*. An empty cell is the finding.

### treemap · area = mass (released in v2.24)

A squarified treemap over the grouping axis: every group's rectangle is
proportional in **area** to how many notes it holds, and the notes fill their own
cell on a grid whose aspect follows the cell's. `matrix` answers *where is
nothing*; `treemap` answers *what is most of this vault*. Area rather than radius
on purpose — `pack`'s circles already say "big" by radius, which under-reads mass
by its square.

## The ⚗ dev door

Layouts that are **built but not yet through a release** live behind a third pill in the HUD
foot: off by default, persisted, and falling back to `force` if you switch it off while standing
in one of them. The pill only exists while something is behind it — with every view released it
hides itself rather than opening onto an empty room, and returns when the next view is built.

## Reading at a distance (v2.10)

- Node cards arrive early on the zoom ramp (`K≥0.95`, lowered again in v2.22) and carry **body
  text**:
  the curated `desc` first, then the note's own prose. Lines wrap on words, each
  line a touch quieter, the last line dissolving left→right into transparency —
  a card reads as an excerpt, not a chopped string.
- The ambient label budget is ~2.5× higher; collision-cull still governs, so it
  degrades to what physically fits.
- In spine/facets the list rows are never budget-culled — they are the reading
  surface.

## The rest of the left bar

| card | what it does |
|---|---|
| **вид / view** | color · size · layout · **group** · task presets (one-pick layout+color+layers) |
| **фокус · камера** | what selection does (dim / ego-blur / tiles) · camera policy (stay = manual zoom) |
| **подписи / labels** | who gets a name (hubs / hops / near / all) · density multiplier · collision cull · overlap |
| **плотность / density** | top-N by degree · edge alpha · node size |
| **слои / layers** | group hulls · ghost nodes · all-edges toggle (key 9) |
| **моушн / motion** | edge particles (direction = who references whom) · cursor magnet · gestures |
| **зоны / zones** | chips: hide/show a zone (keys 1–8) |
| **рёбра по типу** | edge layers per detector kind, incl. builder-declared kinds (provenance: `moved_from`, `became`) |
| **теги · линза** | tag lens: tagged notes stay, the rest dissolves; ∪/∩ multi-tag |
| **легенда / legend** | click a row = isolate the group; metric rows (e.g. `forgotten`) = threshold lens |
| **пины / pins** | rmb pin stack (context delivery), pin remembers its view |
| **виды / views** | saved camera+filters+layout+**group**+motion under a name |
