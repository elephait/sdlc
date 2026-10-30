from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from copilot_customization import db

sys.path.insert(0, str(Path(__file__).resolve().parent))
from support import make_workspace, remove_workspace  # noqa: E402


class DatabaseBoundaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = make_workspace("db-boundary")
        self.addCleanup(remove_workspace, self.root)
        self.workspace = self.root / "workspace"
        self.workspace.mkdir()

    def test_default_database_is_allowed_with_a_separate_workspace_root(self) -> None:
        with patch.object(db, "DEV_ROOT", self.workspace.resolve()):
            self.assertEqual(
                db.DEFAULT_DB.resolve(),
                db.require_under_dev(db.DEFAULT_DB, "Database"),
            )

    def test_workspace_path_is_allowed(self) -> None:
        candidate = self.workspace / "data" / "workspace.db"

        with patch.object(db, "DEV_ROOT", self.workspace.resolve()):
            self.assertEqual(candidate.resolve(), db.require_under_dev(candidate, "Database"))

    def test_path_outside_project_and_workspace_is_rejected(self) -> None:
        candidate = self.root / "outside.db"

        with patch.object(db, "DEV_ROOT", self.workspace.resolve()):
            with self.assertRaisesRegex(
                ValueError,
                "SDLC project root or SDLC_WORKSPACE_ROOT",
            ):
                db.require_under_dev(candidate, "Database")

    def test_paths_are_not_confined_without_a_configured_workspace_root(self) -> None:
        candidate = self.root / "outside.db"

        with patch.object(db, "DEV_ROOT", None):
            self.assertEqual(
                candidate.resolve(),
                db.require_under_dev(candidate, "Database"),
            )


if __name__ == "__main__":
    unittest.main()
