---
name: factory-schedule-sync
description: 'Build a high-leverage agenda for an alignment/sync meeting. Looks at recent changes, the backlog, and issues that lack context or alignment, cross-references who''s attending against ownership, and proposes a discussion list aimed at decisions and priorities — not status theater. Collaborative: you refine the agenda together, and refining it surfaces context worth writing back to issues. Reads per-project rules from `factory/`. Use when the user runs /factory-schedule-sync, says "prep for the sync", "build the meeting agenda", or "what should we talk about".'
---

# Factory — Schedule Sync (agenda builder)

*Walk into the sync knowing exactly what needs deciding — and leave with everyone aligned. Maximize the meeting.*

This is **not** a fire-and-forget skill. It's a **working session**: you propose an agenda, the user reacts, you refine — and the act of refining exposes real context ("actually Igor isn't on that, it's mine") that should be written back to the tracker. The goal is to spend the meeting on **decisions and alignment**, not reading status aloud.

It reads:
- `factory/meetings.md` — the sync's cadence, attendees, goal, length, and agenda format.
- `factory/ownership.md` — who owns what, so the agenda is built around the people in the room.
- `factory/priority.md` — the current priorities, to drive "what matters most this week".
- `factory/intake.md` — the tracker + CLI, to read the backlog and recent activity.
- `factory/syncs/` — past agendas/recaps, for continuity.

If any needed file is missing, route to `/factory-onboard` first.

---

## Step 1 — Get the brief
Ask (or take from the invocation): **which sync** is this, **who's attending**, **when/how long**, and any **focus** the user already has in mind. Default assumption: it's an alignment meeting whose job is to make decisions and set priorities. Match it to a row in `meetings.md` if it's a recurring one.

## Step 2 — Gather the raw material
Pull, via the `intake.md` CLI and the repos in `codebases.md`:
- **Recent changes** — what moved since the last sync (merged work, closed/opened issues, notable threads). Reuse the last `factory/syncs/` recap as the "since" marker.
- **The backlog** — open issues/epics, especially ones tagged high priority.
- **Under-specified work** — issues that are **poorly aligned or low-context**: vague titles, no acceptance criteria, no owner, stale, or big-but-unresearched (spike candidates). These are prime agenda material — the meeting is where they get context.
- **Priorities** — read `priority.md`; note anything with no recent movement.

## Step 3 — The attendee lens (the important part)
For **each attendee**, use `ownership.md` (and any per-person notes in `meetings.md`) to ask: **"what do I need from this person in this meeting?"**
- Pull the status of open work in **their** area of ownership.
- Surface **decisions they own** or blockers only they can clear.
- Flag issues currently assigned to them that might actually belong elsewhere (a realignment prompt).

This is where hidden context comes out. When the user corrects an assumption while reviewing ("that one's mine, not Igor's"), capture it — see Step 5.

## Step 4 — Draft the agenda, ranked by leverage
Propose an agenda ordered to **maximize the meeting**. Favor, in order:
1. **Decisions needed** — practical implementation questions on planned/backlogged work, forks in the road.
2. **Alignment gaps** — issues lacking context or with fuzzy ownership/scope.
3. **Priority-setting** — what are the top things to get done today / this week / this month.
4. **Blockers** — anything stuck on someone in the room.
Status-only items go last or get cut. Time-box against the meeting length from `meetings.md`.

## Step 5 — Refine together, and write context back
Present the draft and **discuss it** with the user. As they react, you'll learn things — reassignments, clarifications, decisions already made. With the user's ok, write that context back through the tracker CLI **as you go**:
- add clarifying comments to under-specified issues,
- fix owners (only to people in `ownership.md`),
- note the decisions/questions the meeting needs to resolve as issue comments.

Honor the same hard rules as intake: **no secrets anywhere**, short specific titles, never invent an assignee.

## Step 6 — Save and share
Write the final agenda to `factory/syncs/YYYY-MM-DD-<sync>.md` (this becomes the "since" marker and the thing `factory-sync-recap` reconciles against). If `communication.md`/`meetings.md` say to post it (a channel, a doc), do so. Remind the user to run **`/factory-sync-recap`** with the transcript afterward so decisions land back on the board and `priority.md` gets refreshed.
