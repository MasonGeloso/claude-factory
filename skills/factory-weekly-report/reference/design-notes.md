# Design notes — what we learned building this

Distilled while turning an interactive dashboard prototype
(`references/tech-tree-dashboard/`) into a skill that renders a real weekly
report from a real tracker. Nothing here is specific to the project we
dogfooded it on. Read this before changing the template or the mapping.

---

## 1. A picture is not a dashboard with the mouse taken away

The prototype was interactive: pan, zoom, status filters, a click-through detail
panel, hover states, an "Allocate Resources" button. **None of that survives a
screenshot, and every control left behind renders as dead chrome** — a zoom
readout that can't zoom, a filter bar that filters nothing, a "Clear" button.
Worse than clutter: it's a lie about what the artifact does.

So the port deleted roughly half the code, and the deletions were the point.
What survived is what carries meaning on a flat page: position, colour, wiring,
and numbers. When you add to this template, ask what it says when nothing can be
clicked. If the answer is "it invites a click", it doesn't belong.

The corollary is that the *interactive* prototype was still the right thing to
design in — filters and a detail panel are how you discover which facts matter.
Just don't ship the scaffolding.

## 2. The tree's argument is the wiring

Lanes × tiers with no dependency edges is a **grid pretending to be a tree**. The
entire reason to spend this much pixel budget on a layout is to show that A is
blocked behind B and that shipping B unlocks three things. If the work has no
real dependencies, this is the wrong visualization — use a list.

Dependencies are also the one input with no standard source. Trackers hand you
labels, assignees and dates for free; "blocked by" lives in prose, in comments,
or in a human's head. Budget real effort for extracting it. **An invented edge is
worse than a missing one** — it fabricates an argument about the roadmap.

The failure mode to watch for is subtler than a missing edge: **if every edge you
draw runs within one lane, you have five independent rows, not a tree.** We did
exactly this on the first real pass — each lane a tidy left-to-right chain, which
looks plausible and says nothing. The board only earns its layout when lane A's
work is visibly gated on lane B's.

The fix is not to invent cross-lane edges; it's to go find the real ones, which
usually hide in label semantics rather than in an explicit "blocked by" field. On
our dogfood run the tracker's "must ship before launch" priority label *was* a
dependency statement — the launch announcement was gated on every open blocker,
in other lanes — and wiring that turned a flat grid into the actual story of the
week: the announcement flipped from `ready` to `locked`, which was both true and
the single most useful thing on the board. Record each inference next to the edge
(we keep a `_prereq_note` per node) so a reader can audit the claim.

## 3. Derive status; don't let humans declare it

`ready` and `locked` are computed: all prereqs done → ready, else locked. Only
`done`/`active`/`risk` are declared.

This isn't a style preference. A hand-set `ready` is a fact that was true when
someone typed it and silently rots the moment a prerequisite ships. Anything
derivable from other fields should be derived, so the report cannot contradict
itself. Same reason `progress` only paints on `active`/`risk`: progress on a
locked card is a number that cannot be true, so the template refuses to draw it.

A consequence worth knowing: with a strict `all prereqs done` rule, `ready` is
rare — in a tree where every tier-1 item is still in flight, *nothing* is ready
and the state never appears. That's honest, and the emptiness is information.

## 4. Don't fabricate a metric to fill a slot

The template inherited `budget` (dollars) and `crew` (headcount) from an
investment dashboard. Most software orgs have neither number, and the strong pull
is to invent them — assign plausible dollar figures so the pretty card isn't
empty.

Don't. **Relabel the slot to something the tracker actually knows, or drop it.**
Complexity labels become effort points; assignees become crew; if nothing is ever
assigned, `crew.cap: null` removes the stat rather than showing a fake headcount.
Which is why formatting is data (`prefix`/`suffix`/`decimals`) rather than
hard-coded `$…M` — the unit is a property of *your* org, so the template must not
have an opinion about it.

A number nobody can source is worse than a blank: it gets quoted back at you.

## 5. The board is a curation

5 lanes × 5 tiers ≈ 25 cards. Real backlogs are hundreds of issues. The mapping
step is therefore mostly **deciding what not to show**, and that's the step that
determines whether the report is any good — not the rendering.

Aggregate paper-cuts into one card. Prefer work that unblocks other work. An
empty lane is a statement worth making ("nothing is happening in Security"); an
empty *section* is just a hole. This is the part of the job that doesn't automate
away, so the skill spends its longest step there.

## 6. Hand-written fixtures lie about your layout

The prototype's fixture data was written by whoever designed the layout, so every
title fit on one line and every card looked perfect. Real tracker titles are
long, wrap, and contain `&`, `<`, quotes and emoji.

Two bugs came straight from this, both inherited from the source:

- **Fixed-height cards clipped wrapped titles.** The one fixture title that
  wrapped ran underneath its own metrics row. The card was sized for the happy
  path.
- **Columns sized to fixture strings truncated real ones.** The owner column fit
  the fixture's names and nothing longer.

Design against your ugliest real row, not your fixture. And escape everything:
tracker text is user input, and a title containing `</script>` will close the
payload's tag if the JSON isn't escaped on the way in.

## 7. The layout has invariants; enforce them in code

A card's position is `(lane, tier)`. Two cards in one cell therefore render at
the *same pixels* — the second silently covers the first. When you're folding 67
issues into 23 cards, putting two in one cell is a completely natural mistake,
and the output looks fine: you just quietly lose a card.

So the renderer validates and throws: one card per cell, lanes that exist, tiers
in range, prereqs that resolve. **The invariant that isn't checked is the one
that bites**, and a report is exactly the artifact where a silent omission does
the most damage — nobody can see what isn't drawn.

This also caps the board at 5×5 by construction, which is the curation forcing
function from §5 expressed as an assertion rather than advice.

## 8. Make bad data fail loudly, in a second

When validation first landed, invalid data threw inside the page, the renderer's
`wait_for_selector` never resolved, and 15 seconds later you got
`TimeoutError` — a message that describes the screenshot tool's disappointment
and not the two nodes sharing a cell.

Anything that renders in a headless browser has this shape: **the error is on the
other side of a process boundary, and the default is that it doesn't cross.** So
the page catches its own throw, writes the message into `body[data-error]`, and
the renderer waits on `ready or error`, then re-raises the real text. Bad data now
fails in 0.4s naming the node ids. Same principle applies to `pageerror` — hook it,
or a stray exception becomes another timeout.

## 9. Render offline or don't render

`file://` is an opaque origin in Chromium, so an external SVG sprite
(`<use href="icons.svg#…">`) **silently renders nothing** — no error, just
invisible icons. CDN fonts and icons are worse: the report's whole identity is
its type and its glyphs, and a flaky CDN means the artifact changes shape between
runs, or renders wrong exactly when you're offline.

So everything is inlined: fonts base64'd into CSS, icons packed into an inline
sprite, all of it assembled into one HTML string that `set_content` takes. Fetch
the vendored copies at build time (`scripts/build-assets.py`), commit them, and
never touch the network at render time. Only the `latin` subset is kept —
inlining every subset quadruples the file for glyphs a report never draws.

The happy accident: once assembly is "produce one self-contained string", the
standalone `.html` artifact is free. Emit it next to the PNG. It's the
debuggable version, and it's what you send when someone wants to read the 9px
text.

## 10. Screenshot mechanics that bite

- **`device_scale_factor=2`.** This design's aesthetic lives in 9–10px mono
  labels with wide tracking. At 1x they turn to mush and the whole thing reads as
  cheap.
- **Screenshot the element, not the viewport.** The report sizes itself to its
  content (which varies with tier count); a viewport screenshot either clips it
  or frames it in dead space.
- **Wait for a ready signal, not a timeout.** The renderer sets
  `body[data-ready="1"]` when it's done and the script waits on that, plus
  `document.fonts.ready`. Screenshot before fonts settle and you capture the
  fallback face — intermittently, which is the worst kind of bug.
- **Absolute px, not flex, for anything the maths touches.** Card positions and
  connector paths are computed from the same metrics object, so the wires meet
  the cards. Let flex reflow either and they drift apart.

## 11. Tokens are what make a retheme free

The prototype's two files are the same component in different skins — and the
whole reskin (near-black cyberpunk with a neon accent, over the original's
blue-grey and blurple) is **a block of CSS variable overrides and nothing else**.
That only worked because the original hard-coded no colours.

Hence: never a hex outside the `:root` blocks in `theme.css`. Lane colours are
the deliberate exception — they come from the data, because a lane's identity
belongs to the org, not the theme.

## 12. What actually makes this design read the way it does

If you're extending it, these are the load-bearing choices:

- **One accent, used as a line and a glow — never a flood.** Plus exactly one
  alarm colour, which is therefore impossible to miss. Everything else is a
  desaturated neutral ramp. Saturation is spent, not sprinkled.
- **Extreme type contrast.** 9–10px uppercase mono with 0.14em tracking against
  13–14px body sans. The micro-label does the work: it makes the thing read as
  instrumentation rather than a slide. Scaling type "up for readability" is what
  kills it.
- **Status is redundantly encoded** — dot, label text, border, and dimming all
  say the same thing. In a static image at unknown scale, on a projector, in
  someone's Slack thumbnail, redundancy is what survives.
- **Density is the message.** The whole quarter fits on one board. That's the
  report's entire claim, so anything that pushes it to two screens defeats it.

## 13. Save the data, not just the picture

The image is a snapshot; the value compounds in the diff. Keep each week's JSON
and next week can say what moved a tier, what slipped to `risk`, what's newly
unlocked — week-over-week movement is the most useful output, and it's nearly
free if the data was saved and nearly impossible to reconstruct if it wasn't.
