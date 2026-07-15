# Weekly report — data schema

One JSON file drives the whole image. `assets/sample.json` is a complete, working
example; render it with `python3 scripts/render.py --sample -o /tmp/s.png`.

Unknown keys are ignored, so it's safe to keep extra context (issue URLs, notes)
in the file for next week's diff.

## Top level

| Key | Type | Notes |
| --- | --- | --- |
| `org` | string | Big name, top left. |
| `subtitle` | string | The mono kicker under it — the report's frame, e.g. `"FY26–27 · milestones, dependencies and where the effort is going"`. |
| `week` | string | Shown beside the priorities badge, e.g. `"Week of Jul 14"`. |
| `theme` | `"cyber"` \| `"nocturne"` | Default `cyber`. |
| `mark` | icon name | The glyph in the header badge. Default `tree`. |
| `capital` | object | How to render the `budget` slot. See below. |
| `crew` | object | How to render the `crew` slot. See below. |
| `lanes` | array | Work areas — rows. 4–6, ideally 5. |
| `tiers` | array | Time horizons — columns. 5. |
| `nodes` | array | The cards. |
| `priorities` | array | Optional. The three cards up top. |
| `throughput` | object | Optional. The bar chart. |
| `shipped` | object | Optional. The feed table. |

## `capital` / `crew`

The two numeric slots on every card. **Relabel them to what you can actually
measure** — see the SKILL's *Map the metrics honestly*.

```jsonc
"capital": { "label": "Effort committed", "prefix": "", "suffix": " pts", "decimals": 0 },
"crew":    { "label": "Crew deployed", "cap": 12 }
```

- `label` — the header stat's name. Must state the unit.
- `prefix` / `suffix` / `decimals` — formatting for `node.budget`. `{"prefix":"$","suffix":"M","decimals":1}` gives `$1.2M`; `{"suffix":" pts","decimals":0}` gives `8 pts`.
- `crew.cap` — the denominator for the "deployed" stat. **Set `null` to drop the stat entirely** when nothing is meaningfully assigned. Don't invent a headcount.

## `lanes`

```jsonc
{ "id": "api", "name": "API & Services", "icon": "stack", "color": "#2ee6e6" }
```

`color` is the lane's identity — keep it stable across weeks so readers learn it.
Icons available: `stack brain rocket chart shield database globe gear bug sparkle
git-branch git-merge tree user flag check circle-notch lock lock-open warning
target github`. Add more via `scripts/build-assets.py` (edit `ICONS`, re-run).

## `tiers`

```jsonc
{ "label": "Tier I", "sub": "Shipped" }
```

`label` is the tier's name, `sub` its meaning. Left to right = now to horizon.

## `nodes`

```jsonc
{
  "id": "a2",              // unique; referenced by prereqs
  "lane": "api",           // a lanes[].id
  "tier": 1,               // index into tiers[]
  "name": "Realtime Inference",
  "status": "active",      // done | active | risk   (see below)
  "budget": 1.1,           // the capital slot
  "crew": 7,               // the crew slot; 0 renders as an em-dash
  "progress": 40,          // 0-100; only drawn for active/risk
  "prereqs": ["a1", "p2"], // node ids this depends on
  "ref": "#175"            // optional; small mono tag in the card corner
}
```

**Only ever declare `done`, `active`, or `risk`.** `ready` and `locked` are
derived: a node whose prereqs are *all* `done` renders as `ready` (accent border,
faint glow), otherwise `locked` (dimmed). Hand-set values for these two are
overwritten — they'd go stale the moment something ships. Set `ready`/`locked` as
the input value to mean "not started"; the renderer decides which one it is.

`progress` only paints for `active`/`risk`, because progress on a locked card is
a number that cannot be true.

## `priorities`

```jsonc
{ "title": "Ship multi-region failover", "lane": "platform",
  "dri": "A. Vasquez", "role": "SRE Lead", "initials": "AV",
  "target": "Fri Jul 18", "progress": 60 }
```

Takes the lane's colour. `dri` is optional — omit the whole block and the card
still renders. Three is the design's column count; other counts stretch to fill.

## `throughput`

```jsonc
{
  "title": "PR Throughput",
  "subtitle": "Merged per day · last 14 days",
  "values": [8, 11, 7, 13, 9, 4, 3, 12, 15, 10, 14, 9, 17, 13],
  "startLabel": "2 wks ago", "endLabel": "today", "totalLabel": "this wk"
}
```

`values` is oldest → newest; the last bar is highlighted as "today". The headline
number is the sum of the **back half**, the delta compares it to the front half —
so a 14-length series gives a true week-over-week. Other lengths still work but
the "WoW" label stops being literal. A zero front half suppresses the delta
rather than printing an infinite percentage.

## `shipped`

```jsonc
{
  "title": "Recently Shipped", "window": "Last 7 days",
  "repoUrl": "https://github.com/org/repo/issues",
  "metaLabel": "Lane / Owner",
  "items": [
    { "type": "Feature", "title": "…", "meta": "API · M. Okafor",
      "time": "2h ago", "ref": "#2841" }
  ]
}
```

`type` is colour-coded: `Feature`, `Fix`, `Improvement`, `Docs`, `Infra` (anything
else renders neutral). `ref` links to `repoUrl/<ref>` unless the item sets an
explicit `href`. Six rows is what the panel fits beside the chart.
