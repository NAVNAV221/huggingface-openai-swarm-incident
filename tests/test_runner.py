import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]


class RunnerSafetyTests(unittest.TestCase):
    def test_scored_run_is_forbidden_on_local_proxy(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "runner/run.py"), "--run-id", "never-start", "--condition", "treatment", "--scored"],
            cwd=ROOT, text=True, capture_output=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("scored runs are forbidden", result.stderr)
        self.assertFalse((ROOT / "telemetry/runs/never-start/agents").exists())


if __name__ == "__main__":
    unittest.main()
