---
name: factory-code-review
description: Independent, fresh-eyes review of one pull/merge request — reads the full diff, the linked issue, and the project's own checklist (`factory/code-review.md`), scores generic engineering categories (correctness, security, duplication/simplification, conventions, test coverage, docs), then posts a PASS/WARN/FAIL table and a VERDICT as a comment on the PR. Built to run two ways — invoked in-context via the Skill tool by Claude itself, or run cold by ANY CLI-based coding agent (e.g. Codex CLI's `codex exec`) that was only handed this file's absolute path and a PR link, with no prior conversation context. `factory-implement` runs this (often via an external tool) as a blocking gate right after opening the PR — before the `factory-qa` gate and the demo. Use when the user says "factory code review", "review this PR", "second opinion review", or when `factory-implement` invokes it against a freshly opened PR.
---

# Factory — Code Review (external / second-opinion)

*A different set of eyes — sometimes literally a different model — on the actual diff, after it's already a PR.*

This skill is read two ways:
1. **In-context (Claude, via the Skill tool).** You already have the conversation's context — the task, the plan, the worktree. Skip straight to **Step 2**.
2. **Cold, by an external CLI agent** (Codex CLI or similar) that was handed nothing but this file's absolute path and a one-line prompt naming a PR. You have no prior context — do **Step 1** first to bootstrap it yourself.

> If you're an external agent reading this file directly: this is a plain markdown instruction file, not a Claude Code skill invocation — just follow it as your task.

---

## Step 1 — Establish context (skip if you already have it)

- Make sure you're working inside the repo the PR belongs to (the worktree it was built in, or a fresh checkout/clone if you're starting cold — read-only is enough, you don't need to build anything).
- Find `factory/` at the repo root. Read `factory/code-review.md` for this project's own "always check for" checklist and which tracker CLI to use for pulling/posting. If that file doesn't exist, fall back to `factory/intake.md`'s tracker CLI and run the generic checklist only — say so in your output.
- Identify the PR from the prompt you were given (a URL, or `<owner>/<repo>#<num>`).

For a follow-up, also follow [finding closure and round quality](references/review-runs.md#make-each-round-earn-its-cost).
Use prior finding IDs and repair evidence to distinguish an incomplete fix from a new regression.
Keep the full review scope; do not manufacture a new blocker merely because earlier findings closed.

## Step 2 — Read everything

- Pull the **full diff** with the tracker CLI (e.g. `gh pr diff <PR>` / the `glab` equivalent).
- Read the PR description and **every comment**, start to finish — none skipped, none truncated, same rule as the rest of Factory.
- Read the **originating issue** the PR closes/references, including its own comment thread, if one is linked. The requirements live there, not just in the diff.

Apply the [conditional failure checks](../factory-plan/references/preventable-failures.md) when this task changes progress tracking,
scheduling, data representation, external payload handling or pipeline monitoring. Reuse applicable
evidence in the existing gate; do not add a review round just to restate it.

## Step 3 — Review

Score every category below against what you just read. PASS / WARN / FAIL each:

1. **Correctness** — Does it do everything the issue asked, including every comment? Trace the actual behavior, don't take the diff's word for it. **Watch specifically for a requirement satisfied by seeded, hardcoded, or fixture data instead of the mechanism that was the point of the issue** — a UI built against stubbed rows where the pipeline producing those rows was the work. That is not a scope decision, it is an unbuilt requirement.
2. **Bugs & edge cases** — Try to break it. What inputs/states/paths fail?
3. **Security** — Auth holes, missing validation on sensitive paths, leaked secrets, admin endpoints that don't check for admin.
4. **Duplication & simplification** — Reinvented something that already exists in the repo? Unnecessary abstraction for a one-shot need?
5. **Conventions & interfaces** — Matches this codebase's existing patterns, or off the rails?
6. **Test coverage** — Are the new/changed paths actually tested, not just touched?
7. **Documentation** — Anything that warranted a doc update and didn't get one? And the other direction: does any **existing** doc now describe behavior this diff removed, renamed, or changed? A doc left describing the old shape is worse than no doc — grep the docs for the symbols the diff touched.
8. **Project-specific checklist** — open `factory/code-review.md` and turn **every bullet into its own todo**, then work them one at a time. Each bullet gets its own targeted scan — grep for the thing it names, open the files it points at — not one pass over the diff answering all of them from memory. Each is scored on its own row, and its note must cite what you actually looked at: a `file:line` where it hits, or `n/a — <why this diff cannot violate it>` where it doesn't. "Looks fine" on a checklist row is not a review of that row.

Before deciding the verdict, identify the exact reviewed revision and check that requirements from
later user corrections were included. Separate blocking defects from optional unrelated improvements.
A cold external reviewer performs this review itself; do not recursively launch another reviewer.

## Output & posting

Same table shape as `factory-recheck`, plus the project-specific rows:

| Check | Status | Note |
|-------|--------|------|
| Correctness | ✅/⚠️/❌ | one-line TLDR |
| Bugs & edge cases | ✅/⚠️/❌ | one-line TLDR |
| Security | ✅/⚠️/❌ | one-line TLDR |
| Duplication & simplification | ✅/⚠️/❌ | one-line TLDR |
| Conventions & interfaces | ✅/⚠️/❌ | one-line TLDR |
| Test coverage | ✅/⚠️/❌ | one-line TLDR |
| Documentation | ✅/⚠️/❌ | one-line TLDR |
| *(project checklist item)* | ✅/⚠️/❌ | one-line TLDR |

Then, on its own line, exactly one of:
```
VERDICT: PASS
VERDICT: FAIL
```
FAIL if anything is ❌. Be ruthlessly concise below the table — no word salad:
- ❌ **Fix:** `file:line` — what's wrong, what it should be.
- ⚠️ **Heads up:** `file:line` — what looks off, why it's not blocking.

Post this exact table + verdict as a **single comment on the PR** via the tracker CLI (e.g. `gh pr comment <PR> --body-file -`). Also make sure it's your final printed output — a headless caller (`codex exec -o <path>`, etc.) captures only that and needs it to contain the full table and the `VERDICT:` line so it can be grepped without re-fetching the PR.

## In a `factory-implement` run

This is a **blocking gate**, not advisory — run once the PR exists (Step 5 of the driver), **before the
`factory-qa` gate and the demo**, and well before the tracker status moves to ready-for-review.
`VERDICT: FAIL` sends the run back to `factory-plan`/`factory-execute` for fixes; once re-pushed, re-run
this step. Loop until `VERDICT: PASS` (or `factory/code-review.md` says external review is disabled for
this repo).

**What this review cannot do:** it only reads the diff — it never runs the app, never opens the UI, and
so cannot judge whether the result is actually good, complete, or polished. That is
[`factory-qa`](../factory-qa/SKILL.md)'s job, which runs immediately after this and is not optional. A
`PASS` here is not evidence the feature works. If QA later pushes fixes, this gate gets re-run against
the updated PR.
