# Factory Code Review — <PROJECT NAME>

> Config for the external/second-opinion review step `factory-implement` runs in Handoff, via the
> `factory-code-review` skill. Filled during onboarding. Leave "Enabled: no" if this project doesn't
> want an external review gate — `factory-recheck` alone still runs either way.

## External review
- **Enabled:** <yes | no>
- **Tool:** <e.g. Codex CLI (`codex exec`) | none | other CLI-based coding agent>
- **Invocation:** <exact one-shot command, e.g.:
  `codex exec --sandbox workspace-write -c 'sandbox_workspace_write.network_access=true' -a never "Read <abs path>/factory-code-review/SKILL.md and follow it. Review PR: <PR_URL>."`>
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
