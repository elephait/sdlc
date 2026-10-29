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
                self.assertEqual(0, launcher.main(["--workspace", str(ROOT)]))
        self.assertEqual(["scripts/sync-customizations.py", "scripts/verify.py", "scripts/sdlc.py"],
                         [call.args[0][1] for call in run.call_args_list])
        self.assertNotIn("--story", run.call_args_list[-1].args[0])
        self.assertTrue(all(call.kwargs["cwd"] == ROOT for call in run.call_args_list))

    def test_failure_stops_before_tracking_and_propagates_exit_code(self):
        results = [subprocess.CompletedProcess([], 0), subprocess.CompletedProcess([], 7)]
        with patch.object(launcher.subprocess, "run", side_effect=results) as run:
            with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
                self.assertEqual(7, launcher.main(["--workspace", str(ROOT)]))
        self.assertEqual(2, run.call_count)

    def test_without_workspace_the_project_is_chosen_before_any_step(self):
        chosen = ROOT.parent / "other-project"
        ok = subprocess.CompletedProcess([], 0)
        with patch.object(launcher, "select_project_folder", return_value=chosen) as select, \
                patch.object(launcher.sys.stdin, "isatty", return_value=True), \
                patch.object(launcher.subprocess, "run", return_value=ok) as run:
            with redirect_stdout(StringIO()):
                self.assertEqual(0, launcher.main([]))
        select.assert_called_once()
        tracking = run.call_args_list[-1].args[0]
        self.assertEqual(str(chosen), tracking[tracking.index("--workspace") + 1])
        # The SDLC-specific default intent is not applied to another project.
        self.assertNotIn("--intent", tracking)

    def test_explicit_workspace_skips_the_prompt_and_sdlc_gets_its_intent(self):
        ok = subprocess.CompletedProcess([], 0)
        with patch.object(launcher, "select_project_folder") as select, \
                patch.object(launcher.subprocess, "run", return_value=ok) as run:
            with redirect_stdout(StringIO()):
                self.assertEqual(0, launcher.main(["--workspace", str(ROOT)]))
        select.assert_not_called()
        self.assertIn(launcher.SDLC_INTENT, run.call_args_list[-1].args[0])

    def test_selection_error_stops_before_any_step(self):
        with patch.object(launcher, "select_project_folder", side_effect=ValueError("none")), \
                patch.object(launcher.sys.stdin, "isatty", return_value=True), \
                patch.object(launcher.subprocess, "run") as run:
            with redirect_stderr(StringIO()):
                self.assertEqual(1, launcher.main([]))
        run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
