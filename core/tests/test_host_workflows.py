from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import unittest

from copilot_customization.service import commit_ready, onboard_project, record_gate

sys.path.insert(0, str(Path(__file__).resolve().parent))
from support import make_workspace, remove_workspace  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]


class HostWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        # Under the authorized Windows workspace; never use the real ledger/DB.
        self.workspace = make_workspace("host")
        self.addCleanup(remove_workspace, self.workspace)
        self.db = self.workspace / "coordination.db"

    def onboard(self, **kwargs):
        return onboard_project(
            self.workspace, project="fixture", repository="local/fixture",
            story_id="TEST-001", intent="Exercise host integration",
            ledger_root=self.workspace / "ledger", db_path=self.db, **kwargs,
        )

    def test_onboarding_is_host_neutral_and_workspace_hooks_are_opt_in(self) -> None:
        first = self.onboard()
        self.assertFalse((self.workspace / ".github").exists())
        self.assertEqual("not-installed", first["status"]["trackingHooks"])
        installed = self.onboard(tracking_hooks="copilot-workspace")
        self.assertEqual(first["ledgerPath"], installed["ledgerPath"])
        hook = self.workspace / ".github/hooks/copilot-sdlc.json"
        before = hook.read_bytes()
        config = json.loads(before)
        self.assertIn("PostToolUseFailure", config["hooks"])
        self.onboard()
        self.assertEqual(before, hook.read_bytes())

    def test_cli_and_hook_run_with_isolated_tracking_from_another_cwd(self) -> None:
        result = self.onboard()
        session = subprocess.run(
            [sys.executable, str(ROOT / "scripts/sdlc.py"), "--db", str(self.db),
             "session-start", "--story", "TEST-001", "--role", "implementation",
             "--session-id", "fixture-session"],
            cwd=self.workspace, capture_output=True, text=True,
        )
        self.assertEqual(0, session.returncode, session.stderr)
        payload = {"cwd": str(self.workspace), "hook_event_name": "PostToolUseFailure",
                   "session_id": "fixture-session", "tool_name": "Bash", "error": "fixture failure"}
        hook = subprocess.run(
            [sys.executable, str(ROOT / "core/scripts/tracking_hook.py")],
            input=json.dumps(payload), cwd=self.workspace, capture_output=True, text=True,
        )
        self.assertEqual(0, hook.returncode, hook.stderr)
        events = Path(result["eventPath"]).read_text().splitlines()
        self.assertEqual(1, len(events))
        self.assertFalse(json.loads(events[0])["success"])

    def test_commit_workflow_respects_required_git_signing(self) -> None:
        self.onboard()

        def git(*args):
            return subprocess.run(["git", "-C", str(self.workspace), *args],
                                  capture_output=True, text=True, check=True)

        git("init")
        git("config", "user.name", "SDLC fixture")
        git("config", "user.email", "fixture@example.invalid")
        git("config", "commit.gpgsign", "true")
        git("config", "gpg.format", "openpgp")
        git("config", "gpg.program", "sdlc-intentionally-missing-signing-program")
        (self.workspace / "README.md").write_text("# Fixture\n")
        git("add", "README.md")
        for gate in ("analysis", "implementation"):
            record_gate(
                workspace=self.workspace,
                story_id="TEST-001",
                gate=gate,
                evidence="fixture validation",
                approved_by="fixture user",
                db_path=self.db,
            )
        with self.assertRaisesRegex(ValueError, "(?i)(sign|gpg)"):
            commit_ready(self.workspace, "ai commit: fixture", "test", "fixture", [], self.db)
        head = subprocess.run(["git", "-C", str(self.workspace), "rev-parse", "--verify", "HEAD"],
                              capture_output=True)
        self.assertNotEqual(0, head.returncode)


if __name__ == "__main__":
    unittest.main()
