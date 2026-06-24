---
name: factory-execute
description: Pick up a single task from the tracker (or an intake item) and drive it end-to-end to ready-for-review — autonomously, with L7-engineer rigor. Sets up an isolated git worktree, then runs the factory pipeline (plan → re-research → implement → recheck → demo → handoff), adjusting autonomy and iteration depth by the task's E-level. Reads per-project rules from the repo's `factory/` directory and onboards any missing config. Usually invoked next to /goal, e.g. `/goal /factory-execute <issue>`. Use when the user says "factory execute", "pick up this task", "execute this issue", "run the factory on <task>", or points at a tracker issue to build.
---

# Factory — Execute

*Pick up one task. Drive it all the way to ready-for-review. Be surgical. You have all the time you need.*

This is the execution counterpart to [`factory-intake`](../factory-intake/SKILL.md). Intake fills the backlog; **execute** takes one item out of it and builds it to completion in an isolated worktree, following the same per-project `factory/` rules.

It is normally invoked alongside Claude Code's `/goal` so the objective stays pinned:
```
/goal /factory-execute <issue id | url | intake item>
```

---

## The skills this orchestrator runs — invoke each BY NAME with the Skill tool

These are already-installed **user skills**. The normal way to run one is the **Skill tool with its name** — you don't need the path to invoke it. But the exact file path is given below so you can `Read` it directly if you ever need to (e.g. to inspect or debug it). Do not go searching the filesystem for them — they're listed here.

| Pipeline phase | Skill name (invoke this) | Path (read if needed) |
|---|---|---|
| Plan | `factory-plan` | `~/.claude/skills/factory-plan/SKILL.md` |
| Re-research | `factory-reresearch` | `~/.claude/skills/factory-reresearch/SKILL.md` |
| Implement | `factory-implement` | `~/.claude/skills/factory-implement/SKILL.md` |
| Recheck | `factory-recheck` | `~/.claude/skills/factory-recheck/SKILL.md` |
| Demo (web UI) | `factory-demo-video` | `~/.claude/skills/factory-demo-video/SKILL.md` |
| Demo (CLI) | `factory-demo-terminal` | `~/.claude/skills/factory-demo-terminal/SKILL.md` |

The factory skills all live under `~/.claude/skills/<name>/` (some, like `factory-demo-terminal`, have an `assets/` or `references/` subdir alongside `SKILL.md`). The suite is self-contained — every skill it calls is a `factory-*` skill. (The web-UI demo still relies on the external `playwright-cli` skill/tool for browser automation; that's a tool dependency, not part of the factory pipeline.)

The demo step uses `factory-demo-video` (web UI) or `factory-demo-terminal` (CLI). Which mode to use, and how to run the stack for it, comes from `factory/deployment.md`.

If you ever can't invoke one of these by name, stop and tell the user the skill is missing — do not improvise the work inline or fabricate a substitute.

---

## Mindset (read this first, every run)

You are operating as an **L7 engineer with extreme precision**. Internalize this for the whole run:

- **You have as much time as you need.** Nothing is rushing you. Do not optimize for wrapping up.
- **Do not be lazy.** Keep going. Keep iterating. If something is wrong, do not accept it — go back and fix it.
- **You are on your own.** Especially for E3 tasks, there is no one to fall back on mid-run. Finish it through and through.
- **It is never too late to go back.** If you get all the way to the demo and notice something is off, go back and replan. You are never obligated to stop at a checkpoint just because you reached it.
- **Surgical, not hasty.** Quality and correctness over speed. Verify everything; trust nothing blindly, including your own plan.
- **Evidence before code.** Always diagnose first — read the docs and how this system is meant to be observed, read the logs, reproduce locally, and **validate the report is even true** — before editing anything. The reported problem is a hypothesis to confirm, not a fact. Reading source is the last research step, not the first.
- **Done means handed off, not coded.** The finish line is the handoff — status moved, demo posted, log comment written (see "Definition of done"). Writing the code is the middle of the job, not the end. Keep the issue updated with concise comments the whole way through.

The point of saying all this: take the stress off. Thoroughness is the job.

---

## Step 0 — Config check (always first)

1. Locate `factory/` at the repo root (`git rev-parse --show-toplevel`). If it does not exist, stop and tell the user to run `/factory-intake` first — execution has no rules to follow without it.
2. Read `factory/intake.md` (tracker + CLI + handoff/status) and `factory/ownership.md`.
3. Check for the **execution config** this skill needs:
   - `factory/codebases.md` — the repo(s) this service spans and where they live.
   - `factory/deployment.md` — worktree base dir, how to bring up / run the stack, and the demo mode.
   - The **Handoff & status** section of `factory/intake.md` — where to post updates and what "ready for review" means.
4. If any of those are **missing or incomplete**, run **Onboarding** ([onboarding.md](onboarding.md)) to fill them with the user, then continue. Do not guess infrastructure or status conventions.

---

## Step 1 — Load the task

**Prime directive:** run this whole process and **satisfy every requirement in the task** — the full description *and* every comment. That is the bar; nothing less counts as done.

- Fetch the **full** task from the tracker using the CLI in `intake.md`: title, description, labels, linked issues, and **every single comment, read in its entirety**. This is mandatory and non-negotiable:
  - Read **every** comment from the first to the last — none skipped, none skimmed, none truncated. Comments routinely carry the real requirements, corrections, and decisions that supersede the original description.
  - Use a command that returns all comments in full (e.g. `gh issue view <num> --comments`, or `gh api` to page through them) — the default issue view truncates. If there are many comments, page until you have all of them.
  - Do not begin planning until you have actually read the complete thread end to end.
- **Read the originating intake run file** in `factory/intake/` (the dated file that produced this issue). It holds the T/E **classification** and the research/caveat bullets intake already captured — this is the most direct source of the route to take. If you were pointed at an intake item rather than an issue, start here.
- Recover the task's **classification**: its T-level and especially its **E-level** — from the intake run file, falling back to labels / the scheme in `intake.md`, mapped per [classification.md](../factory-intake/classification.md). The E-level sets your autonomy and iteration depth — see the table below.
- Restate the requirements to yourself. The issue is the source of truth, not your first interpretation of it.
- If the tracker has an **in-progress** status (per `intake.md` Handoff & status), move the item into it now so the board reflects that you've picked it up.

### E-level governs how this run behaves

| | E3 (hands-off) | E2 (middle) | E1 (complex) |
|---|---|---|---|
| Questions to user | **Never** (only if truly catastrophic) | Only if genuinely blocked | **Expected** — ask blocking design questions |
| Re-research rounds | 1 | 2 | 3–4+ until holes stop appearing |
| Review posture | push straight through, likely auto-mergeable | light, confirm no regressions | heavy, trace everything |

For E1/E2, ask blocking questions through your normal question tool (AskUserQuestion) **after** planning and re-research have surfaced the real design decisions — not before you understand the problem. For E3, do not ask; finish it.

---

## Step 2 — Isolated worktree + stack

Per `factory/codebases.md` and `factory/deployment.md`:

1. Create a **fresh git worktree** off `main` (or the configured HEAD) for each codebase the task requires, under the configured worktree base dir (default `~/worktrees/<task-id>/`). Never work directly on the user's main checkout.
2. Multi-repo: if the service spans repos (e.g. an API + a UI), check out the ones this task touches; stay aware of the others' existence and location even if untouched.
3. Bring the stack up per `deployment.md`:
   - **Be aware of other active worktrees/stacks.** Inspect what's already running.
   - **Pick free ports** for a new instance (understand the compose files / port mappings) rather than colliding with a running stack.
   - **Piggyback shared infra when safe** — e.g. "I'm not changing the schema, the DB that's already up is fine, reuse it" — instead of standing up redundant nodes.
   - If `deployment.md` says this service has **no good local env** (e.g. it's push-to-labs), don't force one — follow its run mode (finish in the worktree, skip the local demo, hand off for the user to push).
   - Do **not** invent a dev-manager CLI. Only use a provisioning CLI if `deployment.md` explicitly documents one.

---

## Step 3 — Pipeline

**This skill is an orchestrator. Each phase below is a separate skill, and you MUST run it by calling the Skill tool with that skill's name — do not do the work inline from memory.** Invoking the skill pulls in its full instructions; follow them, let it finish, then move to the next phase. Running the work yourself instead of invoking the skill is the main failure mode of this command — do not do it.

Before you start, set a todo list with these phases so progress is visible: Plan → Re-research → Implement → Recheck → Demo → Handoff. Then run them in order. Loop backward freely — recheck can send you back to plan.

1. **Plan** — call the Skill tool: `factory-plan`. (Research/diagnose, then write the plan to a markdown file in `./tasks` inside the worktree.) Do not write any production code in this phase.
2. **Re-research** — call the Skill tool: `factory-reresearch`. Run it the number of rounds the E-level calls for (E3:1, E2:2, E1:3–4+).
3. **Implement** — call the Skill tool: `factory-implement`. (Granular todo list, build one item at a time, verify as you go, don't stop until 100% done.)
4. **Recheck** — call the Skill tool: `factory-recheck`. If anything is wrong, fix it or go back to plan/re-research. Repeat until genuinely confident — not until you're tired.

Gate: do not proceed to Implement until Plan **and** Re-research have actually been run (the plan file exists). Do not proceed to Handoff until Recheck passes.

## Step 4 — Demo (per `deployment.md` demo mode)

Call the Skill tool for the configured demo mode:
- **`video`** → call the Skill tool: `factory-demo-video` (web UI). Output the `.webm` into the worktree's demo dir.
- **`terminal`** → call the Skill tool: `factory-demo-terminal` (CLI / stdout).
- **`none`** → skip (e.g. a service with no local dev environment): finish the code in the worktree and report ready for handoff so the user can commit and push to the labs/remote environment.

Pull the demo's story from the task itself; don't re-interview the user. If recording the demo surfaces something off, **go back and fix it** — the demo is a real check, not a formality.

## Step 5 — Handoff (per the Handoff & status config in `intake.md`)

This is a **mandatory phase, not an optional epilogue.** Once Recheck passes, you MUST do all of it — and verify each action actually took effect (re-read the issue / re-query the status; don't assume the command worked):

1. Commit in the worktree. Push if the project's handoff style is auto-push (skip only if it's explicitly "wait for the user to push").
2. Move the tracker status to the configured **ready-for-review** state — then confirm it actually changed.
3. **Post the demo as a comment** on the issue ("here's it working"), per the project's handoff config (the config says exactly how — link/attach). If demo mode is `none`, say so instead. **Do not end the run without doing this.**
4. Post a **concise log** comment: key decisions, assumptions made, open questions.

## Definition of done — DO NOT report the task finished until ALL are true

Before you say "done" / "ready" / hand back to the user, every box must be checked. If any is unchecked, you are not done — go do it.

- [ ] Plan + re-research written (plan file exists)
- [ ] Implemented and Recheck verdict is **PASS**
- [ ] Demo recorded **and verified** (you looked at it), or demo mode is `none`
- [ ] Tracker status moved to ready-for-review (confirmed)
- [ ] Demo posted as an issue comment (or stated `none`)
- [ ] Running-log comment posted (decisions / assumptions / questions)

If you catch yourself about to wrap up with any of these missing, stop and finish them first. "I built the code" is **not** the finish line — the handoff is.

---

## Keep the tracker as a live log (throughout, not just at the end) — REQUIRED

Keeping the work item updated with concise comments is a **general rule of this skill**, not a nicety. Short running log, not an essay. **At minimum** you must post:

1. **On pickup** — a brief "picking this up" comment when you start (alongside moving it to in-progress).
2. **Each assumption** — whenever you interpret an ambiguous requirement and choose a direction, post it and @-mention the issue **owner** (from `ownership.md`) so they can correct it.
3. **At handoff** — the concise summary log (see Definition of done).

Also log, as they happen: material **decisions** (and why), and any **questions / blockers** (for E1/E2, also ask the user directly). If you made no comments during a run, you did it wrong.

## Hard rules

- **Never** put secrets, tokens, credentials, or hard-coded sensitive values into code, commits, issues, comments, or demos.
- Work in the worktree, never the user's primary checkout. Base off the configured HEAD.
- Assign / @-mention only people listed in `ownership.md`.
- Don't fabricate demo output; don't stand up redundant infra you could piggyback on; don't invent tooling the config doesn't document.
