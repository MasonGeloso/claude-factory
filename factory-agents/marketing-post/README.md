# Marketing Post Dispatcher (`marketing-post`)

A cron-style Factory agent. Every hour it wakes up, checks the project's own posting timetable, and
fires whatever content type(s) are due — the one generic engine behind the whole marketing pillar,
replacing what would otherwise be a bespoke script per content type.

## What it does each run

1. Reads `factory/marketing/schedule.md` (the timetable), `content-types.md` (how to build each
   content type and its autonomy mode), and `platforms.md` (mechanics + the mandatory account-switch
   check for each platform).
2. Evaluates every scheduled row's gate against the current time in the project's own configured
   timezone — a tick can fire zero, one, or several content types.
3. For each content type that fires: verifies the right account is active, acquires a lock scoped to
   that (platform, account) pair so two lanes never fight over the same composer, builds the content,
   runs a de-slop pass if configured, and either publishes it (content types with standing
   `autonomous-publish` authority) or saves it as a draft and stops (`draft-only` content types).
4. Records the outcome to a canonical ledger under `factory/marketing/.state/` for dedup/cap math on
   future ticks.

The scheduled command is intentionally trivial and identical on every machine — it just tells Claude
Code to run the `factory-marketing-post` skill (see `prompt.md`), **with Chrome access** (this agent
sets `needs_chrome: true` in `agent.json`, since every platform this suite supports is driven through
the owner's logged-in browser, never headless automation). All the per-project behavior — which
platforms, which content types, the timetable, publish authority per content type — comes from the
repo's `factory/marketing/` directory.

## Install

```bash
factory agents install marketing-post /path/to/repo
```

If `factory/marketing/platforms.md` (or `content-types.md` / `schedule.md`) doesn't exist yet, the
installer launches an interactive Claude Code session running `factory-marketing-onboard` to build
them — with you, not just from a form — then schedules the agent.

## Requirements

- `factory/` already onboarded in the target repo, and the marketing pillar specifically (run
  `/factory-marketing-onboard` once, or let install do it interactively).
- Claude Code on `PATH`, with Claude-in-Chrome connected and logged into every account this project's
  `platforms.md` names.
- This is genuinely optional — a repo with no marketing/content-posting need never runs this
  installer and nothing about this pillar exists on that repo.
