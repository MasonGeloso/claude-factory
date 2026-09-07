#!/usr/bin/env python3
"""Run one external review with isolated artifacts and a fail-closed result.

The command is an argv list, never a shell string. Use {output} where the configured CLI
writes its final response. Keep the returned task/session handle when running in background.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import tempfile
from datetime import datetime, timezone


def snapshot(worktree, inputs):
    def git(*args):
        return subprocess.check_output(["git", "-C", str(worktree), *args])

    return {
        "head": git("rev-parse", "HEAD").decode().strip(),
        "diff": hashlib.sha256(git("diff", "HEAD", "--binary")).hexdigest(),
        "inputs": {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},
    }


def run(args):
    worktree = Path(args.worktree).resolve()
    inputs = [Path(p).resolve() for p in args.input]
    before = snapshot(worktree, inputs)
    directory = Path(tempfile.mkdtemp(prefix=f"factory-{args.gate}-"))
    output = directory / "review.md"
    metadata = directory / "run.json"
    command = [part.replace("{output}", str(output)) for part in args.command]
    state = dict(gate=args.gate, subject=args.subject, worktree=str(worktree),
                 snapshot=before, status="running", pid=os.getpid(),
                 started_at=datetime.now(timezone.utc).isoformat())

    def save():
        temporary = directory / "run.json.tmp"
        temporary.write_text(json.dumps(state, indent=2) + "\n")
        temporary.replace(metadata)

    save()
    print(f"Review artifacts: {directory}", flush=True)
    proc = None

    def interrupt(signum, frame):
        if proc is not None and proc.poll() is None:
            os.killpg(proc.pid, signum)
        raise KeyboardInterrupt

    old_handlers = {sig: signal.signal(sig, interrupt) for sig in (signal.SIGTERM, signal.SIGINT)}
    try:
        with (directory / "process.log").open("w") as log:
            proc = subprocess.Popen(command, cwd=worktree, stdin=subprocess.DEVNULL,
                                    stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            state["child_pid"] = proc.pid
            save()
            code = proc.wait()
        state["exit_code"] = code
        if code:
            raise RuntimeError(f"reviewer exited {code}; inspect process.log")
        if snapshot(worktree, inputs) != before:
            raise RuntimeError("review inputs changed while the reviewer ran; run a fresh review")
        response = output.read_text().strip()
        verdicts = [line for line in response.splitlines() if line.startswith("VERDICT:")]
        if len(verdicts) != 1 or verdicts[0] not in ("VERDICT: PASS", "VERDICT: FAIL"):
            raise RuntimeError("expected exactly one standalone VERDICT: PASS or VERDICT: FAIL")
        state["status"] = verdicts[0].split(": ")[1].lower()
        print(response)
        return 0 if state["status"] == "pass" else 1
    except KeyboardInterrupt:
        if proc is not None and proc.poll() is None:
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.wait()
        state.update(status="interrupted", error="review interrupted; no verdict accepted")
        print(state["error"], flush=True)
        return 130
    except (OSError, RuntimeError, subprocess.CalledProcessError) as exc:
        state.update(status="error", error=str(exc))
        print(f"Review incomplete: {exc}", flush=True)
        return 2
    finally:
        state["finished_at"] = datetime.now(timezone.utc).isoformat()
        save()
        for sig, handler in old_handlers.items():
            signal.signal(sig, handler)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worktree", required=True)
    parser.add_argument("--gate", required=True, choices=["plan", "code", "qa"])
    parser.add_argument("--subject", required=True, help="issue/PR URL or task reference")
    parser.add_argument("--input", action="append", default=[], help="plan/QA report to fingerprint; repeatable")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if args.command[:1] == ["--"]:
        args.command.pop(0)
    if not args.command or not any("{output}" in part for part in args.command):
        parser.error("pass a reviewer command after -- with {output} for its response file")
    raise SystemExit(run(args))


if __name__ == "__main__":
    main()
