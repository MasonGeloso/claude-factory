---
name: factory-plan-review
description: Independent, fresh-eyes review of one finished implementation plan — the pre-execution counterpart to `factory-code-review`. Reads the plan file, the originating task/issue it's for, and the project's own `factory/code-review.md` (reused verbatim — this module has no separate tool config), then checks the plan for missing requirements, doc/convention adherence, and pattern fit, and posts a PASS/FAIL verdict. Built to run two ways — invoked in-context via the Skill tool by Claude itself, or run cold by ANY CLI-based coding agent (e.g. Codex CLI's `codex exec`) that was only handed this file's absolute path and a plan file, with no prior conversation context. `factory-implement` runs this as a blocking gate after Plan + Re-research, before Execute writes any code. Use when the user says "factory plan review", "review this plan", "second opinion on the plan", or when `factory-implement` invokes it before Execute.
user-invocable: true
---

# Factory — Plan Review (external / second-opinion)

*A different set of eyes — sometimes literally a different model — on the plan itself, before a
single line of implementation exists.*

This skill is read two ways:
1. **In-context (Claude, via the Skill tool).** You already have the conversation's context — the
   task, the plan, the worktree. Skip straight to **Step 2**.
2. **Cold, by an external CLI agent** (Codex CLI or similar) that was handed nothing but this file's
   absolute path, a plan file path, and an issue reference. You have no prior context — do
   **Step 1** first to bootstrap it yourself.

> If you're an external agent reading this file directly: this is a plain markdown instruction file,
> not a Claude Code skill invocation — just follow it as your task.

---

## Step 1 — Establish context (skip if you already have it)

- Make sure you're working inside the repo the plan belongs to (the worktree it was built in, or a
  fresh checkout/clone if you're starting cold — read-only is enough, you don't need to build
  anything).
- Find `factory/` at the repo root. Read `factory/code-review.md` for context if present.
  The driver owns tool selection and invocation; an already-invoked reviewer reviews the plan itself,
  including when called directly without an external-tool configuration.
- Read `factory/plan-review.md` for this project's plan-specific checklist (separate from
  code-review's checklist — a plan is reviewed for different things than a diff). If missing, run the
  generic checks only and say so.
- Read `factory/codebases.md`, `factory/deployment.md`, and `factory/intake.md` — the same docs
  `factory-implement` Step 0 already loaded — so you can check the plan against real project
  convention, not judge it in a vacuum. **`factory/intake.md` also gives you the tracker CLI**, needed
  to pull the originating issue yourself since a cold agent has no prior context.
- Identify the plan and issue from the prompt you were given: an absolute path to the plan markdown
  file (usually in the worktree's `./tasks/` dir), and the originating issue id/url.

## Step 2 — Read everything

- The **full plan file**, verbatim.
- The **originating issue**, using the tracker CLI from `intake.md` (e.g. `gh issue view <num>
  --comments`), and **every comment**, start to finish — none skipped, none truncated, same rule as
  the rest of Factory. The requirements the plan must satisfy live there, not just in the plan's own
  restatement of them.
- Skim the **relevant existing code** the plan says it will touch or extend — enough to judge whether
  the plan reinvents something that already exists and whether it matches this codebase's actual
  patterns. Not a full read of the codebase, just enough to check the plan's own claims about what's
  there.

## Keep the plan authoritative

When a design changes, revise its authoritative sections and remove superseded schemas, examples and
tests from the active contract. Keep necessary decision history separate and explicitly non-normative;
do not append a new design below an incompatible old one. Preserve every accepted requirement.

A plan review decides whether implementation has a sound direction: scope, ownership, invariants,
external contracts and how to verify them. It need not pre-write every constructor or incidental field
count. A contradiction about which actor can release paid work is blocking; a redundant prose count
is a warning when the actual schema and behavior are unambiguous. If correctness depends on a subtle
state machine or provider behavior, use a small executable contract/probe to resolve that uncertainty
instead of growing speculative prose through more review rounds.

For follow-ups, use [finding closure and round quality](../factory-code-review/references/review-runs.md#make-each-round-earn-its-cost).
Review all known consequences of a changed design together. Classify each new finding by concrete
impact, and verify earlier fixes without making settled details a new design exercise.

Apply the [conditional failure checks](../factory-plan/references/preventable-failures.md) when this task changes progress tracking,
scheduling, data representation, external payload handling or pipeline monitoring. Reuse applicable
evidence in the existing gate; do not add a review round just to restate it.

## Step 3 — Review

Score every category below against what you just read. PASS / WARN / FAIL each:

1. **Completeness** — does the plan address every requirement in the issue, including every comment?
   Anything the issue asks for that the plan is silent on?
2. **Doc & convention adherence** — does the plan follow this project's own `factory/` docs (worktree
   convention, provisioning, existing architecture notes) and the codebase's real patterns, rather
   than inventing its own approach where an established one exists?
3. **Reuse & simplification** — does the plan re-derive or re-implement something that already exists
   (a util, a service, a pattern) instead of using it? Is it proposing more abstraction than the task
   needs?
4. **Risk & unknowns** — does the plan surface its own open questions/risks honestly, or does it paper
   over a genuine unknown as if it were settled?
5. **Project-specific checklist** — open `factory/plan-review.md` and turn **every bullet into its own
   todo**, then work them one at a time. Each bullet gets its own targeted pass: find where the plan
   addresses it (quote the section) or establish that it is silent on it. Each is scored on its own
   row, and its note must say which part of the plan settled it, or `n/a — <why this plan cannot
   violate it>`. A plan that is *silent* on an applicable bullet has not satisfied it.

Before deciding the verdict, identify the exact reviewed revision and check that requirements from
later user corrections were included. Separate blocking defects from optional unrelated improvements.
A cold external reviewer performs this review itself; do not recursively launch another reviewer.

## Output & posting

Same table shape as `factory-code-review`:

| Check | Status | Note |
|-------|--------|------|
| Completeness | ✅/⚠️/❌ | one-line TLDR |
| Doc & convention adherence | ✅/⚠️/❌ | one-line TLDR |
| Reuse & simplification | ✅/⚠️/❌ | one-line TLDR |
| Risk & unknowns | ✅/⚠️/❌ | one-line TLDR |
| *(project checklist item)* | ✅/⚠️/❌ | one-line TLDR |

Then, on its own line, exactly one of:
```
VERDICT: PASS
VERDICT: FAIL
```
FAIL if anything is ❌. Be ruthlessly concise below the table — no word salad:
- ❌ **Fix:** which section of the plan — what's missing or wrong, what it should say instead.
- ⚠️ **Heads up:** what looks off, why it's not blocking.

Unlike `factory-code-review`, there is no PR to comment on — **the table + verdict are the final
printed output.** A headless caller (`codex exec -o <path>`, etc.) captures only that and needs it to
contain the full table and the `VERDICT:` line so it can be grepped without re-fetching anything; when
run in-context, report it directly to the driver/user.

## In a `factory-implement` run

This is a **blocking gate**, not advisory — run once Plan **and** Re-research finish (however many
rounds the task's E-level called for), before Execute writes any code. `VERDICT: FAIL` means revise
the plan (back to `factory-plan`/`factory-reresearch`) and re-run this gate on the revised plan — do
not proceed to Execute on a FAIL. Loop until `VERDICT: PASS` (or `factory/plan-review.md` says
disabled/is missing, in which case this step is skipped entirely — `factory-reresearch` already
covered in-context scrutiny of the plan).
