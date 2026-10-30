from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sqlite3
from contextlib import closing
import sys
import unittest

from copilot_customization.service import (
    commit_ready, onboard_project, record_gate, record_event, start_session,
)

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

    def test_onboarding_restores_active_story_from_project_config(self) -> None:
        first = self.onboard()
        active = self.workspace / ".sdlc" / "active-story.json"
        active.unlink()

        restored = onboard_project(self.workspace, db_path=self.db)

        self.assertEqual(first["storyId"], restored["storyId"])
        self.assertEqual("created", restored["status"]["activeStory"])
        self.assertTrue(active.is_file())

    def test_onboarding_detects_maven_validation_for_new_and_existing_config(self) -> None:
        first = self.onboard()
        project = self.workspace / ".sdlc" / "project.yaml"
        self.assertNotIn("validation:", project.read_text(encoding="utf-8"))
        (self.workspace / "pom.xml").write_text(
            "<project><properties><java.version>21</java.version></properties></project>",
            encoding="utf-8",
        )

        refreshed = self.onboard()
        text = project.read_text(encoding="utf-8")

        self.assertEqual("updated", refreshed["status"]["projectConfig"])
        self.assertIn("language: java", text)
        self.assertIn("javaVersion: '21'", text)
        self.assertIn("buildTool: maven", text)
        self.assertIn("command: mvn verify", text)

    def test_new_project_config_has_no_machine_specific_paths(self) -> None:
        self.onboard()
        text = (self.workspace / ".sdlc" / "project.yaml").read_text(encoding="utf-8")

        self.assertNotIn("workspaceRoot", text)
        self.assertNotIn("ledgerPath", text)
        self.assertNotIn(str(self.workspace), text)

    def test_onboarding_strips_machine_paths_from_existing_project_config(self) -> None:
        self.onboard()
        project = self.workspace / ".sdlc" / "project.yaml"
        project.write_text(
            project.read_text(encoding="utf-8").replace(
                "project: ", r"workspaceRoot: 'Z:\old\checkout'" + "\nproject: ", 1
            ) + r"  ledgerPath: 'Z:\old\ledger'" + "\n",
            encoding="utf-8",
        )

        refreshed = self.onboard()
        text = project.read_text(encoding="utf-8")

        self.assertEqual("updated", refreshed["status"]["projectConfig"])
        self.assertNotIn("workspaceRoot", text)
        self.assertNotIn("ledgerPath", text)
        self.assertIn("storyId: 'TEST-001'", text)
        self.assertEqual("preserved", self.onboard()["status"]["projectConfig"])

    def test_onboarding_rehomes_stale_active_story_ledger(self) -> None:
        first = self.onboard()
        active = self.workspace / ".sdlc" / "active-story.json"
        data = json.loads(active.read_text(encoding="utf-8"))
        data["ledgerPath"] = str(self.workspace.parent / "old-machine" / "ledger")
        active.write_text(json.dumps(data), encoding="utf-8")

        restored = self.onboard()

        self.assertEqual(first["ledgerPath"], restored["ledgerPath"])
        self.assertEqual(
            first["ledgerPath"],
            json.loads(active.read_text(encoding="utf-8"))["ledgerPath"],
        )

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

    def test_tracking_only_launcher_preserves_running_session_and_evidence(self) -> None:
        result = self.onboard(tracking_hooks="copilot-workspace")
        session = start_session("TEST-001", "implementation", None, "running-codex", self.db, host="codex")
        record_event("TEST-001", "validation", session_id=session, db_path=self.db)
        record_gate(self.workspace, "TEST-001", "analysis", evidence="fixture criteria",
                    approved_by="fixture user", db_path=self.db)
        ledger = Path(result["ledgerPath"])
        paths = [self.workspace / ".sdlc/active-story.json", self.workspace / ".sdlc/project.yaml",
                 self.workspace / ".github/hooks/copilot-sdlc.json",
                 self.workspace / ".sdlc/hooks/tracking_hook.py", ledger / "story.md", ledger / "gates/analysis.md"]
        before = {path: path.read_bytes() for path in paths}

        def rows():
            with closing(sqlite3.connect(self.db)) as connection:
                return {table: connection.execute(f"SELECT * FROM {table}").fetchall()
                        for table in ("stories", "sessions", "events", "gates")}

        def capture_hook():
            payload = {"cwd": str(self.workspace), "hook_event_name": "PostToolUse",
                       "session_id": session, "tool_name": "Read"}
            completed = subprocess.run(
                [sys.executable, str(self.workspace / ".sdlc/hooks/tracking_hook.py")],
                input=json.dumps(payload), capture_output=True, text=True)
            self.assertEqual(0, completed.returncode, completed.stderr)

        capture_hook()
        events_before = Path(result["eventPath"]).read_bytes()
        records_before = rows()
        completed = subprocess.run(
            [sys.executable, str(ROOT / "scripts/onboard.py"), "--workspace", str(self.workspace),
             "--db", str(self.db), "--skip-refresh"], cwd=self.workspace, capture_output=True, text=True)
        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertEqual(records_before, rows())
        self.assertEqual(before, {path: path.read_bytes() for path in paths})
        self.assertEqual(events_before, Path(result["eventPath"]).read_bytes())
        capture_hook()
        self.assertEqual(2, len(Path(result["eventPath"]).read_text().splitlines()))
        record_event("TEST-001", "validation", session_id=session, db_path=self.db)
        with closing(sqlite3.connect(self.db)) as connection:
            self.assertEqual((None, None), connection.execute(
                "SELECT ended_at, outcome FROM sessions WHERE session_id = ?", (session,)).fetchone())

    def test_codex_documented_validation_event_is_accepted(self) -> None:
        self.onboard()
        session = start_session("TEST-001", "implementation", None, None, self.db, host="codex")
        completed = subprocess.run(
            [sys.executable, str(ROOT / "scripts/sdlc.py"), "--db", str(self.db),
             "event", "--story", "TEST-001", "--session", session,
             "--type", "validation", "--tool", "verify.py"],
            cwd=self.workspace, capture_output=True, text=True)
        self.assertEqual(0, completed.returncode, completed.stderr)

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
