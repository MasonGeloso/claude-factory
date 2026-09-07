"""Exercise real child processes and Git changes, without invoking a paid reviewer."""
import json
import os
import shutil
import signal
import time
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

RUNNER = Path(__file__).resolve().parents[1] / "skills/factory-code-review/scripts/run_review.py"


class ReviewRunnerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        for args in (["init", "-q"], ["config", "user.email", "test@example.com"],
                     ["config", "user.name", "Test"], ["commit", "--allow-empty", "-qm", "initial"]):
            subprocess.run(["git", "-C", str(self.repo), *args], check=True)

    def run_review(self, response="VERDICT: PASS", extra="", inputs=()):
        cmd = [sys.executable, str(RUNNER), "--worktree", str(self.repo), "--gate", "code", "--subject", "test"]
        for path in inputs:
            cmd += ["--input", str(path)]
        cmd += ["--", sys.executable, "-c",
                "from pathlib import Path; import sys,subprocess; "
                f"Path(sys.argv[1]).write_text({response!r}); " + extra, "{output}"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        directory = Path(result.stdout.splitlines()[0].removeprefix("Review artifacts: "))
        state = json.loads((directory / "run.json").read_text())
        self.addCleanup(shutil.rmtree, directory)
        return result.returncode, state, directory

    def test_each_run_owns_its_output(self):
        first = self.run_review()
        second = self.run_review()
        self.assertEqual(first[0], 0)
        self.assertEqual(first[1]["status"], "pass")
        self.assertNotEqual(first[2], second[2])

    def test_fail_and_invalid_outputs_never_pass(self):
        for response, expected in [("VERDICT: FAIL", 1), ("", 2), ("PASS", 2),
                                   ("VERDICT: PASS\nVERDICT: FAIL", 2), ("VERDICT: PASS maybe", 2)]:
            with self.subTest(response=response):
                self.assertEqual(self.run_review(response)[0], expected)

    def test_process_failure_overrides_written_pass(self):
        code, state, _ = self.run_review(extra="sys.exit(9)")
        self.assertEqual(code, 2)
        self.assertEqual(state["exit_code"], 9)

    def test_missing_output_never_passes(self):
        code, state, _ = self.run_review(extra="Path(sys.argv[1]).unlink()")
        self.assertEqual(code, 2)
        self.assertEqual(state["status"], "error")

    def test_interruption_only_stops_owned_child(self):
        unrelated = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
        self.addCleanup(unrelated.wait)
        self.addCleanup(unrelated.terminate)
        cmd = [sys.executable, str(RUNNER), "--worktree", str(self.repo), "--gate", "qa",
               "--subject", "test", "--", sys.executable, "-c", "import time; time.sleep(30)", "{output}"]
        with subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) as proc:
            directory = Path(proc.stdout.readline().strip().removeprefix("Review artifacts: "))
            self.addCleanup(shutil.rmtree, directory)
            deadline = time.monotonic() + 5
            while time.monotonic() < deadline:
                state = json.loads((directory / "run.json").read_text())
                if state.get("child_pid"):
                    break
                time.sleep(0.01)
            else:
                self.fail("child did not start")
            proc.send_signal(signal.SIGTERM)
            proc.communicate(timeout=10)
            self.assertEqual(proc.returncode, 130)
            self.assertEqual(json.loads((directory / "run.json").read_text())["status"], "interrupted")
            self.assertIsNone(unrelated.poll())
            with self.assertRaises(ProcessLookupError):
                os.kill(state["child_pid"], 0)

    def test_changed_head_invalidates_pass(self):
        code, state, _ = self.run_review(extra="subprocess.run(['git','commit','--allow-empty','-qm','changed'],check=True)")
        self.assertEqual(code, 2)
        self.assertIn("inputs changed", state["error"])

    def test_changed_plan_invalidates_pass(self):
        plan = self.repo / "plan.md"
        plan.write_text("original")
        code, state, _ = self.run_review(extra="Path('plan.md').write_text('revised')", inputs=[plan])
        self.assertEqual(code, 2)
        self.assertIn("inputs changed", state["error"])


if __name__ == "__main__":
    unittest.main()
