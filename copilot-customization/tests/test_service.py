from __future__ import annotations

import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from copilot_customization.cli import main, parser
from copilot_customization.service import _commit_policy_decision


ROOT = Path(__file__).resolve().parents[1]


class CommitWorkflowTests(unittest.TestCase):
    def test_commit_policy_reads_scope_hook_contract(self) -> None:
        decision = _commit_policy_decision(
            ROOT,
            f'git -C "{ROOT}" commit -m "ai commit: contract check"',
        )

        self.assertEqual("allow", decision["permissionDecision"])

    def test_commit_ready_accepts_validation_summary_without_review_gate(self) -> None:
        args = parser().parse_args(
            [
                "commit-ready",
                "--workspace",
                str(ROOT),
                "--message",
                "contract check",
                "--prepared-by",
                "test",
                "--summary",
                "summary",
                "--validation-summary",
                "focused validation passed",
            ]
        )

        self.assertEqual("focused validation passed", args.validation_summary)
        self.assertFalse(hasattr(args, "review_loop_decision"))

    def test_tracking_report_fails_loudly_for_stale_capture(self) -> None:
        report = {
            "trackingHealthy": False,
            "trackingStatus": "stale",
            "warnings": ["CRITICAL: historical evidence only."],
        }
        output = StringIO()

        with patch(
            "copilot_customization.cli.tracking_report",
            return_value=report,
        ), redirect_stdout(output):
            exit_code = main(
                ["tracking-report", "--workspace", str(ROOT)]
            )

        self.assertEqual(2, exit_code)
        self.assertEqual(report, __import__("json").loads(output.getvalue()))

    def test_tracking_report_can_explicitly_allow_stale_capture(self) -> None:
        report = {
            "trackingHealthy": False,
            "trackingStatus": "stale",
            "warnings": ["CRITICAL: historical evidence only."],
        }

        with patch(
            "copilot_customization.cli.tracking_report",
            return_value=report,
        ), redirect_stdout(StringIO()):
            exit_code = main(
                [
                    "tracking-report",
                    "--workspace",
                    str(ROOT),
                    "--allow-stale",
                ]
            )

        self.assertEqual(0, exit_code)


if __name__ == "__main__":
    unittest.main()
