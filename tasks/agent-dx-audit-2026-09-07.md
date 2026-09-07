# Agent DX audit — 2026-09-07

Audited Factory at `ef857bf`, including the implement driver, plan/code/QA/recheck gates,
remember, onboarding, skill installation, scheduled-agent wrappers and a recent downstream task
sample. Downstream transcripts are private and are not reproduced here.

Recent improvements are material: plan-review (September 2), mandatory live QA (September 3), and
remember plus item-by-item checks (September 6). Older runs should not be counted as failures of new
gates. This patch retains those gates and fixes gaps around them.

| Finding | Change | Evidence/check |
|---|---|---|
| Review output and process handling are improvised at each gate | One bundled helper with exclusive artifact directory, task/revision record, child process ownership, input hashes and fail-closed exit handling | Real subprocess + temporary Git tests, including cancellation without killing unrelated processes |
| A verdict can outlive the input it reviewed | Reject changed local HEAD/diff and explicitly supplied plan/QA input; require driver comparison to remote PR SHA | Tests mutate HEAD and a plan while the child runs |
| Resumption has no concise durable task record | Driver records requirements, accepted corrections, phase, stack, evidence and reviewer task handle | Walkthrough: resume checks live state; a status question does not cancel the task |
| Paths assume a user-skill installation | Resolve loaded sibling paths; direct-file fallback when skill invocation is unavailable | Instructions support plugin and user copies without inventing missing skills |
| Cold plan reviewer can refuse a valid direct review or re-launch a reviewer | Driver owns invocation; invoked reviewer performs the review itself | Direct-file plan path now has no external-tool enablement precondition |
| QA examples assume every change needs an app/screenshot | Add appropriate CLI/failure/recovery and documentation walkthrough evidence | Gate remains mandatory; inapplicable rows require reasons |
| Remember can re-ask for commit authorization already given | Preserve existing session authorization | Diff-only remains the default when no commit/PR was requested |
| Dispatcher frontmatter is invalid YAML (`RESULT:` inside an unquoted scalar) | Quote the description without changing behavior | All 29 skill headers parse |

Validation: `python3 -m unittest discover -s tests -v`; YAML parse of all skill frontmatters;
review of relative links, changed instructions and diff whitespace. The Codex skill validator passes
implement/code-review/QA; its older key allowlist rejects the existing Claude-specific `user-invocable`
metadata on plan-review/remember. That metadata is preserved; both headers parse as valid YAML. Tests invoke synthetic reviewers,
not a paid model, and do not post to any tracker or change installed skills/scheduled jobs.

Adoption: update installed Factory skills, then wrap each project's existing configured review CLI
using `factory-code-review/references/review-runs.md`. The helper does not choose models or permissions.
An exit-0 PASS only proves the run protocol; the driver must still assess findings, coverage, remote
revision and accessible QA evidence. It fingerprints tracked diff plus explicit input files, not remote
tracker contents or arbitrary untracked artifacts. Temp artifacts can be removed by OS cleanup;
retain final reports with the project's normal handoff artifacts.

Deferred: scheduler-wide overlap enforcement (the marketing lane already has account-lock rules),
atomic multi-process installed-agent manifest updates, and empirical measurements of reviewer cost
or defect escape rates after adoption. No claim of zero future agent errors or universal skill compliance.

## Follow-up: review value and repeated failures

A deeper downstream audit found both consequential defect discovery and avoidable review loops.
Recurring causes were incomplete cross-caller fixes, regressions introduced by local patches, plans
accumulating contradictory historical contracts, and full evidence refreshes after narrow changes.
Some final CLI responses were shorter than the posted report, so a verdict file alone is insufficient
feedback. This does not establish that lost feedback caused every repeated finding.

The review-run guide now adds stable finding IDs/dispositions, complete-report retrieval, closure via
real counterexamples, a change in repair strategy when the same root problem returns, and review-yield
timing/categories. Plan review distinguishes executable ambiguity from harmless prose cleanup and
keeps a single authoritative design. QA carries forward unaffected evidence only after a dependency
check. The blocking gate remains; no fixed round limit or automatic waiver was introduced.

Validation: walkthroughs against a repeated state-transition defect, a summary-only reviewer response,
a plan with a stale field-count sentence, and an artifact-only follow-up. Existing subprocess tests
remain applicable to the unchanged runner. These are instruction checks, not measured proof that future
agents will be faster; post-adoption outcomes need measurement.
