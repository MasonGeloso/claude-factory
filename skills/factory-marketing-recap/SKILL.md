---
name: factory-marketing-recap
description: Produce a recurring recap package — a researched narrative transcript, a hand-drawn Excalidraw board of clustered mini-graphics to talk over on video, an optional translated copy of that board, a per-graphic talk track, and an archived backup in the repo. Covers the PRE-production half of a periodic recap video (research → script → visual board → talk track → archive); hands off to `factory-marketing-video` for recording, cutting, dubbing, publishing, and shorts. Use when the user says "weekly recap", "build the recap board", "make this week's/period's recap video", "recap the period", or invokes /factory-marketing-recap.
user-invocable: true
---

# Factory Marketing — Recap (recurring commentary-over-a-whiteboard video)

Produces one package per recap period:

| Artifact | What it is |
|---|---|
| `transcript.md` | The narrative. Read-aloud prose, roughly 1,000-1,500 words. |
| `board-<lang>.excalidraw` + `.png` | A sprawling whiteboard of ~10 clustered mini-graphics. The thing on screen in the video. |
| `board-<other-lang>.excalidraw` + `.png` (if this project posts in more than one language) | Literal copy of the board, translated text, identical geometry. |
| `talk-track.md` | Bullets per graphic, in board reading order. What the presenter says while pointing. |
| `sources.md` | Every URL and data pull behind the numbers. |
| Archive | All of the above committed to a dated directory in the repo. |

The format is a person talking over a whiteboard they drew, not a slide deck — a board wins because
clusters can be pointed at in any order and the drawing carries the thinking. This is the
**generic method**; what the recap actually covers each period (which data sources, which questions
to chase) is project-specific and lives in this project's own file under `factory/marketing/content-types/`
entry for this content type, not in this skill.

**Read `references/narrative-craft.md` before Phase 1.** It holds the beat sheet, the spine rule,
the metaphor rule, and the "explain the engine, not just the event" rule — the difference between a
recap and an illustrated list of numbers.

---

## Phase 1 — Research

Cover this project's own recap period (read it from this content type's own file under `content-types/` — a trading week, a sprint,
a release cycle, whatever this project tracks) using this project's own data sources (also from that same
file — this skill has no opinion on what those are).

### Then answer these four, which are not lookups

Research is not finished when the numbers are in. These decide whether there is a story.

1. **What is the spine?** The one thing a viewer will remember. Write it at the top of
   `sources.md` before drawing anything. Everything else feeds it, contradicts it, or dates it.
2. **What is the engine?** The causal chain that *produces* the spine's headline fact, not the fact
   itself. If you cannot draw the chain, the research is not done. Test: could a viewer predict
   what happens next from what will be on the board?
3. **What is the selfish stake?** Why should someone with no direct exposure to this subject care?
   Find the channel by which it reaches them.
4. **Who acted, and what does their history say?** The biographical or institutional fact that
   makes an actor's own behavior testify about what they believe. One sentence of this beats a
   paragraph of analysis.

Also worth checking: **has someone already covered this well?** If so, find what's happened since
their piece, make that the spine, and credit them — being a period newer, with your own data, is
the edge a recap has over a single source.

### Verification rules — not optional

- **Reconcile any period-over-period numbers arithmetically** before they go on the board — a
  figure that doesn't chain correctly against the surrounding data points is wrong somewhere.
- **A headline number from one weak source is not verified.** Cross-check against a second source
  before it goes anywhere.
- **Pull the real series and draw it yourself** rather than screenshotting someone else's
  branded chart — that drags their logo onto your board, and cropping it off is worse, because it
  strips attribution from their product. Drawing from raw data removes the problem instead of
  hiding it.
- **Conflicts with your own previously published material get flagged, never silently resolved.**
  Put both versions in front of the user and let them decide.

Write every URL and data pull into `sources.md` as you go.

---

## Phase 2 — Transcript

Narrative prose, read-aloud, roughly 1,000-1,500 words. Sections with headers, no bullet lists.

**Structure comes from the beat sheet in `references/narrative-craft.md` §1**, applied to the
spine. A "supporting order" (open on the period's driver, then the rest in sequence) is used
*after* the spine has been told — it is not the shape of the piece by default.

Non-negotiable for the spine, all from `narrative-craft.md`:

- Open on something physical with a human-scale number attached, before any raw metric.
- Consequences before mechanism, for every audience this affects differently.
- Name the puzzle out loud, then reject the official/obvious explanation in its own words.
- Carry the engine, not just the event.
- One metaphor, mechanically load-bearing, reused to the end.
- End on a position, not a summary.

Run `factory-humanizer` (in this project's posting language) on the draft before moving on — no em
dashes, no bold-first bullets, no "it's not X, it's Y", no signposted conclusion, name sources
instead of "reports say".

---

## Phase 3 — The board

Full mechanics, palette, layout grid, and the element-JSON patterns are in
`references/board-style.md`. Read it before creating anything.

Sequence:

1. Start the canvas and open it in a browser tab (screenshots need the tab):
   ```bash
   npx -y mcp-excalidraw-server start
   ```
   Then navigate a Chrome tab to `http://127.0.0.1:3000`.
2. Plan the coordinate grid on paper first. Roughly four rows of three clusters, ~600-900px wide
   each, with 120px+ gutters.
3. Build **one section per call**, generating element JSON from a Python heredoc so charts come
   from real data rather than hand-typed coordinates.
4. **Screenshot after every section** and check it before adding the next. Overlaps compound and
   are far cheaper to fix immediately.
5. Add two or three connector lines between clusters at the end, in genuinely empty space, so the
   board reads as thinking rather than a grid of boxes.

### Draw it. Do not chart it.

**This is the rule the board fails on most.** A rectangle with a number in it is the cheapest thing
to emit from code, which is exactly why boards drift toward it unless you actively resist.

A chart is correct **only when the point is a shape in real data**: a price path, a distribution, a
series over time. Everything else wants a drawing. See `references/board-style.md` §Drawing, not
charting for the mechanics and the vocabulary of parts.

Before you build a cluster, ask what it looks like as a *picture of the thing* rather than a
*measurement of the thing*:

| Instead of | Draw |
|---|---|
| Two number cards | The two subjects as climbers on one mountain, one flag planted, one below the old summit |
| A stacked bar of money spent | A tank with a hole, money being poured in, the puddle draining away |
| Two negative bars for outflows | A door with one crowd leaving carrying bags and a different crowd coming in |
| A split bar for removals from a list | A boat with passengers going over the side into whatever used to carry them |
| A big percentage in a box | A subject in a vice, pressure from one side, a limit holding under from the other |
| A green box describing a feature | The document, the magnifier, and the yes/no answers falling out of it |

### Clusters that earn their place

Title + the core subjects · the key trend/rate chart · **the metaphor** · how the event/decision
happened (timeline) · **the engine** · period-by-period detail · the contradiction · the notable
number · a structural item · your own recently-published work (if relevant) · what decides the
next period.

Two of those carry the weight:

- **The metaphor cluster** is the spine's central image, drawn rather than written, with every
  part of it mapping to a real part of the mechanism. Rules in `references/narrative-craft.md` §7.
- **The engine cluster** is the causal chain that produces the headline fact. A board that shows an
  event without its cause cannot tell a viewer whether it continues. `narrative-craft.md` §13.

The contradiction cluster is usually the best moment on the board — two facts that are both true
and mutually corrosive.

---

## Phase 4 — Translated board (only if this project posts in more than one language)

A literal copy with translated text. Do not rebuild it by hand.

```bash
# 1. snapshot + export the original-language board
npx -y mcp-excalidraw-server snapshot save original
npx -y mcp-excalidraw-server export --out original.excalidraw

# 2. list every text-bearing element with its id
python3 -c "
import json; d=json.load(open('original.excalidraw'))
for e in d['elements']:
    t=e.get('text') or (e.get('label') or {}).get('text')
    if t: print(repr(e.get('id')),'|',repr(t))
"
```

Write an id-keyed translation map, then replace only the `text` / `originalText` / `label.text`
fields, leaving every coordinate untouched. Load with `clear --yes` then
`import translated.excalidraw --replace`.

Bound labels inside shapes carry generated ids (random strings) rather than the ids you set — key
off whatever the inventory prints.

Run `factory-humanizer` on the translated text too, in that language.

Check the target script's rendering behavior before trusting a layout ported from another language
— e.g. CJK text falls back to a different font even when a Latin font is requested, and any layout
that lined up columns with padding spaces breaks under a proportional fallback font and needs
rewriting as ordinary sentences.

---

## Phase 5 — Talk track

Bullets per graphic, in board reading order, so the presenter can point and talk without hunting.

For each cluster: 4-6 bullets of what to say, then a **"The point to land"** line closing the
cluster.

### Write it in plain language. This is the rule that gets broken most.

Every piece of domain jargon must be spelled out — the presenter is talking to a camera, not to a
room of peers who already share the shorthand.

Also required:

- **Carry the metaphor's vocabulary through every later cluster.** Once the spine's image is
  established, later clusters refer back to its parts by name rather than restating the mechanism.
  A metaphor used once and dropped should be deleted from the board and the space reclaimed.
- **Explain the mechanism as dialogue where it has two sides.** Two speakers removes jargon
  automatically. `references/narrative-craft.md` §6.
- **Jokes are allowed when the joke is the explanation.** Strict test: does removing it cost the
  viewer a fact? If not, cut it.
- **Explain any counterintuitive axis before the numbers**, if this subject has one (see
  `board-style.md`'s axis-direction hazard).
- **Mark unresolved conflicts inline with ⚠️** at the exact point the presenter would say the
  disputed number, with both versions and the options.
- **Volunteer limitations before anyone asks.** If your own material has a caveat, say so
  proactively — conceding it under questioning lands far worse.
- Park two or three extra facts at the end for questions rather than the main walkthrough.

---

## Phase 6 — Archive

Everything goes in the repo so the boards survive the canvas server being wiped.

```
<content-type-name>/YYYY-MM-DD/          # the date this period ends
├── README.md                            # date, headline, share links for both boards, one-line summary
├── transcript.md
├── talk-track.md
├── sources.md
├── board-<lang>.excalidraw (+ the translated one, if applicable)
├── board-<lang>.png (+ .png)
└── data/                                 # raw series behind any chart drawn on the board
```

Get shareable links for both boards before archiving:

```bash
npx -y mcp-excalidraw-server share
```

Then commit and push, **only if this content type's own file under `content-types/` grants standing
authorization for this specific archive-and-push workflow** — do not assume it; check first, the
same way any other autonomous-publish authority in this suite has to be stated explicitly rather
than assumed. Keep the commit scoped to the recap folder — if unrelated changes are sitting in the
working tree, stage only the recap paths.

---

## Handoff to production

Recording is a human step. Once the presenter has recorded talking over the board, hand off to
**`factory-marketing-video`** for everything downstream — it owns transcription, cutting, dubbing,
YouTube publishing (human-gated: file selection and the final Publish click are both manual there
by design), and shorts generation. Don't re-derive that mechanics here; invoke that skill by name.
The phase order that skill expects: publish the long-form video(s) first → upload transcripts →
cut shorts → any additional-language cuts, in that order.

## House rules that apply throughout

- Every non-English/non-primary-language line shown gets a rough gloss in the project's primary
  language underneath, if the audience needs it.
- No invented terminology presented as established vocabulary.
- Report what was actually verified. If a number came from one source, say so.
- Do not use Unicode arrows in prose. On the board, draw them.
