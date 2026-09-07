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
