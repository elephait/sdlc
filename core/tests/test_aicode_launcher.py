from __future__ import annotations

import importlib.util
from io import StringIO
from pathlib import Path
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "aicode_launcher", ROOT / "scripts" / "aicode.py"
)
launcher = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(launcher)


class AICodeLauncherTests(unittest.TestCase):
    @staticmethod
    def answers(*values: str):
        answers = iter(values)
        return lambda _: next(answers)

    def test_reports_without_count_defaults_to_five(self) -> None:
        with patch.object(launcher, "show_reports", return_value=0) as reports:
            self.assertEqual(0, launcher.main(["--reports"]))
        reports.assert_called_once_with(5)

    def test_reports_accepts_an_explicit_count(self) -> None:
        with patch.object(launcher, "show_reports", return_value=0) as reports:
            self.assertEqual(0, launcher.main(["--reports", "12"]))
        reports.assert_called_once_with(12)

    def test_menu_maps_latest_all_reports_and_recent_projects(self) -> None:
        recent = [ROOT.parent / f"project-{index}" for index in range(1, 10)]
        expected = {
            "1": recent[0],
            "3": recent[1],
            "10": recent[8],
        }
        for selection, project in expected.items():
            with self.subTest(selection=selection), \
                    patch.object(launcher, "recent_project_folders", return_value=recent), \
                    patch.object(launcher, "current_git_root", return_value=ROOT), \
                    patch.object(launcher, "onboard_project", return_value=0) as onboard:
                self.assertEqual(
                    0,
                    launcher.interactive(
                        ROOT / "test.db",
                        input_fn=self.answers(selection, "E"),
                        output_fn=lambda _: None,
                    ),
                )
                onboard.assert_called_once_with(project, [])

        with patch.object(launcher, "recent_project_folders", return_value=recent), \
                patch.object(launcher, "current_git_root", return_value=ROOT), \
                patch.object(launcher, "show_reports", return_value=0) as reports:
            self.assertEqual(
                0,
                launcher.interactive(
                    ROOT / "test.db",
                    input_fn=self.answers("R 10", "E"),
                    output_fn=lambda _: None,
                ),
            )
            reports.assert_called_once_with(10)

        with patch.object(launcher, "recent_project_folders", return_value=recent), \
                patch.object(launcher, "current_git_root", return_value=ROOT), \
                patch.object(launcher, "onboard_all", return_value=0) as onboard_all, \
                patch.object(launcher.Path, "cwd", return_value=ROOT.parent):
            self.assertEqual(
                0,
                launcher.interactive(
                    ROOT / "test.db",
                    input_fn=self.answers("2", "E"),
                    output_fn=lambda _: None,
                ),
            )
            onboard_all.assert_called_once_with(ROOT.parent.resolve(), [])

    def test_menu_displays_the_requested_numbering(self) -> None:
        recent = [ROOT.parent / f"project-{index}" for index in range(1, 10)]
        output = StringIO()
        with patch.object(launcher, "recent_project_folders", return_value=recent), \
                patch.object(launcher, "current_git_root", return_value=ROOT), \
                patch.object(launcher, "onboard_project", return_value=0), \
                redirect_stdout(output):
            launcher.interactive(
                ROOT / "test.db",
                input_fn=self.answers("1", "E"),
            )
        menu = output.getvalue()
        self.assertIn("1. Onboard latest project", menu)
        self.assertIn("2. Onboard all Git projects", menu)
        self.assertIn("R. Show recent reports (default: 5); use R10 for 10", menu)
        self.assertIn("V. Verify the current Git project", menu)
        self.assertIn("Chain actions, for example: 1R10V or 1VR", menu)
        self.assertIn("3. Onboard recent project", menu)
        self.assertIn("10. Onboard recent project", menu)
        self.assertIn("E. End", menu)

    def test_end_option_exits_without_action(self) -> None:
        for selection in ("E", "e"):
            with self.subTest(selection=selection), \
                    patch.object(launcher, "recent_project_folders", return_value=[]), \
                    patch.object(launcher, "current_git_root", return_value=ROOT), \
                    patch.object(launcher, "onboard_project") as onboard, \
                    patch.object(launcher, "onboard_all") as onboard_all, \
                    patch.object(launcher, "show_reports") as reports:
                output = []
                self.assertEqual(
                    0,
                    launcher.interactive(
                        ROOT / "test.db",
                        input_fn=lambda _: selection,
                        output_fn=output.append,
                    ),
                )
                onboard.assert_not_called()
                onboard_all.assert_not_called()
                reports.assert_not_called()
                self.assertIn("Ended.", output)

    def test_first_run_uses_current_git_project_as_latest(self) -> None:
        current = ROOT.parent / "current"
        with patch.object(launcher, "recent_project_folders", return_value=[]), \
                patch.object(launcher, "current_git_root", return_value=current), \
                patch.object(launcher, "onboard_project", return_value=0) as onboard:
            self.assertEqual(
                0,
                launcher.interactive(
                    ROOT / "test.db",
                    input_fn=self.answers("", "E"),
                    output_fn=lambda _: None,
                ),
            )
        onboard.assert_called_once_with(current, [])

    def test_bare_report_selection_defaults_to_five(self) -> None:
        with patch.object(launcher, "recent_project_folders", return_value=[]), \
                patch.object(launcher, "current_git_root", return_value=ROOT), \
                patch.object(launcher, "show_reports", return_value=0) as reports:
            self.assertEqual(
                0,
                launcher.interactive(
                    ROOT / "test.db",
                    input_fn=self.answers("r", "E"),
                    output_fn=lambda _: None,
                ),
            )
        reports.assert_called_once_with(5)

    def test_verify_selection_runs_current_project_validation(self) -> None:
        with patch.object(launcher, "recent_project_folders", return_value=[]), \
                patch.object(launcher, "current_git_root", return_value=ROOT), \
                patch.object(launcher, "verify_project", return_value=0) as verify:
            self.assertEqual(
                0,
                launcher.interactive(
                    ROOT / "test.db",
                    input_fn=self.answers("v", "E"),
                    output_fn=lambda _: None,
                ),
            )
        verify.assert_called_once_with(ROOT)

    def test_validation_commands_are_read_from_project_config(self) -> None:
        commands = launcher.validation_commands(ROOT)
        self.assertEqual(
            ["compile", "test", "sync", "smoke"],
            [name for name, _ in commands],
        )
        self.assertEqual("python scripts/verify.py", commands[1][1])

    def test_successful_actions_return_to_menu_until_end(self) -> None:
        recent = [ROOT.parent / "project"]
        output = []
        with patch.object(launcher, "recent_project_folders", return_value=recent), \
                patch.object(launcher, "current_git_root", return_value=ROOT), \
                patch.object(launcher, "show_reports", return_value=0) as reports, \
                patch.object(launcher, "verify_project", return_value=0) as verify:
            self.assertEqual(
                0,
                launcher.interactive(
                    ROOT / "test.db",
                    input_fn=self.answers("R", "V", "E"),
                    output_fn=output.append,
                ),
            )
        reports.assert_called_once_with(5)
        verify.assert_called_once_with(ROOT)
        self.assertEqual(3, output.count("AI Code"))

    def test_chained_project_reports_and_verify_actions_run_in_order(self) -> None:
        recent = [ROOT.parent / "project"]
        calls = []
        with patch.object(launcher, "recent_project_folders", return_value=recent), \
                patch.object(launcher, "current_git_root", return_value=ROOT), \
                patch.object(
                    launcher,
                    "onboard_project",
                    side_effect=lambda project, _: calls.append(("project", project)) or 0,
                ), \
                patch.object(
                    launcher,
                    "show_reports",
                    side_effect=lambda count: calls.append(("reports", count)) or 0,
                ), \
                patch.object(
                    launcher,
                    "verify_project",
                    side_effect=lambda project: calls.append(("verify", project)) or 0,
                ):
            self.assertEqual(
                0,
                launcher.interactive(
                    ROOT / "test.db",
                    input_fn=self.answers("1r10v", "E"),
                    output_fn=lambda _: None,
                ),
            )
        self.assertEqual(
            [
                ("project", recent[0]),
                ("reports", 10),
                ("verify", ROOT),
            ],
            calls,
        )

    def test_chained_verify_and_default_reports_are_supported(self) -> None:
        self.assertEqual(
            [("project", 1), ("verify", None), ("reports", 5)],
            launcher.parse_action_chain("1vr"),
        )
        self.assertEqual(
            [("reports", 10), ("verify", None)],
            launcher.parse_action_chain("r 10 v"),
        )

    def test_project_number_must_come_before_reports_or_verify(self) -> None:
        for selection in ("V1", "R10V3", "1R2R"):
            with self.subTest(selection=selection):
                with self.assertRaises(ValueError):
                    launcher.parse_action_chain(selection)


if __name__ == "__main__":
    unittest.main()
