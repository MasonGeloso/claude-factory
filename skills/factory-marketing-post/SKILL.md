---
name: factory-marketing-post
description: The generic hourly dispatcher for the marketing pillar — reads `factory/marketing/schedule.md` to decide whether (and what) to fire this tick, then executes the matching content type(s) against their platform(s), respecting per-content-type autonomy mode and a per-(platform, account) lock so two lanes never fight over the same composer. Ends every autonomous run in a machine-checkable `RESULT: <STATUS> <detail>` line. This is normally invoked by the `marketing-post` cron agent — see `factory-agents/marketing-post/` — running non-interactively via `claude --chrome -p "..." --dangerously-skip-permissions`; it can also be run by hand for a dry-run check. Requires `factory/marketing/platforms.md`, `schedule.md`, and a `content-types/` file for each type it names — if any is missing, invoke `factory-marketing-onboard` instead. Use when the user says "run the marketing dispatcher", "check the posting schedule", "what would fire this hour", or the marketing-post cron agent invokes it.
---

# Factory — Marketing Post (the dispatcher)

*Every hour: check the timetable, and do whatever it says — no more, no less.*

This is the **one generic engine** that replaces a pattern of one bespoke script per content type.
All the per-project specifics (windows, caps, which platforms, how to build each content type) come
from `factory/marketing/` — this skill hardcodes none of it.

> **No human is watching this run** when it's invoked by the cron agent. Assume that unless one
> clearly is (e.g. invoked interactively for a dry-run check).

---

## Step 0 — Config check

Confirm `factory/marketing/platforms.md`, `schedule.md`, and `content-types/` all exist. If any is
missing, stop and say so — invoke `factory-marketing-onboard` (or tell the user to) rather than
guessing at values. Do not partially run with assumed defaults.

## Step 1 — What does this tick fire?

1. Read `schedule.md`. Get the current time in the schedule's declared timezone (not the machine's
   local time, not UTC — get this right, see that file's own notes on why).
2. For every row: check whether its **gate** says yes right now.
   - `time` gates: inside the window, under the daily cap (reset at local midnight in the schedule's
     timezone), past the min-gap since this content type's last fire, — if pacing is `even`, also
     check this content type isn't already ahead of where an evenly-spent daily cap should be by this
     hour (don't let ticks early in the window spend the whole budget before the window's later,
     often more valuable, hours).
   - `event:<...>` gates: do the **cheap existence check** the row names (a poll, a query) *before*
     invoking any content-building logic — if nothing new exists, this row contributes nothing to
     this tick, full stop, no content skill touched.
   - `floor:<N>d` gates: check days since this content type's **last successful publish** (read from
     the ledger, Step 4) — not days since its last run.
3. Collect every content type whose gate passed. It's normal for this to be zero, one, or several.
4. If anything fired, **add a random jitter delay** per that row's jitter range before acting — don't
   execute on a machine-perfect tick boundary.

## Step 2 — For each content type that fires

1. Read its file at `content-types/<content-type-id>.md` — the build steps (or which shipped content skill to
   invoke, e.g. `factory-marketing-recap`/`factory-marketing-clips`/`factory-marketing-dub`), which
   platform(s) it targets, its autonomy mode, and its de-slop language.
2. For each target platform, read its section in `platforms.md` — mechanics, and the **mandatory
   account-switch check**. Run that check before touching any composer, every single time, even if
   you "just" checked it for a different content type this same tick — never assume it's still true.
3. **Acquire a lock scoped to (platform, account)** before opening any composer on that platform —
   see Step 3. If it's held, skip this content type this tick and let the next tick retry; do not
   queue or wait.
4. Build the content per the content type's instructions.
5. If the de-slop language is set, run `factory-humanizer` (in that language) on the draft before it
   goes anywhere near a platform.
6. Publish per the content type's **autonomy mode**:
   - `autonomous-publish` — this run has standing authorization to publish; do not draft-and-stop,
     do not ask for permission. A post left sitting in a draft/composer unpublished is a **failed**
     run, not a partial success — report it as such (see Step 5).
   - `draft-only` — build it, save it as a draft (per the platform's own draft mechanics), and
     **stop there**. Never publish. This is correct behavior, not an incomplete run.

## Step 3 — The lock

One lock per (platform, account) — e.g. a lock file under `factory/marketing/.state/` keyed by
platform+account. Acquire it non-blocking (skip this tick, don't wait, if already held) before
opening any composer on that platform, and hold it for the whole build+publish sequence for that
content type. Two lanes sharing one account/browser and both opening a composer is exactly how a
double-post happens — this is not optional even when only one content type is firing this tick,
because a previous tick's run can still be in flight past its own slot.

## Step 4 — The ledger

Write one row per fire attempt to a canonical ledger under `factory/marketing/.state/` (gitignored —
this is high-churn bookkeeping, not editorial history) keyed by (content type, platform): timestamp,
outcome, and a detail (URL on success). Use this for the dedup/cap/gap/floor math in Step 1 on future
ticks. If a content type's own `content-types/<id>.md` file says to **also** keep a narrative in-repo
ledger (for low-volume editorial content worth a committed history), write that too — but the
canonical machine ledger always exists regardless.

## Step 5 — End every autonomous-publish attempt with a RESULT line

```
RESULT: POSTED <content-type> <platform> <url>
RESULT: NOTHING <content-type> <one-line reason nothing was worth doing>
RESULT: NOT_POSTED <content-type> <one-line reason you could not publish>
```

For `draft-only` content types, there's no publish outcome to report the same way — end with a plain
summary of what was drafted and where it's saved instead; do not fabricate a `RESULT:` line for a run
that was never meant to publish.

## Hard rules

- Never invent a gate, cap, or window value not present in `schedule.md` — if a row is ambiguous,
  stop and say so rather than guessing.
- Never publish `draft-only` content. Never sit on `autonomous-publish` content once every gate above
  has passed — a draft left unpublished on an autonomous lane is a failure, not caution.
- Never point `playwright-cli` or any headless browser automation at a platform this suite drives via
  Chrome — every platform starter says why (ban/mute risk). If Chrome tools are unavailable, stop and
  report it.
- Never put secrets, tokens, or credentials into a post, a draft, a ledger, or this run's output.
