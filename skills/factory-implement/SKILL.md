---
name: factory-implement
description: The factory ENTRY POINT / driver. Pick up a single task from the tracker (by id/url, or an intake item) and drive it end-to-end to ready-for-review — autonomously, with L7-engineer rigor. Reads every comment, then runs the pipeline (plan → re-research → execute(build) → recheck → stand up infra + verify live → PR + code review → QA it like a real user → demo → handoff), adjusting autonomy and iteration depth by the task's E-level. Reads all per-project rules from the working repo's `factory/` directory (worktrees, provisioning, demo, handoff) and onboards any missing config. Use when the user says "factory implement", "pick up this task", "execute this issue", "build this issue", or points at a tracker issue to take to done.
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

Invoke each skill by its registered name (plugin installs may namespace it). The paths below are
examples for a user-skill install, not a guarantee: resolve sibling files from the actual loaded
skill directory when passing paths to an external CLI. Read that same installed version for the
whole run; do not mix a plugin copy with an older user copy.

| Pipeline phase | Skill name (invoke this) | Path (read if needed) |
|---|---|---|
| Plan | `factory-plan` | `~/.claude/skills/factory-plan/SKILL.md` |
| Re-research | `factory-reresearch` | `~/.claude/skills/factory-reresearch/SKILL.md` |
| Plan review (optional, pre-Execute gate) | `factory-plan-review` | `~/.claude/skills/factory-plan-review/SKILL.md` — see the exception note below, invocation differs |
| Execute (build the plan) | `factory-execute` | `~/.claude/skills/factory-execute/SKILL.md` |
| Recheck | `factory-recheck` | `~/.claude/skills/factory-recheck/SKILL.md` |
| Code review (optional, post-PR gate) | `factory-code-review` | `~/.claude/skills/factory-code-review/SKILL.md` — see the exception note below, invocation differs |
| **QA (always on, blocking)** | `factory-qa` | `~/.claude/skills/factory-qa/SKILL.md` — its Step 6 second opinion also shells out, see the note below |
| Demo (web UI) | `factory-demo-video` | `~/.claude/skills/factory-demo-video/SKILL.md` |
| Demo (CLI) | `factory-demo-terminal` | `~/.claude/skills/factory-demo-terminal/SKILL.md` |

User-installed factory skills live under `~/.claude/skills/<name>/`; plugin copies live under the plugin directory (some, like `factory-demo-terminal`, have an `assets/` or `references/` subdir alongside `SKILL.md`). The suite is self-contained — every skill it calls is a `factory-*` skill. (The web-UI demo still relies on the external `playwright-cli` skill/tool for browser automation; that's a tool dependency, not part of the factory pipeline.)

If invocation by name is unavailable, read the actual installed sibling `SKILL.md` and follow it
directly. If the file is missing too, report the missing dependency; do not fabricate its checks.

**Three exceptions** — the external-review steps. **`factory-plan-review`** (Step 3, pre-Execute),
**`factory-code-review`** (Step 5, post-PR) and **`factory-qa`'s Step 6 second opinion** (Step 6) are
invoked *differently* when the config names an external tool — you shell out to that tool (e.g.
`codex exec`) with a prompt pointing at the relevant `SKILL.md`'s **absolute path** (the plan file's
path plus the issue reference for plan-review; a PR URL for code-review; the PR + issue + the QA report
for the QA second opinion), since an external CLI agent can't resolve a Claude Code skill name. If no
external tool is configured (or the config file doesn't exist), run that review yourself in-context
instead — same review, just performed by you.

For every external gate, follow [review run handling](../factory-code-review/references/review-runs.md):
isolated output, owned process handle, successful exit, and a verdict tied to unchanged inputs.
Maintain its finding register across rounds; a repeated root problem changes the repair strategy,
not just the next line to patch.

Note the split: **`factory-qa` itself always runs in-context** (it has to drive a real browser and a
real stack); only its *final second-opinion step* shells out.

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
4. If any of those are **missing or incomplete**, run **`/factory-onboard`** — the single, partial-aware onboarding skill; it detects exactly which `factory/` files are missing (here: `codebases.md`, `deployment.md`, the handoff section of `intake.md`) and fills only those, using this skill's [onboarding.md](onboarding.md) as its reference. If `factory-onboard` isn't available, fall back to [onboarding.md](onboarding.md) directly. Then continue. Do not guess infrastructure or status conventions.
5. Check for `factory/code-review.md` (optional — governs the code review gate in Step 5, **and supplies the external tool `factory-qa` reuses for its Step 6 second opinion**). If it's missing, this run just treats external review as **disabled** and proceeds; no need to block on it or force onboarding. If the user wants it, offer to run `/factory-onboard` (it will pick up this one module using `factory-code-review/onboarding.md`) before the Step 5 review gate, or onboard it later before the next run.
6. Check for `factory/qa.md` (optional — the project-specific half of the QA checklist read by `factory-qa` in Step 6). If it's missing, QA runs its generic checks only; offer `/factory-onboard` (picks up this module via `factory-qa/templates/qa.md`) or `/factory-remember` to start it from the first correction that warrants a rule.
7. Check for `factory/plan-review.md` (optional — governs the pre-Execute plan review gate in Step 3). If missing, this run treats it as disabled and proceeds. If the user wants it, note it requires `factory/code-review.md` to already be enabled (it reuses that invocation) — offer `/factory-onboard` (picks up this module via `factory-plan-review/onboarding.md`).

---

## Resume record

Keep a concise local run record at `git rev-parse --git-path factory-run.md` (the command prints
a path in this worktree's Git metadata). It survives resumption without making the reviewed diff dirty.
Record the task's requirements and
accepted corrections, current phase, worktree/branch/HEAD, plan path, stack mode and URLs, verification
commands/results, each review's input revision + artifact directory + task handle, and the next action.
Link substantial reports rather than copying them. Commit final reports through the usual handoff,
not the local process handles. Never store credentials or raw sensitive payloads.

Update it at phase boundaries and before yielding. On resumption, read it and the user's latest
instructions, then verify Git, the live process handles, stack and tracker state before continuing.
A status question is not cancellation. An explicit stop or changed requirement updates the record;
a continuation hook must not resurrect work the user explicitly cancelled. Only mark requirements
done with evidence; do not replace the original scope with the subset already implemented.

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

## Step 3 — Pipeline: plan → re-research → plan review → execute → recheck

**This skill is the driver. Each phase below is a separate skill, and you MUST run it by calling the Skill tool with that skill's name — do not do the work inline from memory.** Invoking the skill pulls in its full instructions; follow them, let it finish, then move to the next phase. Running the work yourself instead of invoking the skill is the main failure mode of the factory — do not do it.

Set a todo list with these phases so progress is visible: Plan → Re-research → Plan review → Execute → Recheck → Stand-up & verify → PR + code review → **QA** → Demo → Handoff. Then run them in order. Loop backward freely — recheck (or live verification) can send you back to plan.

1. **Plan** — call the Skill tool: `factory-plan`. (Research/diagnose, then write the plan to a markdown file in `./tasks` inside the worktree.) Do not write any production code in this phase.
2. **Re-research** — call the Skill tool: `factory-reresearch`. Run it the number of rounds the E-level calls for (E3:1, E2:2, E1:3–4+).
3. **Plan review** (optional, blocking gate — only if `factory/plan-review.md` exists with `Enabled: yes`) — run `factory-plan-review` against the plan file just produced/refined:
   - If `factory/code-review.md` configures an external tool, shell out to it now with its documented invocation, prompt pointing at `factory-plan-review/SKILL.md`'s absolute path and this plan file's path plus the issue reference. Otherwise run `factory-plan-review` yourself via the Skill tool.
   - Read the result's `VERDICT:` line. **`FAIL`** → revise the plan (back to `factory-plan`/`factory-reresearch`) and re-run this gate on the revised plan — do not proceed to Execute on a FAIL. **`PASS`** → continue.
   - Loop here until `PASS` (or the module says disabled/is missing, in which case skip this step entirely — `factory-reresearch` already covered in-context scrutiny of the plan).
4. **Execute (build the plan)** — call the Skill tool: `factory-execute`. It takes the heavily-researched plan and builds it: granular todo list, one item at a time, verify as you go, don't stop until 100% done.
5. **Recheck** — call the Skill tool: `factory-recheck`. If anything is wrong, fix it or go back to plan/re-research. Repeat until genuinely confident — not until you're tired.

Gate: do not proceed to Execute until Plan **and** Re-research have actually been run (the plan file exists) **and, if `factory/plan-review.md` enables it, the plan review gate has returned `PASS`**. Do not proceed to Stand-up until Recheck passes. **Do not proceed to the Demo until the QA gate (Step 6) has returned `PASS`** — that one has no opt-out.

---

## Step 4 — Stand up the stack and smoke-verify

Recheck is a read-only review; **now bring up the stack and confirm the change is actually running.**
Provision the stack **exactly as the repo's `factory/` docs say** (`factory/dev-manager.md` if present —
use its provisioning tool/CLI and only the **minimal** services the task needs; else
`factory/deployment.md`). Adding seed data your feature needs is fine if the docs allow it.

This step is the **smoke test**, not the QA pass: the stack boots, the app serves, the main path of the
new feature responds, and the running build genuinely contains your change. If it doesn't even come up
or the happy path is broken, fix that here — change → apply it the way the docs say (reload/rebuild) →
re-check — before going further.

The deep pass (real user scenarios, both viewports, polish, output quality) is **Step 6 — QA**. Don't
try to do it here, and don't treat "it booted" as evidence the feature is any good.

---

## Step 5 — Commit, open the PR, and run the code review gate

The review gates need a PR to review, so the PR is opened here — **before** QA and the demo — not at the
end of the run.

1. Commit in the worktree (on the task branch). Push if the project's handoff style is auto-push (skip
   only if it's explicitly "wait for the user to push").
2. Open a **pull request** from the task branch if that's the project's handoff style (per `intake.md` /
   the provisioning doc), and link it on the issue.
3. **External code review gate** (only if `factory/code-review.md` exists with **Enabled: yes**) — run
   `factory-code-review` against the PR you just opened:
   - If `code-review.md` configures an external tool, shell out to it now with its documented invocation
     (prompt pointing at `~/.claude/skills/factory-code-review/SKILL.md`'s absolute path and this PR's
     URL). Otherwise, run `factory-code-review` yourself via the Skill tool.
   - Read the result for its `VERDICT:` line. **`FAIL`** → go back to `factory-plan`/`factory-execute`,
     fix it, re-push, and re-run this gate — do not proceed past it on a FAIL. **`PASS`** → continue.
   - Loop here until `PASS` (or the module says disabled/is missing, in which case skip this step
     entirely — `factory-recheck` already covered the in-context review).

> Remember what this gate can and cannot do: it read the **diff**. It never ran the app, never looked at
> the UI, and cannot tell you whether the result is any good. That's the next step, and it is the reason
> the next step exists.

---

## Step 6 — QA: actually use the feature yourself (mandatory blocking gate)

**Call the Skill tool: `factory-qa`.** This is **not optional and has no config switch** — every run goes
through it, at every E-level. (E3 means "don't ask the user questions", not "don't check your work".)

It runs an iterative loop on the stack you just stood up: write the list of things a real user would
actually do → walk every one of them in a real browser (`claude-in-chrome`, falling back to
`playwright-cli`) or against the real CLI/API → judge **functionality**, **intent** (does it do what the
issue actually asked?), **hidden assumptions/shortcuts you took**, and **UI/UX paper-cuts and design
polish on both desktop and mobile** → fix → re-push → re-walk. For LLM/data pipelines it inspects the
**real rendered prompts, the context sent, and output quality across 3–5 examples, never one**. It then
posts a **QA report with screenshots** to the issue and gets an **external second opinion** ("read the
issue, get caught up, what did we miss? what paper-cuts are still there?").

Your obligations as the driver:

- **Do not skip it, do not do it inline from memory, and do not accept a QA report that is clearly
  thin** (a report with no screenshots, or one that never mentions actually opening the UI, is not a QA
  pass — send it back).
- Read the `VERDICT:` line. **`FAIL`** → stay in the loop: fix, re-push, re-QA. If the problem is
  structural, go all the way back to `factory-plan`/`factory-execute`. **`PASS`** → continue to the demo.
- **If QA pushed any commits, the code review from Step 5 is now looking at stale code — re-run the
  Step 5 code review gate once** before moving on.
- Anything QA surfaces as an **assumption** gets posted on the issue and @-mentioned to the owner (the
  standing rule below; this is the step that most often triggers it).

> This gate exists because reading code is not the same as using a product. A run that reaches handoff
> having never opened the thing it built is a failed run, no matter how clean the diff was.

---

## Step 7 — Demo (per the repo's `factory/` demo config)

Record against **the stack you just QA'd** — use whatever URLs/ports the repo's provisioning docs (or
the provisioning tool's own output) report, not a hardcoded address. Default: **always film a demo**
unless the task explicitly says not to. Call the Skill tool for the configured demo mode:
- **`video`** → call the Skill tool: `factory-demo-video` (web UI). Output into the worktree's demo dir.
- **`terminal`** → call the Skill tool: `factory-demo-terminal` (CLI / stdout).
- **`none`** → skip (e.g. a service with no local dev env): finish the code in the worktree and report ready for handoff so the user can push to the remote environment.

**Build the demo out of the QA scenarios.** You just walked the list of what a real user does and you
know exactly which states are interesting — show those, not a hand-wave over the happy path. A
**thorough, longer demo is preferred** over a short one that skips the real behavior; length is not a
problem here. Pull the story from the task itself plus the QA run; don't re-interview the user. If
recording the demo surfaces something off, **go back and fix it** — the demo is a real check, not a
formality.

---

## Step 8 — Handoff (per the Handoff & status config in `intake.md`)

This is a **mandatory phase, not an optional epilogue.** The PR already exists and both gates have
passed; now close the loop. You MUST do all of it — and verify each action actually took effect (re-read
the issue / re-query the status; don't assume the command worked):

1. Make sure everything is committed and pushed to the task branch (QA fixes included) and the PR is
   up to date.
2. Move the tracker status to the configured **ready-for-review** state — then confirm it actually changed.
3. **Post the demo as a comment** on the issue ("here's it working"), per the project's handoff config (the config says exactly how — link/attach). If demo mode is `none`, say so instead. **Do not end the run without doing this.**
4. Confirm the **QA report comment** (with its screenshots/artifacts) is on the issue — `factory-qa`
   posts it, but it is part of the handoff package, so verify it's actually there.
5. **Post the re-provision one-liner** (if the provisioning doc documents one) so the owner can spin the exact stack back up and poke at it themselves — the demo video is not the only review.
6. Post a **concise log** comment: key decisions, assumptions made, open questions.
7. **End the run by leaving the stack the way the repo's `factory/` docs say to** — if they document a non-destructive pause, use it (free the box's resources while keeping containers, data, and the worktree intact so the owner can resume in seconds). **Do not tear the stack down, delete the worktree, or remove any data volume at handoff** — that cleanup happens only after the owner has reviewed and said so. If the docs don't document a pause, leave a clear note of what is left running.

## Definition of done — DO NOT report the task finished until ALL are true

Before you say "done" / "ready" / hand back to the user, every box must be checked. If any is unchecked, you are not done — go do it.

- [ ] Plan + re-research written (plan file exists)
- [ ] **External plan review gate is `PASS`** (if `factory/plan-review.md` enables it; skip if disabled/missing)
- [ ] Built (factory-execute) and Recheck verdict is **PASS**
- [ ] Stack stood up and **smoke-verified** (Step 4) — it boots and the new path responds
- [ ] PR opened (if that's the project's handoff style)
- [ ] External code review gate is `PASS` (if `factory/code-review.md` enables it; skip if disabled/missing) — **re-run if QA pushed commits after it**
- [ ] **`factory-qa` verdict is `PASS`** (Step 6) — ALWAYS required, no config opt-out, no E-level exemption
- [ ] **You personally used the feature** — opened the UI and looked at it on desktop *and* mobile, or ran the pipeline on 3–5 real examples and read the actual prompts and output
- [ ] **QA report posted on the issue, with screenshots** (or output samples for backend work)
- [ ] **QA's external second opinion returned `PASS`** and anything it raised is fixed or answered
- [ ] Demo recorded **and verified** (you looked at it) and built from the QA scenarios, or demo mode is `none`
- [ ] Tracker status moved to ready-for-review (confirmed)
- [ ] Demo posted as an issue comment (or stated `none`)
- [ ] Re-provision one-liner posted (if the provisioning doc documents one)
- [ ] Running-log comment posted (decisions / assumptions / questions)
- [ ] Stack left per the repo's docs (**paused, not destroyed**); worktree + data volumes intact for review

If you catch yourself about to wrap up with any of these missing, stop and finish them first. "I built the code" is **not** the finish line — the handoff is. And **"the code review passed" is not evidence the feature works** — only Step 6 is.

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
- **Never report a task done without having used it yourself.** No "it should work", no inferring from
  the source that the UI must render correctly, no treating the demo recording as the first time you
  look at the feature. If it has a UI you have seen it, on both viewports; if it's a pipeline you have
  read the real prompts and the real output on several examples. Skipping this is the single worst
  failure mode of this system — it hands unreviewed, often visibly broken work to the user and wastes
  their time re-QAing what you were supposed to check.
- **Codebase-agnostic:** read worktree / provisioning / demo / handoff conventions from the working repo's `factory/` docs — never hardcode them here.
