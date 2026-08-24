# Weekly Tech-Tree Report (`weekly-report`)

A cron-style Factory agent that curates the tracker into a tech-tree investment
board — lanes of work across time tiers, wired to their dependencies — renders it
to a PNG, and posts it where the org wants it. The output is a picture you can
paste into a channel or a deck and understand in eight seconds.

Companion to [`daily-digest`](../daily-digest/README.md): that one is a text pulse
of *what moved*, this is the picture of *where everything stands*.

## Cadence vs window — two separate knobs

The board is **weekly-shaped**: a rolling 7-day window of shipped work, a 14-day
throughput chart, and a roadmap that moves at roadmap speed. That's the *window*,
and it's fixed by the design.

**How often you post it is a separate choice.** The default is every morning at
09:00 (`1440`), which republishes a freshly-refreshed board each day — most of the
tree is unchanged, but "what's in flight" and "recently shipped" are current, and
a blocker flipping to `at risk` shows up the morning it happens rather than next
Monday. Use `--interval 10080` if you'd rather it land once a week.

So: `weekly-report` running daily is not a contradiction — it's a weekly board,
refreshed daily.

## What it does each run

1. Reads `factory/communication.md` (where to post — see its **Scheduled posts**
   section) and `factory/intake.md` (the tracker + CLI). Reads `codebases.md`,
   `ownership.md` and `priority.md` if present. Everything org-specific — the
   lanes, what the metrics mean, the destination — lives in that directory, so
   the same agent behaves differently per repo without any code change.
2. Surveys the last 7 days: open issues, closed issues, merged PRs, per-day merge
   counts, and any dependency links it can find.
3. **Curates** the backlog down to ~25 cards across ~5 lanes and 5 time tiers.
   This is the step that decides whether the report is any good.
4. Renders the board to `factory/reports/YYYY-MM-DD.png` (plus a standalone
   single-file `.html` and the source `.json`).
5. Posts the image where `communication.md` says, with a short summary.

The scheduled command is trivial and identical everywhere — it just tells Claude
Code to run `factory-weekly-report` (see `prompt.md`). All per-org behavior comes
from the target repo's `factory/` directory.

## Install

```bash
factory agents install weekly-report /path/to/repo                   # default: daily 09:00
factory agents install weekly-report /path/to/repo --interval 10080  # once a week, Mondays 09:00
```

On Linux, `1440` schedules as `0 9 * * *` and `10080` as `0 9 * * 1` — a real
day-of-week cron, so a weekly post lands on the same weekday every week. On macOS
it's a launchd `StartInterval`. Other multi-day intervals are rejected rather than
scheduled: cron can only express them via day-of-month stepping, which resets at
month boundaries and drifts across weekdays.

## Requirements

- `factory/` onboarded (`/factory-onboard`), including `communication.md` +
  `intake.md`. The install will route you into onboarding if they're missing.
- Claude Code on `PATH`.
- Python with Playwright + Chromium, for the render step:
  `pip install playwright && playwright install chromium`.

## Notes

- The renderer touches no network — fonts and icons are vendored into the skill.
- If the render fails or the data is invalid, the agent posts nothing and logs
  the reason. A silently wrong board is worse than a missed week.
- Each run keeps its `.json`, so week-over-week diffs (what moved a tier, what
  slipped to risk, what's newly unlocked) are cheap.
