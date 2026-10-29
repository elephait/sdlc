from __future__ import annotations

import importlib.util
import json
import sqlite3
from contextlib import closing
import sys
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from support import make_workspace, remove_workspace  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]


def load_onboard_all():
    spec = importlib.util.spec_from_file_location(
        "onboard_all", ROOT / "scripts" / "onboard-all.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class OnboardAllTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = make_workspace("all")
        self.addCleanup(remove_workspace, self.root)
        self.db = self.root / "coordination.db"
        self.module = load_onboard_all()

    def project(self, name: str, tracked: bool = False) -> Path:
        path = self.root / name
        (path / ".git").mkdir(parents=True)
        if tracked:
            sdlc = path / ".sdlc"
            sdlc.mkdir()
            (sdlc / "active-story.json").write_text(
                json.dumps({"storyId": "TRACKED-001", "project": name}),
                encoding="utf-8",
            )
        return path

    def run_all(self, *extra: str) -> tuple[int, str]:
        output = StringIO()
        with redirect_stdout(output):
            code = self.module.main(
                ["--root", str(self.root), "--db", str(self.db), "--skip-refresh", *extra]
            )
        return code, output.getvalue()

    def test_untracked_project_is_tracked_and_existing_binding_is_preserved(self) -> None:
        tracked = self.project("tracked", tracked=True)
        before = (tracked / ".sdlc" / "active-story.json").read_bytes()
        fresh = self.project("fresh")

        code, output = self.run_all()
        self.assertEqual(0, code, output)
        self.assertIn("preserved  tracked", output)
        self.assertIn("added      fresh", output)
        self.assertEqual(before, (tracked / ".sdlc" / "active-story.json").read_bytes())

        binding = json.loads(
            (fresh / ".sdlc" / "active-story.json").read_text(encoding="utf-8")
        )
        self.assertEqual("FRESH-001", binding["storyId"])
        self.assertTrue(
            (self.root / ".sdlc-ledger" / "fresh" / "FRESH-001").is_dir()
        )

        with closing(sqlite3.connect(self.db)) as connection:
            stories = {
                row[0]
                for row in connection.execute("SELECT story_id FROM stories").fetchall()
            }
        self.assertEqual({"FRESH-001"}, stories)

    def test_second_run_changes_nothing(self) -> None:
        fresh = self.project("fresh")
        self.run_all()
        first = (fresh / ".sdlc" / "active-story.json").read_bytes()

        code, output = self.run_all()
        self.assertEqual(0, code, output)
        self.assertIn("preserved  fresh", output)
        self.assertEqual(first, (fresh / ".sdlc" / "active-story.json").read_bytes())

    def test_dry_run_writes_nothing(self) -> None:
        fresh = self.project("fresh")
        code, output = self.run_all("--dry-run")
        self.assertEqual(0, code, output)
        self.assertIn("would add  fresh", output)
        self.assertFalse((fresh / ".sdlc").exists())
        self.assertFalse((self.root / ".sdlc-ledger").exists())

    def test_dry_run_without_skip_refresh_never_runs_mutating_steps(self) -> None:
        fresh = self.project("fresh")
        with patch.object(self.module, "run") as run, \
                patch.object(self.module.subprocess, "run") as subprocess_run:
            with redirect_stdout(StringIO()):
                code = self.module.main(["--root", str(self.root), "--db", str(self.db),
                                         "--dry-run", "--reports", "5"])
        self.assertEqual(0, code)
        run.assert_not_called()
        # Only the read-only repository identity lookup is allowed.
        self.assertEqual(1, subprocess_run.call_count)
        self.assertEqual(["git", "-C", str(fresh), "remote", "get-url", "origin"],
                         subprocess_run.call_args.args[0])
        self.assertFalse(self.db.exists())
        self.assertFalse((fresh / ".sdlc").exists())

    def test_ledger_path_uses_the_workspace_scoped_root(self) -> None:
        self.project("fresh")
        self.run_all()
        project_yaml = (self.root / "fresh" / ".sdlc" / "project.yaml").read_text(
            encoding="utf-8"
        )
        self.assertIn(str(self.root / ".sdlc-ledger"), project_yaml)


if __name__ == "__main__":
    unittest.main()
