---
name: factory-implement
description: The factory ENTRY POINT / driver. Pick up a single task from the tracker (by id/url, or an intake item) and drive it end-to-end to ready-for-review — autonomously, with L7-engineer rigor. Reads every comment, then runs the pipeline (plan → re-research → execute(build) → recheck → stand up infra + verify live + iterate → demo → handoff), adjusting autonomy and iteration depth by the task's E-level. Reads all per-project rules from the working repo's `factory/` directory (worktrees, provisioning, demo, handoff) and onboards any missing config. Use when the user says "factory implement", "pick up this task", "execute this issue", "build this issue", or points at a tracker issue to take to done.
---

# Factory — Implement (the driver / entry point)

*Pick up one task. Drive it all the way to ready-for-review. Be surgical. You have all the time you need.*

This is the **entry point** of the factory. [`factory-intake`](../factory-intake/SKILL.md) fills the
backlog; **factory-implement** takes one item out and **drives it to completion** by orchestrating the
other factory skills, following the per-project rules in the working repo's `factory/` directory.

It is normally invoked alongside Claude Code's `/goal` so the objective stays pinned:
```
/goal /factory-implement <issue id | url | intake item>
```

> **This skill is codebase-agnostic.** It hardcodes nothing about any specific repo — *every*
> project-specific decision (does this repo use worktrees? is there a provisioning/dev-manager tool?
> how is infra booted, paused, torn down? which env files to copy? demo mode? handoff/status?) is
> read from the **working repo's `factory/` directory** at run time. If the `factory/` docs say to do
> something, do it that way; never assume or invent infrastructure.

---

## The skills this driver runs — invoke each BY NAME with the Skill tool

These are already-installed **user skills**. The normal way to run one is the **Skill tool with its name** — you don't need the path to invoke it. But the exact file path is given below so you can `Read` it directly if you ever need to (e.g. to inspect or debug it). Do not go searching the filesystem for them — they're listed here.

| Pipeline phase | Skill name (invoke this) | Path (read if needed) |
|---|---|---|
| Plan | `factory-plan` | `~/.claude/skills/factory-plan/SKILL.md` |
| Re-research | `factory-reresearch` | `~/.claude/skills/factory-reresearch/SKILL.md` |
| Execute (build the plan) | `factory-execute` | `~/.claude/skills/factory-execute/SKILL.md` |
| Recheck | `factory-recheck` | `~/.claude/skills/factory-recheck/SKILL.md` |
| Demo (web UI) | `factory-demo-video` | `~/.claude/skills/factory-demo-video/SKILL.md` |
| Demo (CLI) | `factory-demo-terminal` | `~/.claude/skills/factory-demo-terminal/SKILL.md` |

The factory skills all live under `~/.claude/skills/<name>/` (some, like `factory-demo-terminal`, have an `assets/` or `references/` subdir alongside `SKILL.md`). The suite is self-contained — every skill it calls is a `factory-*` skill. (The web-UI demo still relies on the external `playwright-cli` skill/tool for browser automation; that's a tool dependency, not part of the factory pipeline.)

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

1. Locate `factory/` at the repo root (`git rev-parse --show-toplevel`). If it does not exist, stop and tell the user to run `/factory-intake` first — the driver has no rules to follow without it.
2. Read `factory/intake.md` (tracker + CLI + handoff/status) and `factory/ownership.md`.
3. Check for the **execution config** this driver needs:
   - `factory/codebases.md` — the repo(s) this service spans and where they live.
   - `factory/deployment.md` — worktree base dir, how to run/demo the stack, and the demo mode. **Also check for `factory/dev-manager.md`** — if the repo has one, it is the canonical provisioning guide (worktrees, env copy, boot/pause/teardown) and overrides the manual instructions in `deployment.md`.
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

## Step 2 — Isolated worktree (only if the repo's `factory/` docs call for one)

Per `factory/codebases.md` and the repo's provisioning doc (`factory/dev-manager.md` if present, else `factory/deployment.md`):

1. If the repo works in worktrees, create a **fresh git worktree** off the configured HEAD for each codebase the task requires, under the configured base dir. **Never work directly on the user's main checkout.** Follow the doc's exact recipe (branch name, base dir).
2. **Copy whatever gitignored env/secret/setup files the repo's `factory/` docs say the stack needs** into the worktree (a fresh checkout won't have them), plus any per-worktree install step those docs list. The docs name the exact files and steps — don't assume; without them nothing authenticates.
3. Multi-repo: if the service spans repos, check out the ones this task touches; stay aware of the others' existence and location even if untouched.

> Infra (the running stack) is **not** booted here — that happens in Step 4, after the build and recheck, so you don't burn resources while planning/building. (If a particular task genuinely needs the stack up *during* the build to make progress, bring it up early per the same doc — but the default is to defer it.)

---

## Step 3 — Pipeline: plan → re-research → execute → recheck

**This skill is the driver. Each phase below is a separate skill, and you MUST run it by calling the Skill tool with that skill's name — do not do the work inline from memory.** Invoking the skill pulls in its full instructions; follow them, let it finish, then move to the next phase. Running the work yourself instead of invoking the skill is the main failure mode of the factory — do not do it.

Set a todo list with these phases so progress is visible: Plan → Re-research → Execute → Recheck → Stand-up & verify → Demo → Handoff. Then run them in order. Loop backward freely — recheck (or live verification) can send you back to plan.

1. **Plan** — call the Skill tool: `factory-plan`. (Research/diagnose, then write the plan to a markdown file in `./tasks` inside the worktree.) Do not write any production code in this phase.
2. **Re-research** — call the Skill tool: `factory-reresearch`. Run it the number of rounds the E-level calls for (E3:1, E2:2, E1:3–4+).
3. **Execute (build the plan)** — call the Skill tool: `factory-execute`. It takes the heavily-researched plan and builds it: granular todo list, one item at a time, verify as you go, don't stop until 100% done.
4. **Recheck** — call the Skill tool: `factory-recheck`. If anything is wrong, fix it or go back to plan/re-research. Repeat until genuinely confident — not until you're tired.

Gate: do not proceed to Execute until Plan **and** Re-research have actually been run (the plan file exists). Do not proceed to Stand-up/Demo/Handoff until Recheck passes.

---

## Step 4 — Stand up the stack and verify live (iterate until it actually works)

Recheck is a read-only review; **now bring up the stack and run the change against it** to confirm it
genuinely works end to end. Provision the stack **exactly as the repo's `factory/` docs say**
(`factory/dev-manager.md` if present — use its provisioning tool/CLI and only the **minimal** services
the task needs; else `factory/deployment.md`). Adding seed data your feature needs is fine if the docs
allow it.

Then exercise the feature the way the demo will — through the real running app — and **iterate**:
change → apply it the way the docs say (reload/rebuild) → re-check. **Stay in this loop until the
feature fully works and every paper-cut is gone.** If something is fundamentally wrong, it is never too
late to go back to Plan/Re-research — reaching this step is not permission to ship something
half-working. Only move on once you've seen it work with your own eyes on the running stack.

---

## Step 5 — Demo (per the repo's `factory/` demo config)

Record against **the stack you just stood up** — use whatever URLs/ports the repo's provisioning docs
(or the provisioning tool's own output) report, not a hardcoded address. Default: **always film a
demo** unless the task explicitly says not to. Call the Skill tool for the configured demo mode:
- **`video`** → call the Skill tool: `factory-demo-video` (web UI). Output into the worktree's demo dir.
- **`terminal`** → call the Skill tool: `factory-demo-terminal` (CLI / stdout).
- **`none`** → skip (e.g. a service with no local dev env): finish the code in the worktree and report ready for handoff so the user can push to the remote environment.

Pull the demo's story from the task itself; don't re-interview the user. If recording the demo surfaces something off, **go back and fix it** — the demo is a real check, not a formality.

---

## Step 6 — Handoff (per the Handoff & status config in `intake.md`)

This is a **mandatory phase, not an optional epilogue.** Once Recheck passes and the change is verified live, you MUST do all of it — and verify each action actually took effect (re-read the issue / re-query the status; don't assume the command worked):

1. Commit in the worktree (on the task branch). Push if the project's handoff style is auto-push (skip only if it's explicitly "wait for the user to push").
2. Open a **pull request** from the task branch if that's the project's handoff style (per `intake.md` / the provisioning doc), and link it on the issue.
3. Move the tracker status to the configured **ready-for-review** state — then confirm it actually changed.
4. **Post the demo as a comment** on the issue ("here's it working"), per the project's handoff config (the config says exactly how — link/attach). If demo mode is `none`, say so instead. **Do not end the run without doing this.**
5. **Post the re-provision one-liner** (if the provisioning doc documents one) so the owner can spin the exact stack back up and poke at it themselves — the demo video is not the only review.
6. Post a **concise log** comment: key decisions, assumptions made, open questions.
7. **End the run by leaving the stack the way the repo's `factory/` docs say to** — if they document a non-destructive pause, use it (free the box's resources while keeping containers, data, and the worktree intact so the owner can resume in seconds). **Do not tear the stack down, delete the worktree, or remove any data volume at handoff** — that cleanup happens only after the owner has reviewed and said so. If the docs don't document a pause, leave a clear note of what is left running.

## Definition of done — DO NOT report the task finished until ALL are true

Before you say "done" / "ready" / hand back to the user, every box must be checked. If any is unchecked, you are not done — go do it.

- [ ] Plan + re-research written (plan file exists)
- [ ] Built (factory-execute) and Recheck verdict is **PASS**
- [ ] **Verified live on the running stack** (Step 4) — seen working with your own eyes, not just code-reviewed
- [ ] Demo recorded **and verified** (you looked at it), or demo mode is `none`
- [ ] PR opened (if that's the project's handoff style)
- [ ] Tracker status moved to ready-for-review (confirmed)
- [ ] Demo posted as an issue comment (or stated `none`)
- [ ] Re-provision one-liner posted (if the provisioning doc documents one)
- [ ] Running-log comment posted (decisions / assumptions / questions)
- [ ] Stack left per the repo's docs (**paused, not destroyed**); worktree + data volumes intact for review

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
- **Codebase-agnostic:** read worktree / provisioning / demo / handoff conventions from the working repo's `factory/` docs — never hardcode them here.
