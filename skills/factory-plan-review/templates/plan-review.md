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
