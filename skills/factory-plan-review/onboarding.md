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
  (this skill's file, and "Review this plan: `<path>`, for issue `<url>`" instead of "Review PR:
  `<url>`").
- **Requires `factory/code-review.md` to already exist with `Enabled: yes`.** If it doesn't:
  - Offer to onboard `factory/code-review.md` first (`factory-code-review/onboarding.md`), then come
    back to this module.
  - If the user declines external code review entirely, this module cannot function — write
    `factory/plan-review.md` with **Enabled: no** and say why (no reviewer tool configured anywhere in
    this project), rather than asking them to configure one from scratch here.
- Do not re-run the smoke test — `factory/code-review.md`'s own onboarding already verified the
  invocation works on this box.

## 3. Project-specific checklist
- "**Besides completeness / doc-adherence / reuse / risk, is there anything specific we should check
  on every plan for this codebase?**" — a category of requirement that's gotten missed before, a
  pattern this project always wants considered, an architecture note that's easy to overlook. Capture
  as a bullet list.

## 4. Write, confirm
Write `factory/plan-review.md` from the template, filled concretely — the checklist, and an explicit
note that Tool/Invocation are `factory/code-review.md`'s, not configured here. Show the user and
confirm before the first `factory-implement` run relies on it.
