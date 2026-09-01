# Board style — Excalidraw

Everything needed to draw the board. Read before creating elements.

## Interface

The `excalidraw-skill` CLI (or the bundled Excalidraw MCP tooling) drives a live canvas:

```bash
npx -y mcp-excalidraw-server start          # prints url + pid
# open http://127.0.0.1:3000 in a Chrome tab — screenshots need it
npx -y mcp-excalidraw-server add file.json
npx -y mcp-excalidraw-server apply patch.json
npx -y mcp-excalidraw-server screenshot --out shot.png
npx -y mcp-excalidraw-server export --out board.excalidraw
npx -y mcp-excalidraw-server share          # encrypted upload, returns a URL
```

Generate element JSON from a Python heredoc into a file, then `add` that file. Charts must be
computed from real data, never hand-typed coordinates.

## Palette

Pick a consistent role-based palette for this project and state it on the board the first time it
appears (some subjects have a domain convention worth following — e.g. some financial markets read
red-as-up/blue-as-down, the inverse of others; a non-market subject has no such convention and can
pick freely, but should still pick ONE scheme and hold it):

| Role | Example stroke | Example fill |
|---|---|---|
| Up / the subject | `#e03131` | `#ffc9c9` |
| Down / contrast | `#1971c2` | `#a5d8ff` |
| Neutral text | `#1e1e1e` | — |
| Muted / captions | `#868e96` | — |
| Mechanism chain | `#f08c00` | `#ffec99` |
| Resolution / the fix | `#2f9e44` | `#b2f2bb` |
| Inert | `#1e1e1e` | `#e9ecef` |

`fillStyle: "solid"` on every filled shape. The default hachure looks unfinished.

## Type

`fontFamily: "excalifont"` for everything except tabular blocks, which use `"cascadia"`.

| Use | Size |
|---|---|
| Board title | 48 |
| Cluster header | 26 |
| Big number | 60-68 |
| Body | 17-19 |
| Caption / axis label | 15-16 |

## Layout grid

Roughly four rows of three clusters. Each cluster 500-900px wide. Gutters of at least 120px
vertically between rows and 140px horizontally between clusters. A cluster is a header, its
graphic, and its notes — keep them within the cluster's own box so a later edit does not disturb a
neighbor.

Give every element an explicit `id` (short, mnemonic). Updates and any translated-language version
of the board both key off ids.

## Drawing a line chart from real data

```python
X0, Y0, W, H = 700, 120, 900, 300
lo, hi = <min>, <max>
def sy(v): return round(H - (v-lo)/(hi-lo)*H, 1)
line = [[round(i*(W/(len(pts)-1)),1), sy(v)] for i,(t,v) in enumerate(pts)]
# element: {"type":"line","x":X0,"y":Y0,"points":line,"strokeColor":BLUE,"strokeWidth":2,"roughness":1}
```

Downsample to 80-100 points. More is invisible and bloats the scene. Add dotted gridlines as
separate `line` elements at round values, with free-standing text for the axis labels.

Annotate the chart where the story is: a dashed vertical at the event, a filled dot on the
endpoint, and short text calling out the extremes.

### Axis-direction hazard

Some quantities are conventionally plotted "backwards" relative to what a viewer expects (e.g. a
currency pair quoted as one unit per the other, where the more intuitive direction is inverted).
Check whether this subject has such a convention — if a label reads "record low" while pointing at
the highest point on the line, it will trip people. Either name the quantity explicitly in the
label, or have the talk track explain the axis before quoting levels off that chart.

## Drawing, not charting

The failure mode this section exists to prevent: "these graphics feel lazy, just charts basically."
It's structural, not aesthetic — a rectangle with a number in it is three lines of Python, a
drawing is thirty, so a board drifts toward boxes unless you actively fight it.

**A chart is only correct when the point is a shape in real data** — a price path, a series over
time, a distribution. If the point is a *relationship*, a *mechanism*, or a *consequence*, it wants
a picture of the thing rather than a measurement of it. See the main skill's conversion table
("draw it, do not chart it") for examples.

### Crude on purpose

The drawings must look hand-made. That's the whole reason this format beats a slide deck.

- `roughness: 2` on every drawn shape. `roughness: 0` is for data lines only.
- No gradients, no shadows, no careful symmetry. Wobble is correct.
- Figures are 5 to 9 primitives. A stick figure with a circle head reads better than anything more
  ambitious, and it survives being small on a stream.
- Draw at 150-400px per figure. Smaller than that and it reads as clip art.
- Label parts with free-standing text and a short leader line. Never bind a label into a drawn
  shape.

### Primitives that compose into everything

Build these as Python helpers in the section script and reuse them. All of them are `line`,
`ellipse`, `rectangle` and `arrow` with high roughness; do not hand-author `freedraw` point arrays,
the pressure data is not worth it.

| Part | Made from |
|---|---|
| Person | `ellipse` head + `line` spine + two `line` arms + two `line` legs |
| Crowd | the same person at 60% scale, repeated 5-8 times on a jittered baseline |
| Container / tank | `rectangle` outline + a second filled `rectangle` inset for the level + a wavy 3-point `line` for the surface |
| Hole / leak | small `ellipse` on the wall + a 4-point `line` arcing away from it |
| Pour / flow | a 5-point `line` tapering down, plus 3 short `line` ticks for splash |
| Puddle | flat `ellipse`, solid pale fill, `roughness: 2` |
| Plug / cork | trapezoid via 5-point closed `line` |
| Mountain | 4-point `line` for the ridge, a second lower ridge behind it at 40% opacity |
| Flag | `line` pole + 4-point closed `line` triangle |
| Boat | 5-point closed `line` hull + `line` mast |
| Vice / press | two heavy `rectangle` jaws + two `arrow` pointing inward |
| Document | `rectangle` with a folded corner (2-point `line` across the top-right) + 3 short `line` ticks for text |
| Magnifier | `ellipse` + a thick `line` handle at 45° |

### Composition rules

- **The metaphor cluster gets the most drawing and the most space.** Give it a full row if it needs
  one. It's the thing people will screenshot.
- **One drawn scene per cluster, not a collage.** Several small drawings in one cluster read as
  decoration.
- **Every labelled part must map to a real part of the mechanism.** If a part of the picture has no
  referent, delete it. That's what separates a load-bearing metaphor from a doodle.
- **Keep the real charts real.** A line drawn from an actual data series stays a chart. Do not
  illustrate something you have actual data for.
- **Color still follows the palette.** A drawing that ignores the project's chosen palette stops
  matching the rest of the board.

## Anti-patterns

- **Never put a label on a large background rectangle.** Excalidraw centers bound text inside the
  shape, so it lands on top of whatever the zone contains and cannot be moved. Use a free-standing
  text element at the top-left of the zone instead.
- **Avoid long cross-cluster arrows.** They cut through everything between. Keep arrows inside a
  cluster; connect clusters with a short curved line in genuinely empty space plus a handwritten
  note.
- **Arrow labels sit at the midpoint** and collide with the shapes at both ends on short arrows.
  Prefer no label.
- **Check text against its container width.** Bound labels wrap; free text does not.

## Verify as you go

Screenshot after every section, view it, and fix before adding more. Crop large boards to inspect a
region:

```python
from PIL import Image
im = Image.open('shot.png'); w,h = im.size
im.crop((0, int(h*0.62), int(w*0.60), h)).save('crop.png')
```

Checklist per section: no truncated text, no overlap, arrows not crossing unrelated shapes, at
least 40px between elements, headers not colliding with the cluster above. A collision worth
watching for specifically: two elements that are each correct in isolation but overlap once placed
— only the screenshot reveals this, not the element JSON.

## Snapshots

```bash
npx -y mcp-excalidraw-server snapshot save <name>
npx -y mcp-excalidraw-server snapshot restore <name>
```

Save before `clear --yes`. The canvas holds one scene at a time, so building a translated-language
version of the board replaces the original one — export both to disk before switching.
