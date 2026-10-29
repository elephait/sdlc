from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
HOOKS = ROOT / "scripts"
SCOPE_HOOK = HOOKS / "scope_hook.py"
sys.path.insert(0, str(HOOKS))

import scope_hook  # noqa: E402
import tracking_hook  # noqa: E402

HOOK_CONFIGS = (
    REPO / "copilot-customization" / "plugin" / "com.github.copilot"
    / "hooks" / "hooks.json",
)
CLAUDE_HOOKS = REPO / "claude-customization" / "plugin" / "hooks" / "hooks.json"


class HookContractTests(unittest.TestCase):
    def test_scope_hook_returns_pre_tool_contract(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(SCOPE_HOOK)],
            input=json.dumps(
                {
                    "hookEventName": "PreToolUse",
                    "cwd": r"C:\dev\common",
                    "toolName": "powershell",
                    "toolArgs": {"command": "git status --short"},
                }
            ),
            text=True,
            capture_output=True,
            check=True,
        )

        output = json.loads(completed.stdout)
        self.assertEqual(
            {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow",
                "permissionDecisionReason": (
                    r"Allowed by the C:\dev universal policy."
                ),
            },
            output["hookSpecificOutput"],
        )

    def test_tracking_configs_use_supported_non_intercepting_hooks(self) -> None:
        for path in HOOK_CONFIGS:
            with self.subTest(path=path):
                config = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(1, config["version"])
                self.assertEqual(
                    {"SessionStart", "PostToolUse", "PostToolUseFailure", "Stop"},
                    set(config["hooks"]),
                )
                for entries in config["hooks"].values():
                    self.assertEqual(1, len(entries))
                    entry = entries[0]
                    self.assertEqual("command", entry["type"])
                    self.assertIn("command", entry)
                    self.assertEqual(5, entry["timeout"])
                    self.assertNotIn("powershell", entry)
                    self.assertNotIn("timeoutSec", entry)

    def test_claude_hooks_wire_scope_guard_and_tracking(self) -> None:
        config = json.loads(CLAUDE_HOOKS.read_text(encoding="utf-8"))["hooks"]
        self.assertEqual(
            {
                "SessionStart",
                "PreToolUse",
                "PostToolUse",
                "PostToolUseFailure",
                "Stop",
            },
            set(config),
        )
        for event, groups in config.items():
            for group in groups:
                for entry in group["hooks"]:
                    self.assertEqual("command", entry["type"])
                    self.assertIn("${CLAUDE_PLUGIN_ROOT}", entry["command"])
                    if event == "PreToolUse":
                        self.assertIn("--no-allow", entry["command"])


class ScopeDecisionTests(unittest.TestCase):
    def decide(self, tool: str, tool_input: dict) -> str:
        return scope_hook.hook_decision(
            {"tool_name": tool, "tool_input": tool_input, "cwd": r"C:\dev\x"}
        )["permissionDecision"]

    def test_push_is_denied_and_judged_on_the_shell_command_only(self) -> None:
        self.assertEqual("deny", self.decide("Bash", {"command": "git push"}))
        self.assertEqual(
            "allow",
            self.decide(
                "Write",
                {"file_path": r"C:\dev\x\a.md", "content": "run git push later"},
            ),
        )
        self.assertEqual(
            "allow", self.decide("Bash", {"command": "git log --grep push"})
        )

    def test_file_content_is_not_a_write_destination(self) -> None:
        self.assertEqual("allow", self.decide("Write", {
            "file_path": r"C:\dev\x\guide.md", "content": r"Example D:\outside\file.txt"
        }))

    def test_relative_write_cannot_escape_dev(self) -> None:
        self.assertEqual("deny", self.decide("Write", {"file_path": r"..\..\outside.txt"}))

    def test_repository_does_not_duplicate_plugin_tracking(self) -> None:
        config = json.loads((REPO / ".github/hooks/copilot-sdlc.json").read_text())
        self.assertEqual({}, config["hooks"])

    def test_commit_title_prefix_is_enforced(self) -> None:
        self.assertEqual(
            "deny", self.decide("Bash", {"command": "git commit -m 'oops'"})
        )

    def test_write_outside_dev_root_is_denied(self) -> None:
        self.assertEqual(
            "deny",
            self.decide("Write", {"file_path": r"D:\other\a.txt", "content": ""}),
        )

    def test_git_exe_is_judged_like_git(self) -> None:
        self.assertEqual(
            "deny", self.decide("Bash", {"command": "git.exe push origin main"})
        )
        self.assertEqual(
            "deny", self.decide("Bash", {"command": "git.exe commit -m 'oops'"})
        )

    def test_dash_c_inside_a_message_is_not_a_repository(self) -> None:
        fallback = Path(r"C:\dev\fallback")
        self.assertEqual(
            fallback,
            scope_hook.git_command_cwd(
                'git commit -m "ai commit: x -C C:\\dev\\fake"', fallback
            ),
        )
        self.assertEqual(
            Path(r"C:\dev\repo"),
            scope_hook.git_command_cwd(
                'git -C "C:\\dev\\repo" commit -m "ai commit: x"', fallback
            ),
        )

    def test_no_allow_flag_defers_allowed_calls(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(SCOPE_HOOK), "--no-allow"],
            input=json.dumps(
                {
                    "tool_name": "Bash",
                    "tool_input": {"command": "git status"},
                    "cwd": r"C:\dev\x",
                }
            ),
            text=True,
            capture_output=True,
            check=True,
        )
        self.assertEqual({}, json.loads(completed.stdout))


class TrackingEventTests(unittest.TestCase):
    active = {"storyId": "S-1", "project": "p"}

    def event(self, **payload: str) -> dict:
        return tracking_hook.build_event(payload, self.active)

    def test_stop_without_reason_is_not_a_failure(self) -> None:
        self.assertTrue(self.event(hook_event_name="Stop")["success"])

    def test_abnormal_stop_reason_is_a_failure(self) -> None:
        event = self.event(hook_event_name="Stop", reason="error")
        self.assertFalse(event["success"])
        self.assertEqual("SESSION_STOP_FAILURE", event["errorCode"])

    def test_tool_failure_is_recorded(self) -> None:
        event = self.event(
            hook_event_name="PostToolUseFailure", tool_name="Bash", error="boom"
        )
        self.assertFalse(event["success"])
        self.assertEqual("boom", event["failureMessage"])


if __name__ == "__main__":
    unittest.main()
