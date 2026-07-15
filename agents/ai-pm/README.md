# AI Product Manager (`ai-pm`)

A cron-style Factory agent. Every few minutes it wakes up, reads the org's
communication channels since the last time it checked, looks at the work
tracker, and reconciles the two — opening, closing, assigning, and commenting
on issues based on what people are actually discussing.

## What it does each run

1. Reads `factory/communication.md` (how this org communicates — medium, auth,
   channels, reply policy) and `factory/intake.md` (the tracker + its CLI).
2. Loads the last-read timestamp from `factory/.state/ai-pm.json`.
3. Pulls new messages across the configured channels since that timestamp.
4. Reconciles the board: creates issues for new work, closes finished ones,
   reassigns, and posts short status comments — following the same
   classification and no-secrets rules as `factory-intake`.
5. Saves a new last-read timestamp.

The scheduled command is intentionally trivial and identical on every machine —
it just tells Claude Code to run the `factory-ai-pm` skill (see `prompt.md`).
All the per-org behavior comes from the repo's `factory/` directory.

## Install

```bash
factory agents install ai-pm /path/to/repo
```

If `factory/communication.md` does not exist yet, the installer launches an
interactive Claude Code session running `factory-communication-setup` to create
it, then schedules the agent.

## Requirements

- `factory/` already onboarded in the target repo (run `/factory-intake` once).
- Claude Code on `PATH`.
- Whatever the communication medium needs (e.g. a bot token in the repo `.env`).
