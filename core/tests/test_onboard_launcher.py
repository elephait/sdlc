from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
import unittest
from contextlib import redirect_stdout, redirect_stderr
from io import StringIO
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("onboard_launcher", ROOT / "scripts/onboard.py")
launcher = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(launcher)


class OnboardLauncherTests(unittest.TestCase):
    def test_refresh_validates_before_tracking_and_preserves_binding(self):
        with patch.object(launcher.subprocess, "run", return_value=subprocess.CompletedProcess([], 0)) as run:
            with redirect_stdout(StringIO()):
                self.assertEqual(0, launcher.main([]))
        self.assertEqual(["scripts/sync-customizations.py", "scripts/verify.py", "scripts/sdlc.py"],
                         [call.args[0][1] for call in run.call_args_list])
        self.assertNotIn("--story", run.call_args_list[-1].args[0])
        self.assertTrue(all(call.kwargs["cwd"] == ROOT for call in run.call_args_list))

    def test_failure_stops_before_tracking_and_propagates_exit_code(self):
        results = [subprocess.CompletedProcess([], 0), subprocess.CompletedProcess([], 7)]
        with patch.object(launcher.subprocess, "run", side_effect=results) as run:
            with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
                self.assertEqual(7, launcher.main([]))
        self.assertEqual(2, run.call_count)


if __name__ == "__main__":
    unittest.main()
