# Factory Marketing — Schedule — <PROJECT NAME>

> The timetable. Read by `/factory-marketing-post` every time its cron agent ticks (hourly, by
> default). Only **scheduled** content types (from their files under `content-types/`) appear here — `on-demand` ones
> never do, the dispatcher doesn't look at them.
>
> The dispatcher ticks once an hour. On each tick it evaluates every row below against the current
> time (in that row's timezone) and fires every content type whose gate says yes this hour — a single
> tick can fire zero, one, or multiple content types.

## Timezone

- **Default timezone for this project's schedule:** <e.g. `Asia/Tokyo` — all windows below are in
  this timezone unless a row overrides it>

## Rows

<!-- One row per scheduled content type. Keep the table below, add rows as needed. -->

| Content type | Window(s) | Daily cap | Min gap | Jitter | Pacing | Gate |
|---|---|---|---|---|---|---|
| <name, matches a `content-types/<id>.md` file> | <e.g. `09:00-17:59`, or `all-day` split into your own slots> | <max fires per calendar day in this timezone, or "n/a" if gated purely by min-days-between> | <minimum minutes between fires, so ticks don't fire back-to-back> | <e.g. "1-30 min" — random delay after the tick decides to fire, before it actually acts, so publishes don't land on a machine-perfect boundary> | <`even` — spend the daily cap evenly across the window rather than as fast as ticks arrive \| `none`> | <`time` — pure time/cap-based \| `event:<what to poll>` — only fires when something new appears (e.g. "a new item in <data source>"), checked cheaply without invoking the content skill, at a possibly-different cadence than the window above \| `floor:<N>d` — a minimum number of days since the **last successful publish** (not the last run), for low-frequency editorial content> |

## Notes on gate types (read before writing a row)

- **`time`** — the simplest case: fire if inside the window, under the daily cap, past the min gap,
  after adding jitter. This is the right choice for most autonomous scheduled posting.
- **`event:<...>`** — for content gated on something external appearing (a new filing, a new data
  point). The dispatcher should do the cheap existence check itself (no content skill invoked) before
  deciding to fire — an ungated version of this that fires the full content-building skill every tick
  just to find "nothing new" burns a full run for no output. Track what's already been seen/handled
  in the same `factory/marketing/.state/` ledger the dispatcher already uses for dedup.
- **`floor:<N>d`** — for expensive, low-frequency content (e.g. one long-form piece every few days).
  Measure the floor from the last **successful publish**, not the last run — a run that correctly
  found nothing worth doing should be free to try again next tick, not locked out for N days by its
  own restraint.
- A day boundary always resets in the **project's own timezone**, not the machine's local time or
  UTC — a cap or floor that resets at the wrong moment can silently grant a double budget or cut one
  short right at the boundary. Get this right; it has caused real incidents in the systems this
  pattern was generalized from.
