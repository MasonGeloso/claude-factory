# Factory Intake Config — <PROJECT NAME>

> How this project takes a brain-dump / transcript and turns it into tracker issues.
> Filled during onboarding. Keep it concrete — embed real commands, IDs, and label names.

## Tracker & interface
- **System:** <GitHub Projects | GitLab | Jira | Zapier | markdown | …>
- **CLI / interface:** <gh | glab | jira | webhook>
- **Where issues go:** <repo / project board / Jira project key + IDs>
- **Create command(s):** <e.g. `gh issue create --repo ORG/REPO --label …`>
- **Query / dedup command(s):** <e.g. `gh issue list --search "…"`, `gh project item-list …`>
- **Add-to-board / monitor:** <e.g. `gh project item-add …`>

## Issue taxonomy (what each type is here)
- **Epic:** <when an item is big enough to be an epic>
- **Issue / task:** <the default unit>
- **Spike:** <when something is unresearched/uncertain — research ticket>
- **Labels / fields / priority:** <names + meanings>

## Classification mapping
- **Scheme:** <standard T1–T3 × E1–E3  |  opted-out custom scheme>
- **T (priority) → tracker:** <which label/field encodes T1/T2/T3>
- **E (complexity/autonomy) → tracker:** <which label/field encodes E1/E2/E3>
- **Type rules:** <which T/E combos become epic vs issue vs spike>
- **Automation:** <any combos auto-picked-up / self-merged by an agent>

## Intake sources
- **Default — solo voice transcript:** one person (the user) talking. Parse directly into items.
- **<e.g. Weekly team sync>:** *Indicators:* <multiple speakers, meeting/back-and-forth format>. *Handling:* <extract action items only; ignore discussion/opinions>.
- <add more sources as needed>

## Conventions & rules
- **Title style:** <short, pointy; conventions>
- **Description format:** <TLDR first, then context; required sections>
- **Always capture:** <context this tracker expects>
- **Never include:** secrets / tokens / credentials / hard-coded sensitive values — and <anything project-specific>.

## Handoff & status
> Used by `/factory-execute` when a task is finished. Also relevant at intake time so created issues start in the right state.
- **In-progress status:** <status/column set when a task is picked up — e.g. "In Progress"; or "none">
- **Ready-for-review status:** <what status/column means "done, please review" — e.g. move GitHub Project item to "Ready for Review">
- **Where updates go:** <same tracker — post comments on the issue>
- **Demo upload:** <attach the demo .webm as a comment? yes/no>
- **Running log conventions:** post **assumptions** (@-mention the issue owner), key **decisions**, and open **questions** as concise comments while working.
- **Handoff style:** <auto-commit-and-push  |  finish-in-worktree and wait for the user to push (e.g. labs env)>

## Recon notes (from onboarding)
<What the live tracker looked like: existing labels, sample issue style, board/project IDs, house conventions observed.>
