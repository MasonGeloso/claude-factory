# Daily Activity Digest (`daily-digest`)

A cron-style Factory agent that runs once a day. It surveys what actually happened
across the org's systems over the last day (or two), and posts a short,
bullet-point TLDR of what's being worked on — so the team gets a passive, reliable
pulse without anyone assembling it by hand.

## What it does each run

1. Reads `factory/communication.md` (where to post + what channels count) and
   `factory/intake.md` (the tracker + CLI). Reads `factory/priority.md` if present.
2. Surveys recent activity across whatever systems the org uses — e.g. for B3:
   git diffs/commits, GitHub issues opened/closed/updated, Discord conversation;
   for MGI: GitHub + Slack; for a Jira shop: Jira + its channels.
3. Optionally looks back over the last several days of its own digests for context
   (so it can say "still in progress" vs "new").
4. Writes a concise digest and posts it where `communication.md` says.
5. If `priority.md` exists but looks stale (not updated in ~a week), adds a gentle
   "priorities may need a refresh" heads-up.

The scheduled command is trivial and identical everywhere — it just tells Claude
Code to run `factory-daily-digest` (see `prompt.md`). All per-org behavior comes
from the target repo's `factory/` directory.

## Install

```bash
factory agents install daily-digest /path/to/repo        # default: once a day
factory agents install daily-digest /path/to/repo --interval 720   # twice a day
```

## Requirements

- `factory/` onboarded (`/factory-onboard`), including `communication.md` + `intake.md`.
- Claude Code on `PATH`; whatever the systems need to read them (tokens in `.env`).
