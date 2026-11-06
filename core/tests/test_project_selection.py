from __future__ import annotations

import sys
import unittest
from pathlib import Path

from copilot_customization.service import (
    recent_project_folders,
    record_project_use,
    select_project_folder,
)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from support import make_workspace, remove_workspace  # noqa: E402


class ProjectSelectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = make_workspace("selection")
        self.addCleanup(remove_workspace, self.root)
        self.db = self.root / "coordination.db"

    def test_recent_projects_are_limited_to_ten_and_newest_is_default(self) -> None:
        projects = []
        for index in range(12):
            project = self.root / f"project-{index:02d}"
            project.mkdir()
            record_project_use(project, self.db)
            projects.append(project.resolve())

        recent = recent_project_folders([], self.db)

        self.assertEqual(10, len(recent))
        self.assertEqual(projects[-1], recent[0])
        self.assertNotIn(projects[0], recent)

    def test_current_folder_is_default_when_no_project_was_onboarded(self) -> None:
        current = self.root / "current"
        current.mkdir()
        output = []

        selected = select_project_folder(
            self.db,
            current_folder=current,
            input_fn=lambda _: "",
            output_fn=output.append,
        )

        self.assertEqual(current.resolve(), selected)
        self.assertTrue(any("No previously onboarded projects" in line for line in output))

    def test_current_folder_is_option_two_when_most_recent_is_different(self) -> None:
        current = self.root / "current"
        current.mkdir()
        older = self.root / "older"
        older.mkdir()
        newest = self.root / "newest"
        newest.mkdir()
        record_project_use(older, self.db)
        record_project_use(newest, self.db)
        output = []

        selected = select_project_folder(
            self.db,
            current_folder=current,
            input_fn=lambda _: "2",
            output_fn=output.append,
        )

        self.assertEqual(current.resolve(), selected)
        self.assertIn(f"  1. {newest.resolve()} [default]", output)
        self.assertIn(f"  2. {current.resolve()} [current]", output)
        self.assertIn(f"  3. {older.resolve()}", output)
        self.assertIn("  Or enter a project directory path.", output)

    def test_current_folder_is_not_duplicated_when_it_is_most_recent(self) -> None:
        older = self.root / "older"
        older.mkdir()
        current = self.root / "current"
        current.mkdir()
        record_project_use(older, self.db)
        record_project_use(current, self.db)
        output = []

        selected = select_project_folder(
            self.db,
            current_folder=current,
            input_fn=lambda _: "2",
            output_fn=output.append,
        )

        self.assertEqual(older.resolve(), selected)
        self.assertIn(f"  1. {current.resolve()} [default, current]", output)
        self.assertIn(f"  2. {older.resolve()}", output)

    def test_user_can_enter_an_unlisted_directory(self) -> None:
        current = self.root / "current"
        current.mkdir()
        recent = self.root / "recent"
        recent.mkdir()
        entered = self.root / "entered"
        entered.mkdir()
        record_project_use(recent, self.db)

        selected = select_project_folder(
            self.db,
            current_folder=current,
            input_fn=lambda _: str(entered),
            output_fn=lambda _: None,
        )

        self.assertEqual(entered.resolve(), selected)


if __name__ == "__main__":
    unittest.main()
