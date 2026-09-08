---
name: factory-weekly-rule-audit
description: Review the past week's coding-agent conversations and outcomes, then write a Markdown proposal to simplify or improve agent rules. Use for weekly failure retrospectives and rule audits, not project status reports or individual code reviews.
---

# Weekly rule audit

Find preventable failures and reduce instruction clutter. Produce proposals for owner review;
do not apply rule changes or schedule recurring runs unless requested.

## Review the week

1. Use the requested repo(s), timezone and dates; default to the past seven days in the user's
   timezone. Record exact boundaries and read the previous report to avoid repeating proposals.
2. Find relevant conversations in available session stores or supplied exports. Common local sources
   are `~/.claude/projects/` and `${CODEX_HOME:-~/.codex}/sessions/`. Match repository metadata and
   event timestamps; file modification time alone does not establish scope. Report access gaps.
3. Inventory the window, then investigate corrections, repeated repairs, failed commands, review
   loops and post-merge fixes. Read surrounding conversation and tool results, including reviewer
   feedback and the agent's response. Follow linked issues/diffs when needed to verify the outcome.
   Report what was inventoried versus deeply reviewed; do not claim exhaustive coverage from searches.
4. Group incidents by root cause. Distinguish missing guidance, ignored or conflicting guidance,
   missing feedback, tooling defects and changed requirements. Separate shipped failures from
   pre-release catches. Count actual review runs, not log mentions; infer no speedup from raw counts.
5. Read the applicable rules, skills and checklists, including the version used during the incident
   when available. Check whether previous proposals were adopted and whether the problem recurred;
   no observed recurrence alone is not proof a rule worked.

## Propose less, better guidance

- Prefer **keep, shorten, merge or remove** before adding. No quota; zero changes is a valid result.
- Add a rule only for a recurring pattern or one consequential failure with a clear preventive check.
- Write one short imperative per rule, at most two sentences. Keep incident stories in the report.
- Show how the check would catch the failure and one legitimate case it should allow.
- Put guidance where the agent first needs it; reference one authoritative rule instead of copying it
  across gates. Preserve distinct obligations when consolidating.
- If a rule already covers the failure, investigate why it was missed. Propose a workflow/tool fix
  when appropriate rather than another warning. Do not add review gates by default.

## Write the review file

Save `tasks/weekly-rule-audit/YYYY-MM-DD.md` in the audited repo unless another location was requested.
Keep the summary skimmable; put supporting evidence below it. For multi-repo audits, keep private
conversation evidence in a private destination, not a public rules repository. Redact secrets and
unnecessary personal details; cite session IDs/timestamps or PR links rather than dumping transcripts.

Use this shape, omitting empty sections:

- **Window and coverage:** dates/timezone, sources, inventoried/deeply reviewed counts and gaps.
- **Weekly finding:** the main failure pattern and any evidence that existing rules helped.
- **Proposed edits:** for each, action + target file/section, exact current and proposed wording
  (all source bullets for a merge), brief rationale, evidence pointer, and preventive/allowed cases.
- **Rule budget:** affected rule count and word count before → after; explain any net growth.
- **No rule change:** important incidents already covered, tooling fixes, rejected ideas or unknowns.
- **Previous proposals:** adopted/pending/rejected status and follow-up evidence, when available.

Finish by linking the file and naming the few decisions needed. Applying proposals is a separate
step governed by the user's authorization; the weekly audit itself produces only the review file.
