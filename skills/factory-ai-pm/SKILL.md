---
name: factory-ai-pm
description: Run as an automated AI Product Manager. On each (usually scheduled) run, read the org's communication channels since the last check, reconcile the work tracker against the conversation — create, close, assign, and comment on issues — then save a new last-read timestamp. Reads per-project rules from the repo's `factory/` directory (communication medium from `communication.md`, tracker from `intake.md`); onboards `communication.md` if it is missing. Use when the user runs /factory-ai-pm, says "run the AI PM", or the ai-pm cron agent invokes it.
---

# Factory — AI Product Manager

*Every few minutes: read what the team said, and make the board reflect it.*

This skill is normally invoked by the **`ai-pm` cron agent** (see `agents/ai-pm/` in the factory repo), running non-interactively via `claude -p "..." --dangerously-skip-permissions`. It can also be run by hand. Assume **no human is watching** unless one clearly is.

It uses the same primitives as [`factory-intake`](../factory-intake/SKILL.md) — the tracker, its CLI, the classification scheme, the no-secrets rule — but its trigger is a **conversation stream** (Slack, Discord, …) rather than a pasted transcript, and it runs on a loop.

**Every org is different**, so nothing is hard-coded. Two files in the repo's `factory/` directory drive it:
- `factory/communication.md` — how this org communicates: medium, how to authenticate, which channels to read, and whether you may reply.
- `factory/intake.md` — the tracker, its CLI, the classification mapping, and handoff/status rules.

---

## Step 0 — Locate config (always first)

Find `factory/` at the repo root (`./factory`, else `git rev-parse --show-toplevel`). Expected once onboarded:

```
factory/
  intake.md            # tracker + CLI + classification + handoff (from factory-intake)
  ownership.md         # team members + areas + tracker handles
  communication.md     # THIS skill's config: medium, auth, channels, reply policy
  .state/ai-pm.json    # last-read timestamp + run log (gitignored; created on first run)
```

Then branch:

- **`factory/` missing entirely** → this repo was never onboarded. Log clearly that `/factory-intake` must be run first, and stop. Do not guess a tracker.
- **`factory/intake.md` exists but `factory/communication.md` is missing** →
  - If a **human is present** (interactive run): run **`/factory-onboard`** (which back-fills just the missing `communication.md` via [`factory-communication-setup`](../factory-communication-setup/SKILL.md)), then continue.
  - If **no human** (cron/`-p` run): stop and log: *"factory/communication.md missing — run `factory agents install ai-pm` or `/factory-onboard` interactively to set it up."* Do not attempt to read channels without it.
- **Both exist** → read `intake.md`, `ownership.md`, and `communication.md` in full, then run the loop below.

---

## Step 1 — Load state (the last-read watermark)

Read `factory/.state/ai-pm.json`. Shape:

```json
{ "last_read": "2026-07-09T14:32:05Z", "runs": [ { "at": "...", "messages": 12, "actions": ["created #841", "closed #830"] } ] }
```

- **First run ever** (no file / no `last_read`): do **not** ingest all history. Use the bounded look-back window `communication.md` declares (default: the last 24 hours). Record it and move on.
- Otherwise start from `last_read`.

Never let a crash advance the watermark — only write it after a run completes (Step 5).

## Step 2 — Read new messages

Following the **Access & read protocol** in `communication.md`:
- Authenticate exactly as documented (e.g. a bot token in the repo `.env` — read it from there; never hard-code or echo it).
- Pull messages **since `last_read`** across **every** channel `communication.md` lists. Do not silently skip channels; if one is unreachable, note it and continue.
- Capture enough to act on: author, channel, timestamp, text, and thread context. Resolve author identities to `ownership.md` handles where you can.

## Step 3 — Read the board

Using the tracker CLI from `intake.md`, load current open issues (and recently closed ones, enough to avoid duplicating or re-opening). You are about to reconcile the conversation against this state.

## Step 4 — Reconcile conversation → tracker

For the new messages, decide what actually changed and make the board match. Typical actions, all through the tracker CLI:

- **New work surfaced** → create an issue. Classify it (T/E or the project's scheme) and dedupe against the board exactly as `factory-intake` does — obvious duplicate: skip and note it; near-duplicate: create and flag it. Short pointy title; TLDR-first body; owner only if known from `ownership.md`.
- **Work reported done / merged** → close (or move to the tracker's done state per `intake.md`).
- **Ownership discussed** → assign/reassign, but only to people in `ownership.md`.
- **Status / decisions / blockers discussed** → post a concise comment on the relevant issue so the board carries the context.
- **Ambiguous or risky** → do **not** guess. Follow the reply policy: if replies are allowed, ask a brief clarifying question in-channel; otherwise leave it for a human and note it in the run log.

**Hard rules (inherited from intake, non-negotiable):**
- Never put secrets, tokens, credentials, or internal hostnames/IPs into an issue, comment, or message.
- Titles short and specific; elaboration goes in the body.
- Assign only real people from `ownership.md`; never invent an assignee.
- Be conservative when unattended: prefer creating/commenting over closing or reassigning when unsure. It is cheaper to leave a note than to wrongly close someone's issue.

## Step 5 — Reply, record, and advance the watermark

- **Reply** only if `communication.md` says you may, and only where it says (e.g. a specific channel or a thread reply). Respect any "read-only" setting — many orgs want the AI PM to observe silently and only touch the tracker.
- Append a run entry to `factory/.state/ai-pm.json` (timestamp, message count, list of actions taken) and set `last_read` to the newest message timestamp you processed (or run time if none).
- Emit a short summary to stdout/log: N messages read, issues created/closed/assigned, and anything skipped or flagged for a human.

---

## Notes for unattended runs

- Runs overlap poorly. Keep each run short; if there is genuinely nothing new since `last_read`, do almost nothing and exit.
- If a step fails (auth, tracker down), log it and exit **without** advancing `last_read`, so the next run retries the same window.
- This skill only ever touches the tracker and (optionally) posts messages — it never edits code, branches, or infra.
