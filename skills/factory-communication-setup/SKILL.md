---
name: factory-communication-setup
description: Onboard how an org communicates so Factory agents (the AI PM and future ones) can read from and — where permitted — write to its channels. Interviews the user about the medium (Slack, Discord, …), authentication, which channels to read, and reply policy, then writes `factory/communication.md`. Use when the user runs /factory-communication-setup, when `factory/communication.md` is missing, or when installing a Factory agent that needs it.
---

# Factory — Communication Setup

*Teach Factory how this org talks, so its agents can listen (and, if allowed, speak).*

Every org has two things: a **work management system** (already captured in `factory/intake.md`) and a **way of communicating** — Slack, Discord, Teams, email, something else. This skill captures the second one into `factory/communication.md`, the file that the [`factory-ai-pm`](../factory-ai-pm/SKILL.md) agent (and future communication-driven agents) read to know how to reach the conversation.

This mirrors the onboarding pattern used by `factory-intake` and `factory-implement`: if the file doesn't exist, we don't guess — we set it up together, once.

---

## 1. Set expectations

Confirm there's a `factory/` directory here (if not, tell the user to run `/factory-intake` first — communication config sits alongside the tracker config). Explain you'll ask a handful of questions and then write `factory/communication.md`.

## 2. Interview the user

Ask in small batches (use the AskUserQuestion tool where it fits). Cover:

**Medium**
- What's the primary communication medium? (Slack, Discord, Microsoft Teams, email, other.) More than one? Which is primary.

**Access & authentication**
- How does an agent connect — official API, a bot/app, a CLI, webhooks?
- What credential is needed and **where does it live**? (Strongly prefer a named env var in the repo's `.env` — e.g. `DISCORD_BOT_TOKEN`, `SLACK_BOT_TOKEN`. Capture the *variable name*, never the value.)
- Any workspace / guild / team / org IDs, base URLs, or API versions needed to make calls non-interactively.
- Bot/app scopes or permissions required (e.g. `channels:history`, `chat:write`, Discord `Read Message History`).

**Channels to read**
- Which channels/servers should the agent read? List them by name and ID.
- Are they grouped by work-group / team / project? Note the grouping so the agent can attribute conversations to the right area (ties into `ownership.md`).
- Explicit instruction to **read every listed channel** each run (don't sample), and any channels to **never** read (private/HR/leadership).

**Read protocol**
- How to fetch messages **since a timestamp** (the API/endpoint, pagination, threads). How timestamps are expressed (ISO, Slack `ts`, Discord snowflake).
- The **first-run look-back window** (default: 24h) — how far back to read on the very first run before a watermark exists.

**Reply / write policy**
- May the agent **post messages back**, or is it **read-only** (observe silently, only update the tracker)? Read-only is a common and safe default.
- If it may reply: **where** (a specific channel, a thread reply, a DM to an owner) and **when** (e.g. only to ask a clarifying question, only to confirm an action taken). Tone/format conventions.
- Anything it must **never** do (announce in public channels, @-here/@-everyone, DM people, etc.).

**Scheduled posts (recurring reports)**

Distinct from the reply policy above: these are standing posts the org has asked
for, so they're allowed even when the agent is otherwise read-only. Ask per report
the org wants — today that's the **daily digest** (`daily-digest`) and the
**weekly tech-tree board** (`weekly-report`):

- Does the org want this report at all? If not, say so explicitly — a blank destination means *don't post*, and it should be a decision rather than an omission.
- **Where** does it go (channel + ID)? Same place as conversation, or a dedicated #reports-style channel?
- **When** — which day and roughly what time? (This is documentation; the actual schedule is the install-time `--interval`. Keep the two in step.)
- **Format** — for the weekly board, the artifact is a **PNG image**. Get the exact upload call: attaching a file is a different API call from posting text (Slack `files.upload_v2`, Discord multipart `files[0]`, …). A destination with no upload mechanism is a report that can't be delivered.
- **Threading** — a fresh message each time, a reply into a standing thread, or replace/pin the previous one?
- Anything that must **never** appear in a scheduled post (@-channel, customer names, revenue figures).

**Restrictions**
- Rate limits to respect, quiet hours, privacy constraints, or compliance notes.

## 3. Recon pass (if credentials are available now)

If the token/credential is present and it's safe, use the real API to pre-fill:
- List the channels the bot can see and their IDs, so `communication.md` names them exactly.
- Confirm the auth works and the required scopes are present.
Fold what you learn into the file. Never print the credential itself.

## 4. Write the file

Create `factory/communication.md` from [templates/communication.md](templates/communication.md), filled concretely — real env-var names, real channel IDs, the exact API calls to read-since-timestamp, and an unambiguous reply policy. Also ensure a `factory/.gitignore` ignores `.state/` (where the AI PM keeps its watermark).

## 5. Confirm

Show the user the written `communication.md`, confirm it matches how they work and that the reply policy is exactly what they want, then hand back. If this was triggered mid-install of a Factory agent, the installer resumes and schedules the agent once the file exists.
