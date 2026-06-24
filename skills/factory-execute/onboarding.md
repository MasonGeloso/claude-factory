# Factory Execute — Onboarding

Run this the first time `/factory-execute` is used in a repo (or whenever its config is incomplete). Goal: capture how *this* service is built and shipped so future runs are autonomous. You're filling three things:

1. `factory/codebases.md` — the repo(s) this service spans
2. `factory/deployment.md` — worktrees, running the stack, demo mode
3. the **Handoff & status** section of `factory/intake.md` (if intake didn't already capture it)

Ask in small batches (use AskUserQuestion where it fits). Inspect the repo to pre-fill answers before asking.

## 1. Codebases → `factory/codebases.md`
- Is this service **one repo or several**? (e.g. an API and a separate UI.)
- For each: name, local path, git remote, and its role. Which is **primary** (where the `factory/` dir lives)?
- How do the repos relate / talk to each other? Which combinations get checked out together for a typical change?

## 2. Deployment & run → `factory/deployment.md`
- **Worktree base dir** — where should new worktrees go? (default `~/worktrees/`)
- **Bringing the stack up** — exact commands. Docker Compose? A dev script? Which services/nodes.
- **Ports** — how are they assigned, and how to run a *second* instance alongside an existing stack without collisions. Which infra can be **piggybacked** (e.g. a shared DB) vs. must be stood up per-worktree.
- **Local env quality** — is there a good local environment at all? If not (some services have none), set the **run mode** to *finish-in-worktree-then-handoff*: build it, skip the local demo, let the user commit & push to the labs/remote environment.
- **Demo mode** — `video` (web UI → `demo-video` skill), `terminal` (CLI → `demo-terminal` skill), or `none`.
- Any provisioning CLI / dev-manager? Only document one if it really exists — otherwise leave it out (do not invent one).

Inspect first: read `docker-compose*.yml`, `Makefile`, `package.json` scripts, `.env.example`, README/`docs/` run instructions to draft this before asking.

## 3. Handoff & status → `factory/intake.md`
If intake already captured this, skip. Otherwise ask and write it into `intake.md`'s **Handoff & status** section:
- Is there an **in-progress** status to set when a task is picked up? (e.g. "In Progress", or none.)
- Once a task is finished and demoed, **where do updates go** and **what status means "ready for review"**? (e.g. move the GitHub Project item / Jira issue to "Ready for Review".)
- Should the demo be uploaded as a **comment** on the issue?
- Conventions for the running log: posting **assumptions** (@-mention the owner), decisions, and open questions as comments.
- **Handoff style:** auto-commit-and-push, or finish-and-wait-for-the-user-to-push.

## 4. Recon, write, confirm
Use the project's own commands to verify (list current worktrees, try the run commands if safe, read the compose port maps). Write the three files/sections concretely — real paths, real commands, real status names. Show the user and confirm before the first execution run.
