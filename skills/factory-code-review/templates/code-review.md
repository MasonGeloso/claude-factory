# Factory Code Review — <PROJECT NAME>

> Config for the external/second-opinion review step `factory-implement` runs right after opening the
> PR (before the QA gate and the demo), via the `factory-code-review` skill. Filled during onboarding.
> Leave "Enabled: no" if this project doesn't want an external review gate — `factory-recheck` alone
> still runs either way.
>
> The **Tool / Invocation** below is also reused by `factory-qa` for its second-opinion step and by
> `factory-plan-review`, so those gates configure no tool of their own.

## External review
- **Enabled:** <yes | no>
- **Tool:** <e.g. Codex CLI (`codex exec`) | none | other CLI-based coding agent>
- **Invocation:** <exact one-shot command, verified against the actual installed CLI version before
  relying on it — flags drift between releases. Worked example for Codex CLI 0.149.1:
  `codex exec -C <worktree dir> --approve-for-me -c 'sandbox_workspace_write.network_access=true' -o <output file> "Read <abs path>/factory-code-review/SKILL.md and follow it. Review PR: <PR_URL>." < /dev/null`
  Note: `--approve-for-me` and `-s/--sandbox` are **mutually exclusive** in this version —
  `--approve-for-me` already implies the workspace-write sandbox, don't pass both.>
- **Run handling:** Use the bundled `factory-code-review/scripts/run_review.py` wrapper and
  `references/review-runs.md`. Give each invocation its own output and record its task handle;
  require successful process exit and a verdict for the current revision.
- **Tracker CLI for PR diff/comments:** <gh | glab | … — usually the same CLI as `factory/intake.md`; only list here if it differs>
- **Credentials:** <reuse whatever auth `factory/intake.md` already documents — don't stand up a separate credential unless explicitly asked>

## Project-specific checklist
> Besides the obvious review steps (correctness, security, duplication, conventions, tests, docs) —
> is there anything specific to check on *every* review of this codebase?
- <e.g. "Every new DB migration must be reversible">
- <e.g. "No endpoint may skip the tenant-scoping middleware">
- <add more>

## Notes
<Anything else the reviewer should know — house-style exceptions, known false positives to ignore, etc.>
