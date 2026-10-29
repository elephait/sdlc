from __future__ import annotations

import sqlite3
import subprocess
import sys
import unittest
from contextlib import closing
from pathlib import Path

from copilot_customization.cli import brief_gates
from copilot_customization.db import database
from copilot_customization.service import (
    commit_ready,
    gates_for_story,
    onboard_project,
    record_gate,
    required_gates,
    run_verify,
    start_session,
    stop_session,
)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from support import make_workspace, remove_workspace  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]


class GateWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.workspace = make_workspace("gate")
        self.addCleanup(remove_workspace, self.workspace)
        self.db = self.workspace / "coordination.db"
        onboard_project(
            self.workspace,
            project="fixture",
            repository="local/fixture",
            story_id="TEST-001",
            intent="Exercise handoff gates",
            ledger_root=self.workspace / "ledger",
            db_path=self.db,
        )
        self.git("init")
        self.git("config", "user.name", "SDLC fixture")
        self.git("config", "user.email", "fixture@example.invalid")
        self.write("README.md", "# Fixture\n")
        self.write("analysis.md", "# Analysis\n\nCriteria accepted.\n")
        self.git("add", "README.md")

    def git(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["git", "-C", str(self.workspace), *args],
            capture_output=True,
            text=True,
            check=True,
        )

    def write(self, name: str, text: str) -> None:
        (self.workspace / name).write_text(text, encoding="utf-8")

    def gate(self, name: str, **overrides):
        payload = dict(
            workspace=self.workspace,
            story_id="TEST-001",
            gate=name,
            status="passed",
            evidence="Checked in the fixture",
            approved_by="fixture user",
            db_path=self.db,
        )
        payload.update(overrides)
        return record_gate(**payload)

    def test_implementation_commit_requires_analysis_and_implementation(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            r"analysis \(missing\), implementation \(missing\)",
        ):
            commit_ready(self.workspace, "ai commit: first", "test", "summary", [], self.db)

        with self.assertRaisesRegex(ValueError, "requires --evidence"):
            self.gate("analysis", evidence="")
        with self.assertRaisesRegex(ValueError, "requires --approved-by"):
            self.gate("analysis", approved_by="")

        self.gate("analysis", artifact="analysis.md")
        self.gate("implementation", evidence="python scripts/verify.py passed")
        result = commit_ready(
            self.workspace, "ai commit: first", "test", "summary", [], self.db
        )
        self.assertEqual("ai commit by test: first", result["title"])
        self.assertEqual(
            "ai commit by test: first",
            self.git("log", "-1", "--format=%s").stdout.strip(),
        )
        self.assertEqual(
            {"analysis": "passed", "implementation": "passed"}, result["gates"]
        )
        self.assertEqual(
            {"analysis": "passed", "implementation": "passed"},
            result["analysis"]["gates"],
        )
        self.assertEqual(
            {"analysis": "passed", "implementation": "passed"},
            result["analysis"]["handoff"]["gates"],
        )
        self.assertTrue(
            any(
                "telemetry" in finding
                for finding in result["analysis"]["importantFindings"]
            )
        )
        self.assertEqual(2, len(gates_for_story("TEST-001", self.db)))

    def test_review_commit_requires_review_and_docs(self) -> None:
        for name in ("analysis", "implementation"):
            self.gate(name)
        commit_ready(self.workspace, "ai commit: first", "test", "summary", [], self.db)

        self.write("README.md", "# Fixture\n\nRefined.\n")
        self.git("add", "README.md")
        with self.assertRaisesRegex(
            ValueError, r"docs \(missing\), review \(missing\)"
        ):
            commit_ready(
                self.workspace, "ai code review: close", "test", "summary", [], self.db
            )

        review = self.workspace / ".sdlc" / "review.md"
        review.parent.mkdir(parents=True, exist_ok=True)
        review.write_text("# Review\n\nNo actionable findings.\n", encoding="utf-8")
        self.gate("review", artifact=".sdlc/review.md")
        self.gate("docs", artifact="README.md")
        result = commit_ready(
            self.workspace, "ai code review: close", "test", "summary", [], self.db
        )
        self.assertEqual({"docs": "passed", "review": "passed"}, result["gates"])

    def test_telemetry_finding_is_repeated_while_still_unmeasured(self) -> None:
        for name in ("analysis", "implementation"):
            self.gate(name)
        commit_ready(self.workspace, "ai commit: first", "test", "summary", [], self.db)
        self.write("README.md", "# Fixture\n\nRefined.\n")
        self.git("add", "README.md")
        self.write(".sdlc/review.md", "# Review\n")
        self.gate("review", artifact=".sdlc/review.md")
        self.gate("docs", artifact="README.md")
        second = commit_ready(
            self.workspace, "ai code review: close", "test", "summary", [], self.db
        )
        self.assertTrue(
            any("telemetry" in f for f in second["analysis"]["importantFindings"])
        )

    def test_run_verify_pins_the_staged_tree(self) -> None:
        scripts_dir = self.workspace / "scripts"
        scripts_dir.mkdir()
        (scripts_dir / "verify.py").write_text("print('Ran 3 tests')\n", encoding="utf-8")
        result = run_verify(self.workspace)
        tree = self.git("write-tree").stdout.strip()
        self.assertEqual(tree, result["treeHash"])
        self.git("add", "analysis.md")
        with self.assertRaisesRegex(ValueError, "staged tree changed after verify"):
            self.gate("implementation", details={"verification": result})

    def test_gate_status_display_drops_the_output_tail(self) -> None:
        self.gate(
            "implementation",
            details={"verification": {"result": "passed", "outputTail": "x\n" * 40}},
        )
        shown = brief_gates(gates_for_story("TEST-001", self.db))["implementation"]
        self.assertNotIn("outputTail", shown["details_json"])
        self.assertIn("passed", shown["details_json"])

    def test_customization_change_requires_customization_gate(self) -> None:
        (self.workspace / "policy").mkdir()
        self.write("policy/rule.md", "changed\n")
        self.git("add", "policy/rule.md")
        staged = ["README.md", "policy/rule.md"]
        self.assertEqual(
            ["analysis", "customization", "implementation"],
            required_gates("ai commit: change", staged),
        )

        for name in ("analysis", "implementation"):
            self.gate(name)
        with self.assertRaisesRegex(ValueError, "customization \\(missing\\)"):
            commit_ready(self.workspace, "ai commit: change", "test", "summary", [], self.db)

        self.gate("customization", evidence="sync and verify passed")
        result = commit_ready(
            self.workspace, "ai commit: change", "test", "summary", [], self.db
        )
        self.assertEqual("passed", result["gates"]["customization"])

    def test_generated_skill_dot_prefixed_and_launcher_paths_require_customization(self) -> None:
        self.assertEqual(
            ["analysis", "customization", "implementation"],
            required_gates(
                "ai commit: skills",
                [
                    ".agents/skills/tracked-story/SKILL.md",
                    "./core/a.py",
                    "scripts/onboard.py",
                    "aicode.cmd",
                ],
            ),
        )
        self.assertEqual(
            ["analysis", "implementation"],
            required_gates("ai commit: plain", ["README.md", "md/notes.md"]),
        )

    def test_waiver_counts_as_satisfied_and_is_recorded(self) -> None:
        self.gate(
            "analysis",
            status="waived",
            evidence="User accepted starting without written analysis",
        )
        self.gate("implementation")
        result = commit_ready(
            self.workspace, "ai commit: waived", "test", "summary", [], self.db
        )
        self.assertEqual("waived", result["gates"]["analysis"])

    def test_failed_gate_does_not_satisfy_commit(self) -> None:
        self.gate("analysis")
        self.gate("implementation", status="failed", evidence="verify.py failed")
        with self.assertRaisesRegex(ValueError, "implementation \\(failed\\)"):
            commit_ready(
                self.workspace, "ai commit: blocked", "test", "summary", [], self.db
            )

    def test_gate_rejects_unknown_name_and_missing_artifact(self) -> None:
        with self.assertRaisesRegex(ValueError, "Gate must be one of"):
            self.gate("deploy")
        with self.assertRaisesRegex(ValueError, "artifact was not found"):
            self.gate("analysis", artifact="missing.md")

    def test_gate_refuses_a_story_that_is_not_active(self) -> None:
        with self.assertRaisesRegex(ValueError, "not the active story"):
            self.gate("analysis", story_id="OTHER-001")

    def test_session_records_host_and_refuses_rewrite(self) -> None:
        session = start_session(
            "TEST-001", "implementation", "gpt-5-codex", None, self.db, host="codex"
        )
        with database(self.db) as connection:
            row = connection.execute(
                "SELECT host, outcome FROM sessions WHERE session_id = ?", (session,)
            ).fetchone()
        self.assertEqual("codex", row["host"])

        stop_session(session, "DONE", self.db)
        stop_session(session, "DONE", self.db)
        with self.assertRaisesRegex(ValueError, "already closed as DONE"):
            stop_session(session, "FAILED", self.db)
        with self.assertRaisesRegex(ValueError, "Outcome must be one of"):
            stop_session(session, "done-ish", self.db)

    def test_gate_report_is_written_under_the_ledger(self) -> None:
        record = self.gate("analysis", artifact="analysis.md")
        report = Path(record["report"])
        self.assertTrue(report.is_file())
        text = report.read_text(encoding="utf-8")
        self.assertIn('gate: "analysis"', text)
        self.assertIn('approvedBy: "fixture user"', text)
        self.assertEqual(64, len(record["artifactSha256"]))

    def test_gates_go_stale_after_a_commit(self) -> None:
        self.gate("analysis")
        self.gate("implementation")
        commit_ready(self.workspace, "ai commit: first", "test", "summary", [], self.db)

        self.write("README.md", "# Fixture\n\nSecond change.\n")
        self.git("add", "README.md")
        with self.assertRaisesRegex(
            ValueError, r"implementation \(stale: recorded for"
        ):
            commit_ready(
                self.workspace, "ai commit: second", "test", "summary", [], self.db
            )

        # Analysis is story-level: it stays valid without a re-record.
        self.gate("implementation")
        result = commit_ready(
            self.workspace, "ai commit: second", "test", "summary", [], self.db
        )
        self.assertEqual("passed", result["gates"]["implementation"])

    def test_staged_tree_change_invalidates_implementation_gate(self) -> None:
        self.gate("analysis")
        self.gate("implementation")
        self.write("extra.txt", "staged after the gate\n")
        self.git("add", "extra.txt")
        with self.assertRaisesRegex(
            ValueError, r"implementation \(stale: staged tree"
        ):
            commit_ready(
                self.workspace, "ai commit: tree", "test", "summary", [], self.db
            )

        self.gate("implementation")
        result = commit_ready(
            self.workspace, "ai commit: tree", "test", "summary", [], self.db
        )
        self.assertEqual("passed", result["gates"]["implementation"])

    def test_gate_writes_migrate_a_legacy_gates_table(self) -> None:
        with closing(sqlite3.connect(self.db)) as connection:
            connection.execute("ALTER TABLE gates DROP COLUMN head_commit")
            connection.execute("ALTER TABLE gates DROP COLUMN tree_hash")
            connection.commit()
        record = self.gate("implementation")
        self.assertRegex(record["treeHash"], r"^[0-9a-f]{40,64}$")
        stored = gates_for_story("TEST-001", self.db)["implementation"]
        self.assertEqual(record["treeHash"], stored["tree_hash"])

    def test_tree_bound_gate_report_records_the_staged_tree(self) -> None:
        record = self.gate("implementation")
        report = Path(record["report"]).read_text(encoding="utf-8")
        self.assertRegex(record["treeHash"], r"^[0-9a-f]{40,64}$")
        self.assertIn("treeHash:", report)
        self.assertNotIn("headCommit:", report)
        self.assertIsNone(self.gate("analysis", evidence="intent accepted")["treeHash"])

    def test_recorded_by_is_stored_separately_from_the_approver(self) -> None:
        record = self.gate("analysis", recorded_by="deepseek")
        self.assertEqual("deepseek", record["recordedBy"])
        report = Path(record["report"]).read_text(encoding="utf-8")
        self.assertIn('recordedBy: "deepseek"', report)
        stored = gates_for_story("TEST-001", self.db)["analysis"]
        self.assertEqual("deepseek", stored["recorded_by"])
        self.assertEqual("fixture user", stored["approved_by"])

    def test_verification_details_are_reported(self) -> None:
        record = self.gate(
            "implementation",
            details={
                "verification": {
                    "result": "passed",
                    "testCount": 7,
                    "exitCode": 0,
                }
            },
        )
        report = Path(record["report"]).read_text(encoding="utf-8")
        self.assertIn('verification: "passed (7 tests, exit 0)"', report)

    def test_run_verify_records_a_structured_result(self) -> None:
        scripts_dir = self.workspace / "scripts"
        scripts_dir.mkdir()
        (scripts_dir / "verify.py").write_text(
            "print('Ran 7 tests in 0.1s')\nprint('OK')\n", encoding="utf-8"
        )
        result = run_verify(self.workspace)
        self.assertEqual(0, result["exitCode"])
        self.assertEqual(7, result["testCount"])
        self.assertEqual("passed", result["result"])

    def test_run_verify_refuses_unstaged_changes(self) -> None:
        scripts_dir = self.workspace / "scripts"
        scripts_dir.mkdir()
        (scripts_dir / "verify.py").write_text("print('Ran 1 test')\n", encoding="utf-8")
        self.write("README.md", "# Worktree only\n")
        with self.assertRaisesRegex(ValueError, "unstaged changes"):
            run_verify(self.workspace)


if __name__ == "__main__":
    unittest.main()
