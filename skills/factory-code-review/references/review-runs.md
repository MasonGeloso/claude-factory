# Running external review gates

Use this for plan review, code review and QA's second opinion. The project owns the reviewer
command in `factory/code-review.md`; resolve the actual loaded Factory skill directory first.
User-skill installs and plugin installs have different paths. Pass absolute paths to the reviewer.

## One invocation, one result

Run the bundled helper with the project's configured command as argv after `--`. Substitute
`{output}` for that CLI's response-file argument (do not keep a shared `/tmp/factory_*_review.txt`).
For example, with a CLI that accepts `-o`:

```bash
python3 <factory-code-review-dir>/scripts/run_review.py \
  --worktree <absolute-worktree> --gate code --subject <PR_URL> \
  -- <configured-reviewer> <configured-flags> -o '{output}' \
  'Read <absolute-skill-path> and review <PR_URL>. End with one standalone VERDICT: PASS or VERDICT: FAIL.'
```

For plan review add `--input <absolute-plan-file>`; for QA add `--input <absolute-QA-report>`
and repeat for local evidence files. The helper records the task, HEAD and input hashes, creates
an exclusive temporary directory, detaches stdin, captures process logs, and accepts a verdict
only after successful process exit with unchanged inputs. Exit 0 = PASS, 1 = FAIL, 2 = incomplete
or invalid run, 130 = interrupted. It does not prove the review's reasoning or artifact coverage;
the driver must read the result. It fingerprints tracked changes plus explicit inputs, so include
any untracked input the reviewer needs. Before and after review, also verify the remote PR head
matches the local HEAD; the helper does not query the tracker or fetch remote evidence.

## Wait and recover

- Keep the tool's task/session handle and the printed artifact directory in the task's run record.
  Poll that handle; a missing verdict file is normal while the reviewer runs. File age, a quiet log,
  and an observation timeout do not establish that the process stopped.
- After interruption or compaction, inspect that handle and the recorded process identity before
  restarting. `run.json` records intent and result; a `running` label alone is not proof of liveness.
  Check the process command/start time if the original tool handle is unavailable; PIDs can be reused.
- Never use `pkill -f codex`, `pgrep ... | head -1`, or a shared output filename to control a run.
  Cancel only this invocation through its task handle (or a verified owned PID). The helper forwards
  termination to its own child process group and records interruption.
- An unavailable tool, quota failure, nonzero exit, missing/ambiguous verdict or stale HEAD leaves
  the gate incomplete. Diagnose the recorded error once; use an alternative only if the user or
  project already authorizes it. Continue independent work while an external dependency is blocked.
- A FAIL needs specific findings: reproduce/verify them, fix accepted findings, and rerun affected
  checks. If a finding is mistaken, give the reviewer the evidence and ask it to reassess. Repeating
  the same review without new evidence or changes is not progress.

Keep the final output's single verdict line exact. Explanations may follow it; do not add a second
verdict when discussing a previous round. The reviewer should identify the reviewed commit (or plan
hash) and distinguish blocking defects from optional improvements outside the requested scope.

## Make each round earn its cost

A review count is not a quality metric. Keep the blocking gate, but distinguish new defects from
incomplete fixes, regressions introduced by fixes, changed requirements, and evidence-only work.
Use the local run record for a finding register:

| ID / root problem | Origin + reviewed revision | Impact / counterexample | Disposition | Fix + verification | Next review result |
|---|---|---|---|---|---|
| stable ID retained across rounds | report path/comment + SHA | concrete failing behavior | open / fixed-pending-review / disputed / closed / authorized-deferred | commit + meaningful check | closed / incomplete / regression / new |

- **Receive the whole report.** Read the complete findings, not `grep VERDICT`, a `head`/`tail`, or a
  count of red checklist rows (several rows can describe one defect). If the CLI prints only a summary
  or comment link, fetch that exact full comment. Compare the received findings to the source report;
  a truncated output is not a complete repair list. Keep all open IDs in the next review request.
- **Close with behavior.** A fix is pending until its counterexample passes through the real caller,
  producer/consumer contract or equivalent meaningful test. Check adjacent callers and failure paths
  before resubmitting; test doubles must reject the same invalid calls as the real boundary. A test
  with invented IDs, direct helper calls or omitted projections may bypass the defect entirely.
- **Change approach when the same root problem returns.** Do not just patch the next cited line.
  Map the relevant state transitions/callers, identify the shared rule, and fix that rule centrally.
  Replay all earlier counterexamples for that root problem, plus the boundary the latest patch changed.
  Continue the task; this is a change in repair strategy, not permission to skip the gate or stop.
- **Give the reviewer the repair evidence.** Supply the prior findings, dispositions, current delta,
  superseding owner decisions and test results. Ask it to mark each previous ID closed or still open,
  distinguish a new regression from an incomplete fix, and collect all independently verified findings
  from its sweep before returning. Do not drip-feed one already-known finding per invocation.
- **Tie blockers to consequences.** State the violated requirement and concrete user/operational harm.
  Cosmetic wording, redundant counts and optional redesigns are warnings unless they change the
  executable contract, invalidate necessary evidence or violate an explicit requirement. Disputed
  findings need evidence-based reassessment; neither automatic acceptance nor silent dismissal.
- **Retest evidence according to what changed.** A changed component/shared dependency needs fresh
  evidence for affected scenarios. An unrelated docs or artifact-only commit does not make every
  prior screenshot false. Carry forward each scenario's tested revision with a checked dependency
  delta; if the affected set is uncertain, run the broader check. Validate changed evidence and its
  provenance without inventing a need to redesign already-verified code.

Record each invocation's elapsed time and numbers of new, incomplete, regressed, disputed and closed
findings. Keep plan, code and QA rounds separate. Review-loop elapsed time includes repairs and waits;
it is not reviewer runtime or proof of a causal slowdown. There is no arbitrary round limit: real
remaining defects stay blocking, while repeated root problems require a better repair method.
