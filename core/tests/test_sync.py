from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SYNC = Path(__file__).resolve().parents[2] / "scripts" / "sync-customizations.py"
ROOT = SYNC.parents[1]


class GeneratedFilesTests(unittest.TestCase):
    def test_host_plugins_match_shared_sources(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(SYNC), "--check"],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)

    def test_workspace_install_preserves_existing_instructions(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            agents = workspace / "AGENTS.md"
            agents.write_text("# Project instructions\n", encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, str(SYNC), "--workspace", str(workspace)],
                text=True,
                capture_output=True,
                check=False,
                cwd=ROOT,
            )
            self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)
            self.assertIn("# Project instructions", agents.read_text(encoding="utf-8"))
            self.assertIn("BEGIN DENISTEK SDLC", agents.read_text(encoding="utf-8"))
            self.assertTrue(
                (workspace / ".github/instructions/sdlc.instructions.md").is_file()
            )
            python_instructions = (
                workspace / ".github/instructions/sdlc-python.instructions.md"
            )
            java_instructions = (
                workspace / ".github/instructions/sdlc-java.instructions.md"
            )
            self.assertTrue(python_instructions.is_file())
            self.assertTrue(java_instructions.is_file())
            python_text = python_instructions.read_text(encoding="utf-8")
            java_text = java_instructions.read_text(encoding="utf-8")
            self.assertIn('applyTo:\n  - "**/*.py"\n', python_text)
            self.assertIn('  - "**/pyproject.toml"\n', python_text)
            self.assertIn('applyTo:\n  - "**/*.java"\n', java_text)
            self.assertIn('  - "**/pom.xml"\n', java_text)
            self.assertNotIn('applyTo: "**/*.py,', python_text)
            self.assertNotIn('applyTo: "**/*.java,', java_text)
            self.assertTrue((workspace / ".claude/CLAUDE.md").is_file())
            self.assertTrue(
                (workspace / ".agents/skills/tracked-story/SKILL.md").is_file()
            )

    def test_workspace_install_refreshes_managed_copilot_instruction(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            instruction = (
                workspace / ".github/instructions/sdlc-python.instructions.md"
            )
            instruction.parent.mkdir(parents=True)
            instruction.write_text(
                "<!-- Managed by DenisTek SDLC onboarding. "
                "Run aicode.cmd to refresh. -->\nold",
                encoding="utf-8",
            )

            completed = subprocess.run(
                [sys.executable, str(SYNC), "--workspace", str(workspace)],
                text=True,
                capture_output=True,
                check=False,
                cwd=ROOT,
            )

            self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)
            refreshed = instruction.read_text(encoding="utf-8")
            self.assertIn("# Python working rules", refreshed)
            self.assertNotIn("\nold", refreshed)

    def test_workspace_install_refuses_unmanaged_reserved_instruction(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            instruction = workspace / ".github/instructions/sdlc.instructions.md"
            instruction.parent.mkdir(parents=True)
            instruction.write_text("# User-owned instructions\n", encoding="utf-8")

            completed = subprocess.run(
                [sys.executable, str(SYNC), "--workspace", str(workspace)],
                text=True,
                capture_output=True,
                check=False,
                cwd=ROOT,
            )

            self.assertNotEqual(0, completed.returncode)
            self.assertIn(
                "Refusing to overwrite unmanaged Copilot instruction",
                completed.stderr,
            )
            self.assertEqual(
                "# User-owned instructions\n",
                instruction.read_text(encoding="utf-8"),
            )


    def test_workspace_install_writes_path_scoped_claude_rules(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            completed = subprocess.run(
                [sys.executable, str(SYNC), "--workspace", str(workspace)],
                text=True,
                capture_output=True,
                check=False,
                cwd=ROOT,
            )

            self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)
            python_rule = (workspace / ".claude/rules/sdlc-python.md").read_text(encoding="utf-8")
            java_rule = (workspace / ".claude/rules/sdlc-java.md").read_text(encoding="utf-8")
            self.assertTrue(python_rule.startswith('---\npaths:\n  - "**/*.py"\n'))
            self.assertIn('  - "**/pyproject.toml"\n', python_rule)
            self.assertTrue(java_rule.startswith('---\npaths:\n  - "**/*.java"\n'))
            self.assertIn('  - "**/pom.xml"\n', java_rule)
            self.assertIn("# Python working rules", python_rule)
            self.assertIn("# Java working rules", java_rule)
            self.assertNotIn("VS Code", python_rule)

    def test_workspace_install_refuses_unmanaged_claude_rule(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            rule = workspace / ".claude/rules/sdlc-python.md"
            rule.parent.mkdir(parents=True)
            rule.write_text("# User-owned rule\n", encoding="utf-8")

            completed = subprocess.run(
                [sys.executable, str(SYNC), "--workspace", str(workspace)],
                text=True,
                capture_output=True,
                check=False,
                cwd=ROOT,
            )

            self.assertNotEqual(0, completed.returncode)
            self.assertIn("Refusing to overwrite unmanaged Claude rule", completed.stderr)
            self.assertEqual("# User-owned rule\n", rule.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
