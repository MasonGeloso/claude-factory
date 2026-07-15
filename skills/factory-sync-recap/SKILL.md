---
name: factory-sync-recap
description: Turn a completed alignment-meeting transcript into board updates and refreshed priorities. Matches the transcript to the agenda it came from, cross-correlates what was decided to the real issues, updates them (context comments, owners, status, new/closed items), and captures the meeting's priorities into `factory/priority.md`. The post-meeting counterpart to factory-schedule-sync; reuses factory-intake's rules. Use when the user runs /factory-sync-recap, drops a meeting transcript, or says "recap the sync", "process the meeting".
---

# Factory — Sync Recap (post-meeting reconcile)

*The meeting happened. Now make the board and the priorities reflect what was decided.*

This is the back half of the sync loop: [`factory-schedule-sync`](../factory-schedule-sync/SKILL.md) builds the agenda; **factory-sync-recap** takes the transcript afterward and lands every decision where it belongs. It's a focused cousin of [`factory-intake`](../factory-intake/SKILL.md) — it reuses intake's classification, dedupe, and no-secrets rules — but its input is a **meeting about existing work**, so it leans toward **updating** issues and setting priorities rather than creating a fresh backlog.

It reads: `factory/intake.md` (tracker + CLI), `factory/ownership.md` (people), `factory/meetings.md` (decision/priority conventions), `factory/communication.md` (where to post, if anywhere), and `factory/syncs/` (the agenda this transcript corresponds to). Missing a needed file → route to `/factory-onboard`.

---

## Step 1 — Get the transcript and identify the meeting
Take the pasted transcript. Identify **which sync** it is and match it to its agenda in `factory/syncs/` (by date / attendees / topics). The agenda gives you the issue links and the questions the meeting was meant to answer — use it as the checklist. If there's no matching agenda (an unplanned meeting), proceed anyway and derive the items from the transcript.

## Step 2 — Extract decisions and action items
These are real conversations — **ignore filler, tangents, and disfluencies**; pull out only what changes state:
- **Decisions** made (and the reasoning worth keeping).
- **Reassignments** — who now owns what.
- **New work** surfaced that isn't tracked yet.
- **Completed / dropped** work.
- **Priorities** — what the group said matters most (today / this week / this month).
- **Open questions** deferred to a follow-up.

Cross-correlate each against the agenda's issue links so you know exactly which issue each decision touches.

## Step 3 — Reconcile the board
Walk the checklist and make the tracker match, via the `intake.md` CLI:
- **Existing issue discussed** → add a concise comment capturing the decision/context; update owner (only to someone in `ownership.md`), labels, or status as decided.
- **New work** → create the issue, classified per `factory-intake`'s scheme; dedupe against the board (obvious dup → skip + note; near-dup → create + flag for the user).
- **Finished / cancelled** → close or move to the done state per `intake.md`.
- **Open question** → record it on the relevant issue (or a follow-up item) so it isn't lost.

Same hard rules as intake, non-negotiable: **never** put secrets/tokens/credentials/internal hosts into any issue or comment; short specific titles; never invent an assignee.

## Step 4 — Refresh priorities
This is a first-class output. From what the meeting decided, **update `factory/priority.md`**:
- Rewrite the **Now / Soon / Later** sections to match, linking real issues/epics.
- Record explicit **non-priorities** the group named.
- Stamp `Last updated: <today>` and who set them — this is what clears the daily digest's staleness flag.
If priorities weren't explicitly discussed, ask the user for a quick read on the top 2–3 things before writing.

## Step 5 — Write the recap and report
Append a recap to the agenda file (or a new `factory/syncs/YYYY-MM-DD-<sync>-recap.md`): decisions, issue changes (with links/IDs), new/closed items, priorities set, and open questions. If `communication.md`/`meetings.md` say to post a summary (a channel, a doc), do so. Then report to the user: what was updated, what was created (with near-dup flags), and the new priority list — so they can eyeball it before it's considered final.
