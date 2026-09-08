# Add `factory-plan-review` — external plan review gate

## Context / why

`factory-implement`'s pipeline today only gets an independent second opinion at the very end
(Handoff, Step 6: `factory-code-review` against the opened PR). The user's read: a large share of
regressions and bad code get decided during planning, not during coding — reviewing only the output
catches them late, after execution has already been built on top of a flawed plan. The fix mirrors the
existing code-review gate, but at the other end of the pipeline: after Plan + Re-research finish
(however many rounds that took) and before Execute writes any code.

Hard constraints from the user, verbatim intent:
- Send the **plan** (not a diff) to the reviewer.
- Same reviewer/model as `factory-code-review` — **"same model, not separately configurable."** This
  is a deliberate divergence from how `factory-content-review` was built (which has its own Tool/
  Invocation fields, just documented as copied from code-review.md). `factory-plan-review` must not
  ask "which tool" during onboarding at all — it always reuses `factory/code-review.md`'s config,
  full stop, and simply requires code-review.md to already be enabled.
- Iterate with the reviewer until it passes, only then hand off to execute.
- Same self-onboarding install pattern as content-review: write the skill once in the core `factory`
  repo, re-run `/factory-onboard` on a project, onboarding detects the module missing and installs it,
  modifying `factory-implement`'s own pipeline doc + the onboarding registry. No per-project hand-wiring.
- Factory-wide, not project-specific.
- Install/activate it on the target project right now, once built.

## Research — the exact pattern being mirrored

Read in full: `skills/factory-code-review/{SKILL.md,onboarding.md,templates/code-review.md}`,
`skills/factory-content-review/{SKILL.md,onboarding.md,templates/content-review.md}`,
`skills/factory-implement/SKILL.md`, `skills/factory-onboard/SKILL.md`, and the target project's real
`factory/code-review.md` + `factory/content-review.md` (both already `Enabled: yes`, working Codex CLI
0.149.1 invocations, model `gpt-5.6-terra`).

**The three-file shape every review module uses:**
1. `skills/factory-<x>-review/SKILL.md` — frontmatter (`name`, `description`, `user-invocable: true`),
   dual-mode preamble ("read two ways: in-context, or cold by an external CLI agent"), Step 1 (context
   bootstrap, only needed cold), Step 2 (read everything), Step 3 (scored checklist), Output (table +
   single `VERDICT:` line, exact vocabulary), "What to do with the result", and a final section titled
   "In a `factory-implement` run" / "In a `factory-marketing-post` run" describing exactly how the
   calling pipeline treats the verdict.
2. `skills/factory-<x>-review/onboarding.md` — run when `factory/<x>-review.md` is missing. Small
   numbered sections: (1) enable at all — if not, write `Enabled: no` and stop; (2) which tool +
   mandatory smoke-test-before-trusting-flags instructions; (3) credentials (reuse, never mint new);
   (4) project-specific checklist question; (5) write + confirm.
3. `skills/factory-<x>-review/templates/<x>-review.md` — the config file shape, with a one-line intro
   naming which pipeline step reads it and via which skill, an `## External review` section
   (Enabled/Tool/Invocation/Tracker CLI or N/A/Credentials), the project-specific checklist section,
   and a Notes section.

**Verdict vocabulary differs on purpose per module** — code-review uses binary `PASS`/`FAIL` (matches
a PR: either mergeable or not); content-review uses three-way `SHIP`/`FIX`/`BLOCK` (a finished piece
can have a fixable nit vs. a must-not-ship problem). The user asked for plan review to work like
code-review ("mirroring the code review step... iterates... until it passes") — binary `PASS`/`FAIL`
is the right vocabulary here, not a three-way one; a plan either has real gaps or it doesn't, and this
gate's whole job is "does this need another planning round," a yes/no question.

**How `factory-implement/SKILL.md` wires code-review in** (the exact 4 places a new gate must touch):
1. The "skills this driver runs" table (line ~39) — one row, path column notes the invocation
   exception.
2. The **"One exception" paragraph** right after that table (line ~45) — explains code-review is
   invoked differently (shell out to an external tool per `factory/code-review.md`) vs. in-context.
3. **Step 0, item 5** (line ~74) — the optional-module config check: if `factory/code-review.md` is
   missing, treat external review as disabled and proceed; if the user wants it, offer `/factory-onboard`.
4. **Step 6, item 3** (Handoff, lines 165-168) — the actual gate: run it, read `VERDICT:`, loop on
   `FAIL`, continue on `PASS`, skip entirely if disabled/missing.
5. Also touches: the pipeline table's **"Gate:" line** (line 126, "do not proceed to Execute until...")
   and the **Definition-of-done checklist** (lines 175-191, one checkbox per gate).

**How `factory-onboard/SKILL.md` exposes it as a module** — one row in the registry table (line ~35-36
for the two existing review modules): Module name, what it captures, "Needed by" (which skill/agent),
and the template+onboarding doc pair. That's the entire integration point — factory-onboard's scan/
interview procedure (`### 2. Scan and report a status matrix` / `### 3. Interview`) already iterates
the registry generically; no procedural code changes needed there, only the new row.

**`factory-marketing-post/SKILL.md`'s content-review gate wording** (lines 58-69) confirms the exact
phrasing pattern for a "how the calling skill treats this gate" section — used as the template for
`factory-plan-review`'s own such section, adapted for a driver ("factory-implement run") instead of an
autonomous cron dispatcher.

**Where the real invocation command already lives**: `factory/code-review.md` on
the target project's main branch (already `Enabled: yes`) — the exact command to copy structurally (just
swapping the target SKILL.md path and prompt wording) is:
```
codex exec --approve-for-me \
  -c 'sandbox_workspace_write.network_access=true' \
  -o /tmp/factory_plan_review.txt \
  "Read ~/.claude/skills/factory-plan-review/SKILL.md and follow it. Review this plan: <PLAN_FILE_PATH>, for issue <ISSUE_URL>."
```

## Plan

### 1. New skill: `skills/factory-plan-review/SKILL.md`

Frontmatter:
```yaml
---
name: factory-plan-review
description: Independent, fresh-eyes review of one finished implementation plan — the pre-execution counterpart to `factory-code-review`. Reads the plan file, the originating task/issue it's for, and the project's own `factory/code-review.md` (reused verbatim — this module has no separate tool config), then checks the plan for missing requirements, doc/convention adherence, and pattern fit, and posts a PASS/FAIL verdict. Built to run two ways — invoked in-context via the Skill tool by Claude itself, or run cold by ANY CLI-based coding agent (e.g. Codex CLI's `codex exec`) that was only handed this file's absolute path and a plan file, with no prior conversation context. `factory-implement` runs this as a blocking gate after Plan + Re-research, before Execute writes any code. Use when the user says "factory plan review", "review this plan", "second opinion on the plan", or when `factory-implement` invokes it before Execute.
user-invocable: true
---
```

Body sections, following the established shape exactly:

- Title + one-line framing: *"A different set of eyes — sometimes literally a different model — on
  the plan itself, before a single line of implementation exists."*
- Dual-mode preamble (copy verbatim from code-review, s/PR/plan/, s/diff/plan file/).
- **Step 1 — Establish context (skip if you already have it).**
  - Find `factory/` at the repo root.
  - **Read `factory/code-review.md` for the reviewer tool + invocation.** This skill has **no
    separate tool configuration** — it always reuses whatever `factory/code-review.md` names,
    pointed at this file instead. If `factory/code-review.md` doesn't exist, or exists with
    `Enabled: no`, stop and say external plan review is unavailable — do not fall back to some other
    tool or ask the user to configure one here; that config lives in exactly one place.
  - Read `factory/plan-review.md` for this project's plan-specific checklist (separate from
    code-review's checklist — a plan is reviewed for different things than a diff). If missing, run
    the generic checks only and say so.
  - Read the originating task's `factory/` docs relevant to "does this follow our docs" —
    specifically whatever `factory-implement` Step 0 already loaded (`codebases.md`,
    `deployment.md`, `intake.md`) so the reviewer can check the plan against real project convention,
    not judge it in a vacuum. **Read `factory/intake.md` for the tracker CLI** — a cold agent has no
    prior context and needs this to pull the originating issue itself in Step 2.
  - Identify the plan and issue from the prompt: an absolute path to the plan markdown file in the
    worktree's `./tasks/` dir, and the originating issue id/url (both must be in the prompt handed to
    a cold agent — see the invocation shape below).
- **Step 2 — Read everything.**
  - The **full plan file**, verbatim.
  - The **originating issue**, every comment (same non-negotiable rule as `factory-implement` itself)
    — the requirements the plan must satisfy live there.
  - Skim the **relevant existing code** the plan says it will touch or extend, enough to judge "does
    this plan reinvent something that exists" and "does it match this codebase's actual patterns" —
    not a full read of the codebase, just enough to check the plan's own claims about what's there.
- **Step 3 — Review.** Score, PASS/WARN/FAIL each:
  1. **Completeness** — does the plan address every requirement in the issue, including every
     comment? Anything the issue asks for that the plan is silent on?
  2. **Doc & convention adherence** — does the plan follow this project's own `factory/` docs
     (worktree convention, provisioning, existing architecture notes) and the codebase's real
     patterns, rather than inventing its own approach where an established one exists?
  3. **Reuse & simplification** — does the plan re-derive/re-implement something that already exists
     (a util, a service, a pattern) instead of using it? Is it proposing more abstraction than the
     task needs?
  4. **Risk & unknowns** — does the plan surface its own open questions/risks honestly, or does it
     paper over a genuine unknown as if it were settled?
  5. **Project-specific checklist** — every bullet from `factory/plan-review.md`, each scored on its
     own line.
- **Output & posting** — same table shape as code-review, PASS/WARN/FAIL columns, then exactly one of
  `VERDICT: PASS` / `VERDICT: FAIL` on its own line. FAIL if anything is ❌. Ruthlessly concise bullets
  below (❌ **Fix:** / ⚠️ **Heads up:**, each naming the specific plan section). Unlike code-review,
  there's no PR to comment on — **the verdict + notes are the final printed output**, captured by
  `-o` when run cold; when run in-context, report it directly to the driver/user.
- **In a `factory-implement` run** — mirror code-review's closing section: "This is a blocking gate,
  not advisory — run once Plan + Re-research finish, before Execute starts. `VERDICT: FAIL` means
  revise the plan (back to `factory-plan`/`factory-reresearch`) and re-run this gate on the revised
  plan. Loop until `VERDICT: PASS` (or `factory/plan-review.md` says disabled/is missing — then this
  step is skipped, `factory-reresearch` already covered in-context scrutiny of the plan)."

### 2. New `skills/factory-plan-review/onboarding.md`

Mirror the numbered-sections shape, but Section 2 is structurally different per the "not separately
configurable" constraint:

```markdown
# Factory — Plan Review Onboarding

Run when `factory/plan-review.md` is missing and `/factory-onboard` or `/factory-implement` needs it.
This module is **optional** — a repo can run Factory forever without it; `factory-reresearch` still
covers in-context plan scrutiny either way. This just adds an independent, external second opinion on
the finished plan itself, before any code is written.

Ask in small batches (AskUserQuestion where it fits).

## 1. Enable it at all?
- Do you want an **independent second opinion on the plan** — before Execute writes any code — to run
  after Plan + Re-research finish? Or skip this and rely on `factory-reresearch` alone?
- If skipping: write `factory/plan-review.md` with **Enabled: no** and stop here (still worth
  capturing the project-specific checklist below for future use, but mark it inactive).

## 2. Tool — reused from code-review, not configured here
- **This module has no separate tool/invocation config.** It always runs the exact same external tool
  and invocation as `factory/code-review.md` — only the target skill file and prompt wording differ
  (this skill's file, and "Review this plan: <path>" instead of "Review PR: <url>").
- **Requires `factory/code-review.md` to already exist with `Enabled: yes`.** If it doesn't:
  - Offer to onboard `factory/code-review.md` first (`factory-code-review/onboarding.md`), then come
    back to this module.
  - If the user declines external code review entirely, this module cannot function — write
    `factory/plan-review.md` with **Enabled: no** and say why (no reviewer tool configured anywhere
    in this project), rather than asking them to configure one from scratch here.
- Do not re-run the smoke test — `factory/code-review.md`'s own onboarding already verified the
  invocation works on this box.

## 3. Project-specific checklist
- "**Besides completeness/doc-adherence/reuse/risk, is there anything specific we should check on
  every plan for this codebase?**" — a category of requirement that's gotten missed before, a
  pattern this project always wants considered, an architecture note that's easy to overlook.
  Capture as a bullet list.

## 4. Write, confirm
Write `factory/plan-review.md` from the template, filled concretely — the checklist, and an explicit
note that Tool/Invocation are `factory/code-review.md`'s, not configured here. Show the user and
confirm before the first `factory-implement` run relies on it.
```

### 3. New `skills/factory-plan-review/templates/plan-review.md`

```markdown
# Factory Plan Review — <PROJECT NAME>

> Config for the external/second-opinion review step `factory-implement` runs after Plan +
> Re-research, before Execute, via the `factory-plan-review` skill. Filled during onboarding.
> Leave "Enabled: no" if this project doesn't want an external plan-review gate —
> `factory-reresearch` alone still runs either way.
>
> **This module has no Tool/Invocation of its own.** It reuses `factory/code-review.md`'s exactly —
> same tool, same sandbox flags, same credentials — only the target skill file and prompt wording
> differ. If `factory/code-review.md` is missing or `Enabled: no`, this module cannot run regardless
> of what's written below.

## External review
- **Enabled:** <yes | no>
- **Tool / Invocation / Credentials:** same as `factory/code-review.md` — not configured separately
  here. (See that file.)

## Project-specific checklist
> Besides the generic checks (completeness against the issue, doc/convention adherence, reuse vs.
> reinvention, honest risk surfacing) — is there anything specific to check on *every* plan for this
> codebase?
- <e.g. "Every plan touching a DB schema must state the migration's reversibility up front">
- <e.g. "Every plan for a new endpoint must name which authz chokepoint it goes through">
- <add more>

## Notes
<Anything else the reviewer should know — house-style exceptions, known false positives to ignore.>
```

### 4. Edit `skills/factory-implement/SKILL.md` — five touch points

1. **Skills table** (after the `factory-plan`/`factory-reresearch` rows, before `factory-execute`,
   since it slots there positionally too):
   ```
   | Plan review (optional, pre-Execute gate) | `factory-plan-review` | `~/.claude/skills/factory-plan-review/SKILL.md` — see the exception note below, invocation differs |
   ```
2. **"One exception" paragraph** — extend to cover both gates:
   > **Two exceptions: `factory-code-review`** (Handoff, Step 6) **and `factory-plan-review`** (Step 3,
   > pre-Execute) are invoked *differently* when their respective config file names an external tool
   > — shell out to that tool with a prompt pointing at the relevant `SKILL.md`'s absolute path (a PR
   > URL for code-review, the plan file's path for plan-review), since an external CLI agent can't
   > resolve a Claude Code skill name. If no external tool is configured (or the config file doesn't
   > exist), run the skill yourself via the Skill tool instead — same review, just in-context.
3. **Step 0, new item 6** (after the existing code-review item 5):
   ```
   6. Check for `factory/plan-review.md` (optional — governs the pre-Execute plan review gate in
      Step 3). If missing, this run treats it as disabled and proceeds. If the user wants it, note it
      requires `factory/code-review.md` to already be enabled (it reuses that invocation) — offer
      `/factory-onboard` (picks up this module via `factory-plan-review/onboarding.md`).
   ```
4. **Step 3 pipeline** — insert between item 2 (Re-research) and item 3 (Execute), renumber:
   ```
   1. **Plan** — call the Skill tool: `factory-plan`. …
   2. **Re-research** — call the Skill tool: `factory-reresearch`. …
   3. **Plan review** (optional, blocking gate — only if `factory/plan-review.md` exists with
      `Enabled: yes`) — run `factory-plan-review` against the plan file just produced/refined:
      - If `factory/code-review.md` configures an external tool, shell out to it now with its
        documented invocation, prompt pointing at `factory-plan-review/SKILL.md`'s absolute path and
        this plan file's path. Otherwise run `factory-plan-review` yourself via the Skill tool.
      - Read the result's `VERDICT:` line. **`FAIL`** → revise the plan (back to `factory-plan`/
        `factory-reresearch`) and re-run this gate on the revised plan — do not proceed to Execute on
        a FAIL. **`PASS`** → continue.
      - Loop here until `PASS` (or the module says disabled/is missing, in which case skip this step
        entirely — `factory-reresearch` already covered in-context scrutiny of the plan).
   4. **Execute (build the plan)** — call the Skill tool: `factory-execute`. …
   5. **Recheck** — call the Skill tool: `factory-recheck`. …
   ```
   And update the **"Gate:" line** right after the table:
   > Gate: do not proceed to Execute until Plan **and** Re-research have actually been run (the plan
   > file exists) **and, if `factory/plan-review.md` enables it, the plan review gate has returned
   > `PASS`**. Do not proceed to Stand-up/Demo/Handoff until Recheck passes.
5. **Definition of done checklist** — one new checkbox, placed right after the existing "Plan +
   re-research written" line:
   ```
   - [ ] **External plan review gate is `PASS`** (if `factory/plan-review.md` enables it; skip if
         disabled/missing)
   ```

### 5. Edit `skills/factory-onboard/SKILL.md` — one registry row

Insert after the `content-review.md` row (keeps all four review-adjacent optional modules grouped):
```
| `plan-review.md` | whether an external second-opinion plan review is enabled (reuses `code-review.md`'s tool/invocation — not configured separately), project-specific checklist | implement (pre-Execute gate) | `factory-plan-review/templates/plan-review.md` + `factory-plan-review/onboarding.md` |
```
No procedural changes needed in the Scan/Interview sections — they already iterate the registry
generically. (Optional nuance not worth its own registry column: if a user tries to enable
`plan-review.md` while `code-review.md` is missing/disabled, `factory-plan-review/onboarding.md`
itself handles that dependency — no special-casing needed in `factory-onboard`'s own procedure.)

### 6. Install core-repo changes + activate on the target project

1. In `~/code/factory`: create the three new files above, run `./install.sh` to refresh
   `~/.claude/skills/` (confirms no install errors, matches the pattern used after every skill change
   this session), commit + push to `origin/main`.
2. In `~/code/<project>` (the real checkout the `marketing-post` agent runs in — **not** the
   marketing-migration worktree, which is done and merged): run `/factory-onboard`. It will scan,
   report `factory/plan-review.md` missing → needed by: implement, and offer to onboard it (default
   scope is "missing modules only," which this now is).
   - Since `factory/code-review.md` is already `Enabled: yes` there, the dependency check in
     `factory-plan-review/onboarding.md` passes immediately — no need to onboard code-review first.
   - Answer the "enable at all" question (yes, matching the existing code-review/content-review
     posture on this repo) and the project-specific-checklist question (reuse the project's existing
     code-review checklist categories as a starting point — migrations/authz/observability/cost/
     triggers/localization/tests/vibecoded-look — since a plan review should check the plan commits
     to addressing these, same as the diff-review already checks the code does).
   - Confirm the resulting `factory/plan-review.md`, commit + push on the project's `main`.
3. Verify: `factory-implement/SKILL.md`'s Step 0 item 6 and Step 3 item 3 now have something to read
   on the project; no live `factory-implement` run needs to actually happen to prove the wiring — the module
   registry status matrix (all four review-adjacent modules ✓) is the confirmation.

## Verification
- Read `factory-plan-review/SKILL.md` back and confirm every established-pattern element is present:
  dual-mode preamble, PASS/FAIL vocabulary (not SHIP/FIX/BLOCK — that's content-review's), the
  no-separate-tool-config statement in Step 1, final "In a factory-implement run" section.
- Confirm `factory-implement/SKILL.md`'s five touch points all landed and read coherently alongside
  the existing code-review references (no contradictory gate wording between the two).
- Confirm `factory-onboard/SKILL.md`'s new row matches the existing rows' column shape exactly.
- Re-run `./install.sh` in `~/code/factory` after all edits, confirm 25 skills install cleanly (24
  today + the new one).
- On the project: confirm `factory/plan-review.md` exists, `Enabled: yes`, and its own text is internally
  consistent (references code-review.md correctly, has a real project-specific checklist, no stray
  Tool/Invocation fields duplicated in by mistake).
