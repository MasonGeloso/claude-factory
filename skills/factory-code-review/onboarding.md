# Factory — Code Review Onboarding

Run when `factory/code-review.md` is missing and either `/factory-onboard` or `/factory-implement`
needs it. This module is **optional** — a repo can run Factory forever without it; `factory-recheck`
still covers the in-context review either way. This just adds an independent, external second opinion
on the actual PR diff after it's opened.

Ask in small batches (AskUserQuestion where it fits).

## 1. Enable it at all?
- Do you want a **second, independent review** — ideally from a different model/tool — to run on every
  PR before it's marked ready-for-review? Or skip this and rely on `factory-recheck` alone?
- If skipping: write `factory/code-review.md` with **Enabled: no** and stop here (still worth
  capturing the project-specific checklist below for future use, but mark it inactive).

## 2. Which tool?
- What CLI-based coding agent should run it? (e.g. Codex CLI, Cursor Agent, Aider, opencode.) Confirm
  it's actually installed and authenticated on the box `factory-implement` runs on — don't configure
  a tool that isn't there.
- **Smoke-test the exact invocation before writing it into `code-review.md` — do not trust a
  remembered or researched flag set.** CLI flags for these tools drift release to release (e.g.
  Codex CLI's approval flag has changed shape more than once). Run `<tool> exec --help` / `<tool>
  --help` yourself, confirm the non-interactive/headless entry point and its actual flag names, then
  run one trivial prompt end-to-end (e.g. "reply with exactly: OK") and confirm it actually returns —
  not just that it launched. Only write the command down once you've seen it work.
  - If it **errors immediately** with an argument-parse complaint, the docs/your memory are stale —
    diff the real `--help` output against what you were about to pass.
  - If it **hangs**, you're missing the non-interactive flag (it dropped into an interactive
    TUI/prompt waiting on approval).
  - If it **runs but produces nothing useful**, that's auth or sandbox/network, not flags — check it
    can actually reach the tracker CLI (`gh`/`glab`) from inside its sandbox.
- The prompt it runs must point at `factory-code-review/SKILL.md`'s **absolute path** — external tools
  can't resolve Claude Code's skill names.

## 3. Credentials
- **Reuse whatever tracker CLI/credential `factory/intake.md` already documents** (gh/glab, however
  it's authenticated) so the external tool can read the diff and post its review comment. Do not stand
  up a separate token or credential unless the user explicitly asks for one scoped differently.

## 4. Project-specific checklist
- "**Besides the obvious code-review steps, is there anything specific we should check on every review
  of this codebase?**" — migrations, tenant-scoping, a house convention that's bitten them before,
  whatever's non-obvious from the code itself. Capture as a bullet list; this is the part hand-written
  generic checklists always miss.

## 5. Write, confirm
Write `factory/code-review.md` from the template, filled concretely — real command, real checklist.
Show the user and confirm before the first `factory-implement` run relies on it.
