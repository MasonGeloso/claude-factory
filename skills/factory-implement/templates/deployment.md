# Factory Deployment — <SERVICE NAME>

> How to set up a worktree, run the stack, and demo/hand off. Read by `/factory-implement` (the driver).

## Worktrees
- **Base dir:** <~/worktrees/>  (new worktree per task: `<base>/<task-id>/<repo>`)
- **Base branch / HEAD:** <main>
- **One worktree per:** <repo this task touches>

## Running the stack
- **Bring up:** <exact commands — e.g. `docker compose up -d api db`>
- **Nodes/services:** <api, ui, db, worker, …>
- **Ports:** <default ports + how to shift them for a second concurrent instance>
- **Concurrent instances:** <how to run alongside another active worktree without collisions>
- **Piggyback rules:** <which infra can be reused if untouched — e.g. "shared DB on :5432 OK if no schema change"; what must be per-worktree>
- **Provisioning CLI:** <only if one truly exists; otherwise "none — set up manually">

## Run mode
- <`full-local`  — stand up the stack locally and demo it>
- <`finish-in-worktree` — no good local env: build it, skip local demo, user commits & pushes to labs/remote>

## Demo mode
- **Mode:** <`video` | `terminal` | `none`>
  - `video` → web UI, use the `factory-demo-video` skill
  - `terminal` → CLI/stdout, use the `factory-demo-terminal` skill
  - `none` → skip; just report ready for handoff
- **Demo output dir:** <e.g. `demos/` in the worktree>
