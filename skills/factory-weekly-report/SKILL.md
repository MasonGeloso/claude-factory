---
name: factory-weekly-report
description: Generate a weekly report as a single image — a tech-tree investment board showing where the work stands, what's in flight, what's blocked, and what shipped. Surveys the tracker and repo, curates the load-bearing work into lanes and time tiers, renders a PNG (plus a standalone HTML). Reads per-project rules from the repo's `factory/` directory. Use when the user runs /factory-weekly-report, says "weekly report", "generate the tech tree", "the investment board", or wants a shareable picture of where things stand.
---

# Factory — Weekly Report

*Once a week: the whole org on one board — what shipped, what's moving, what's blocked behind what.*

The output is an **image**, not a document. It gets pasted into a channel, a deck, or an investor update, and it has to survive being looked at for eight seconds. Everything below serves that.

The board is a **tech tree**: work areas as horizontal lanes, time horizons as vertical tiers, initiatives as cards wired to their prerequisites. It reads as an investment board because that's the useful frame — it shows where effort is committed and what that spend unlocks.

Companion to `/factory-daily-digest` (a text pulse, daily). This is the weekly picture.

---

## Step 0 — Locate config

Find `factory/` at the repo root and read what's there:

- `intake.md` — the tracker and its CLI, plus the label taxonomy (priority/complexity). **Required.**
- `codebases.md` — the repo(s) and their components. Seeds the lanes.
- `ownership.md` — who owns what. Fills DRIs.
- `priority.md` — the current priorities. Fills the "Priorities This Week" row.
- `communication.md` — where to post the image, if posting.

If `intake.md` is missing: interactive → route to `/factory-onboard`; unattended → log and stop. Missing optional files degrade a section, they don't stop the run — see *Sections are optional* below.

## Step 1 — Gather

Over the last **7 days** (widen after a gap). The window is 7 days **regardless of how often this runs** — the `weekly-report` agent posts every morning by default, which republishes a refreshed weekly board rather than reporting on a single day. Cadence and window are independent; don't shrink one to match the other.

- **Open issues** with labels, assignees, and update times.
- **Closed issues** and **merged PRs** in the window — these are "shipped" and the throughput series.
- **Per-day merge counts** for the last 14 days — the bar chart wants a 14-length integer series.
- **Commits** for themes the tracker missed.
- **Blocked-on / depends-on** relationships, from issue bodies, comments, or a `blocked-by` label. This is the one input with no standard source. Read for it deliberately — the tree's whole argument is the wiring, and if you skip this you will produce a grid pretending to be a tree.

## Step 2 — Curate (the step that matters)

**The board is a curation, not a dump.** The layout holds about **5 lanes × 5 tiers ≈ 25 cards**. A 60-issue backlog does not become 60 cards; it becomes the ~20 pieces of work that a reader needs to understand the quarter. Everything else is noise you are deliberately dropping.

- **Lanes (4–6, ideally 5)** — the org's real work areas, from `codebases.md` and what the issues are actually about. Not label names. Each lane gets a colour that belongs to the org, and keeps it across weeks.
- **Tiers (5)** — time horizons, left to right: what's **shipped**, what's **in flight now**, what's **next**, what's **later**, what's **horizon**. Tier 0 is the foundation the rest builds on; put genuinely-landed work there, not everything ever closed.
- **Cards** — epics and load-bearing issues. Aggregate paper-cuts into one card ("Public-page polish · 6 issues") rather than spending five slots on them. Prefer the issue that unblocks other issues.
- **Status** — declare only `done`, `active`, `risk`. `ready` and `locked` are **derived** from prerequisites by the renderer and must not be hand-set.
- **Prereqs** — wire real dependencies only. An invented edge is worse than a missing one.

## Step 3 — Map the metrics honestly

The template carries two numeric slots per card, `budget` and `crew`, drawn from the investment metaphor. **Most software orgs have neither number.** Do not invent dollars.

Relabel the slot to something the tracker actually knows, via `capital` and `crew` in the data:

- **`budget`** → effort/complexity points from the complexity labels (e.g. E1=8, E2=3, E3=1), rendered as `"suffix": " pts"`. Then "capital committed" honestly means "effort committed".
- **`crew`** → assignees, or agents/sessions on the work. If nothing is ever assigned, set `crew.cap` to `null` — the stat drops out of the header and the per-card figure shows an em-dash rather than a fake headcount.

State the unit in the label. A reader who thinks `◆ 8` is dollars has been misled by the report.

## Step 4 — Render

Write the data JSON (schema: `reference/data-schema.md`), then:

```bash
python3 skills/factory-weekly-report/scripts/render.py <data.json> -o <out.png>
```

Writes `<out.png>` and a standalone `<out.html>` beside it. The HTML inlines its fonts, icons and styles — it opens anywhere with no network and no sibling files, so it's what you share when someone wants to read the small text. Add `--open` to open it in the browser (`xdg-open`).

**Look at the PNG you just made.** Read it back and check it as a picture — clipped titles, an empty lane, a bar chart of one value, a `0%` where a number should be. It is an image; nothing but your eyes will catch an image bug.

## Step 5 — Post and record

Post where `communication.md`'s **Scheduled posts** table names for `weekly-report`, with a two-line summary — the image is the artifact, the text is the pointer. Use the upload call it specifies: attaching a PNG is a different API call from posting text, and a destination without one can't receive this report.

If the row has **no destination**, or `communication.md` doesn't exist: write the artifacts locally, say so plainly, and post nothing. Never guess a channel.

Keep the data JSON (e.g. `factory/reports/YYYY-MM-DD.json`) so next week can diff against it: what moved a tier, what slipped to risk, what's newly unlocked. Week-over-week movement is the most valuable thing this report produces, and only the saved data makes it cheap.

Normally invoked by the **`weekly-report` cron agent** (`claude -p … --dangerously-skip-permissions`), so assume **no human is watching**: nothing but your own check stands between a broken render and a channel.

---

## Sections are optional

Each section renders only if its data is present. Omit rather than pad:

| Section | Omit when | Key |
| --- | --- | --- |
| Priorities This Week | no `priority.md`, no agreed priorities | `priorities` |
| Throughput chart | no merge history worth plotting | `throughput` |
| Recently Shipped | nothing landed | `shipped` |
| Crew stat | nothing is ever assigned | `crew.cap: null` |

An empty lane is a statement ("nothing is happening in Security"). An empty *section* is just a hole. If a lane is genuinely empty, either say so deliberately or drop the lane.

## Design constraints

Non-negotiable, because they're what make it read as one thing — the full reasoning is in `reference/design-notes.md`:

- **Two themes, `cyber` (default) and `nocturne`.** A theme is a block of token overrides and nothing else. Never hard-code a colour outside `theme.css`.
- **The accent is a line and a glow, never a flood.** One accent, one alarm colour. Lane colours are the only other hues, and they come from the data.
- **Density is deliberate.** 9–10px uppercase mono micro-labels against 13–14px body — that contrast is the whole aesthetic. Don't "fix" it by scaling type up.
- **Nothing interactive.** No hover states, filters, or controls: the output is flat, and a control in a picture is a lie.
