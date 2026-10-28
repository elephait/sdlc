from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCOPE_HOOK = ROOT / "plugin" / "scripts" / "scope_hook.py"
HOOK_CONFIGS = (
    ROOT / ".github" / "hooks" / "copilot-sdlc.json",
    ROOT / "plugin" / "com.github.copilot" / "hooks" / "hooks.json",
)


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
                    {"SessionStart", "PostToolUse", "Stop"},
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


if __name__ == "__main__":
    unittest.main()
