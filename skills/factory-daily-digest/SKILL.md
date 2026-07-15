---
name: factory-daily-digest
description: Produce a concise daily digest of what's happening across an org's systems. Surveys recent activity (commits/diffs, tracker changes, conversation) over the last day or two, writes a short bullet-point TLDR of what's being worked on, and posts it where the org wants — factoring in current priorities and flagging them when they've gone stale. Reads per-project rules from the repo's `factory/` directory. Use when the user runs /factory-daily-digest, says "daily digest / standup", or the daily-digest cron agent invokes it.
---

# Factory — Daily Activity Digest

*Once a day: what moved, what's in flight, what to watch — in a few bullets.*

Normally invoked by the **`daily-digest` cron agent** (`claude -p … --dangerously-skip-permissions`), so assume **no human is watching**. It can also be run by hand. It only ever **reads and reports** — it never edits code or the board (that's the AI PM's job).

**Every org surveys different systems and posts to different places**, so nothing is hard-coded. It reads:
- `factory/communication.md` — where to post the digest, and which channels/conversation count as "activity".
- `factory/intake.md` — the tracker and its CLI.
- `factory/codebases.md` (if present) — the repo(s) to inspect for commits/diffs.
- `factory/priority.md` (if present) — the current priorities, to frame the digest and to check freshness.

---

## Step 0 — Locate config
Find `factory/` at the repo root. Need at least `communication.md` (where to post) and `intake.md` (the tracker). If either is missing: in an interactive run, route to `/factory-onboard`; in a cron run, log the missing file and stop. Read all present config files in full.

## Step 1 — Set the window
Default look-back is **the last 24 hours** (or since the previous digest, if you can find it — see Step 4). `communication.md`/`priority.md` may declare a different default. On a Monday or after a gap, widen to cover the missed days so nothing falls through.

## Step 2 — Survey activity across the org's systems
Only the systems the `factory/` files name — do not assume infrastructure. Typical sources:
- **Code:** recent commits / merged PRs / diffs in the repos from `codebases.md` (e.g. `git log --since`, the tracker's merge history). Summarize *what changed*, not every line.
- **Tracker:** issues opened, closed, moved, or commented in the window (via the `intake.md` CLI).
- **Conversation:** notable threads in the channels `communication.md` lists — decisions, blockers, questions raised. Skip chatter.

Attribute activity to people via `ownership.md` where useful. If a source is unreachable, note it and continue.

## Step 3 — Compose the digest
Concise and scannable — this is a pulse, not a report. Suggested shape (defer to any format in `communication.md`):
- **In flight** — what's actively being worked on, grouped by area/owner.
- **Landed** — what shipped / closed since last time.
- **New / raised** — issues opened or topics surfaced.
- **Watch** — blockers, decisions pending, anything at risk.

Lead with the most important movement. Keep it to bullets. **Never** include secrets, tokens, or internal hostnames/IPs.

## Step 4 — Priorities & continuity
- If `factory/priority.md` exists, frame the digest against it ("progress on this week's priorities: …") and note priorities with no movement.
- **Staleness check:** if `priority.md`'s `Last updated` is more than ~7 days old, append a brief heads-up — e.g. *"⚠︎ Priorities were last set on <date>; they may need a refresh (run `/factory-schedule-sync` or update `factory/priority.md`)."*
- For continuity, keep a lightweight record of each digest (e.g. `factory/.state/daily-digest.json` and/or a dated note under `factory/syncs/`) so the next run can say "still in progress" vs "new" and cover any gap since the last one.

## Step 5 — Post and record
Post the digest where `communication.md` says (a specific channel, a thread, an issue). Respect its reply/post policy — if the org wants digests only in one place, honor that. Record the run and the window covered, then exit. If genuinely nothing happened in the window, say so in one line rather than padding.
