# Factory — Content Review Onboarding

Run when `factory/content-review.md` is missing and `/factory-onboard` or the `marketing-post` agent
needs it. This module is **optional** — the marketing pillar runs forever without it; each content
type's own de-slop/factual-check steps still apply either way. This just adds an independent, outside
read on the finished piece right before it publishes.

Ask in small batches (AskUserQuestion where it fits).

## 1. Enable it at all?
- Do you want an **independent second opinion** — from a different model/tool than whatever built the
  content — to run on every piece before it publishes? Or skip this and rely on each content type's
  own checks alone?
- If skipping: write `factory/content-review.md` with **Enabled: no** and stop here (still worth
  capturing audience/voice below for future use, but mark it inactive).

## 2. Which tool?
- What CLI-based agent should run it? (e.g. Codex CLI, Cursor Agent, Aider, opencode.) Confirm it's
  actually installed and authenticated on the box the `marketing-post` agent runs on.
- **Smoke-test the exact invocation before writing it down — do not trust a remembered or researched
  flag set.** Run `<tool> exec --help` yourself, confirm the non-interactive entry point and its real
  flag names, then run one trivial prompt end-to-end and confirm it actually returns. Only write the
  command down once you've seen it work.
  - **Errors immediately** with an argument-parse complaint → the docs/your memory are stale, diff
    real `--help` output against what you were about to pass.
  - **Hangs** → missing the non-interactive flag, it dropped into an interactive prompt.
  - **Runs but produces nothing useful** → auth or sandbox/network, not flags.
- The prompt it runs must point at `factory-content-review/SKILL.md`'s **absolute path** — external
  tools can't resolve Claude Code's skill names.
- If this project already has `factory/code-review.md` configured with a working invocation, reuse the
  same tool/sandbox flags — just point the prompt at this skill's file instead. Don't re-derive them
  from scratch if they're already proven to work on this box.

## 3. Audience & voice
- "**Who reads this, and what do they already know that whoever writes it might forget to explain?**"
- "**What's the account/publication's voice — and is there anything explicitly banned** (a register,
  a phrase pattern, revealing machine authorship)?"
- "**What makes a piece 'actually good' here, not just correct?**" — a specific hook test, a structural
  bar, whatever the project already knows from experience.

## 4. Project-specific checklist
- "**Besides accuracy/tone/quality, is there anything specific we should check on every piece?**" —
  a claim-sourcing rule, a banned-word list, a past incident worth guarding against. This is the part
  a generic checklist always misses.

## 5. Write, confirm
Write `factory/content-review.md` from the template, filled concretely — real command, real audience/
voice, real checklist. Show the user and confirm before `factory-marketing-post` relies on it as a
publishing gate.
