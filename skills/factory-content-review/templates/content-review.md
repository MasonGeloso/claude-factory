# Factory Content Review — <PROJECT NAME>

> Config for the external/second-opinion content review step `factory-marketing-post` runs as the
> last gate before publishing, via the `factory-content-review` skill. Filled during onboarding.
> Leave "Enabled: no" if this project doesn't want this gate — publishing still runs the content
> type's own de-slop/factual checks either way, just without an independent outside read.

## External review
- **Enabled:** <yes | no>
- **Tool:** <e.g. Codex CLI (`codex exec`) | none | other CLI-based coding agent>
- **Invocation:** <exact one-shot command, verified against the actual installed CLI version before
  relying on it — flags drift between releases. Worked example for Codex CLI 0.149.1:
  `codex exec -C <repo dir> --approve-for-me -c 'sandbox_workspace_write.network_access=true' -o <output file> "Read <abs path>/factory-content-review/SKILL.md and follow it. Review this content: <packet path or inline>." < /dev/null`
  Note: `--approve-for-me` and `-s/--sandbox` are **mutually exclusive** in this version —
  `--approve-for-me` already implies the workspace-write sandbox, don't pass both.>

## Audience & voice
- **Audience:** <who reads this — expertise level, what they already know, what they don't share with
  whoever writes it>
- **Voice:** <the account/publication's documented register — e.g. "dry-funny and always right, not
  loud"; anything explicitly banned (a comedy-account register, hype, apology, revealing machine
  authorship)>
- **The bar for "actually good":** <what does this project's content need to do to earn a stranger's
  attention — a hook test, a specific structural requirement, etc.>

## Project-specific checklist
> Besides accuracy/tone/quality — is there anything specific to check on *every* piece this project
> publishes?
- <e.g. "Every hard number must trace to a source in the packet, never to an LLM-summarized field">
- <e.g. "Never reveal or hint the content is machine-produced">
- <add more>

## Notes
<Anything else the reviewer should know — a past incident worth remembering (e.g. a specific class of
claim the packet kept omitting), house-style exceptions, known false positives to ignore.>
