from __future__ import annotations

import json
import shutil
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
            self.assertNotIn(ROOT.as_posix(), agents.read_text(encoding="utf-8"))
            self.assertEqual(
                ROOT.as_posix() + "\n",
                (workspace / ".sdlc/sdlc-source.txt").read_text(encoding="utf-8"),
            )
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

    def test_workspace_install_refuses_colliding_user_skill_before_writing(self) -> None:
        for host in (".agents", ".github", ".claude"):
            with self.subTest(host=host), tempfile.TemporaryDirectory() as temporary:
                workspace = Path(temporary)
                skill = workspace / host / "skills/tracked-story/SKILL.md"
                skill.parent.mkdir(parents=True)
                skill.write_text("# My own workflow\n", encoding="utf-8")
                completed = subprocess.run(
                    [sys.executable, str(SYNC), "--workspace", str(workspace)],
                    text=True, capture_output=True, cwd=ROOT,
                )
                self.assertNotEqual(0, completed.returncode)
                self.assertIn("unmanaged skill", completed.stderr)
                self.assertEqual("# My own workflow\n", skill.read_text(encoding="utf-8"))
                self.assertFalse((workspace / "AGENTS.md").exists())

    def test_workspace_skill_refresh_preserves_user_added_files(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            command = [sys.executable, str(SYNC), "--workspace", str(workspace)]
            first = subprocess.run(command, text=True, capture_output=True, cwd=ROOT)
            self.assertEqual(0, first.returncode, first.stderr)
            extra = workspace / ".agents/skills/tracked-story/project-notes.md"
            extra.write_text("Keep this project note\n", encoding="utf-8")
            stale = extra.parent / "old-managed.md"
            stale.write_text("obsolete managed file\n", encoding="utf-8")
            manifest = extra.parent / ".sdlc-managed.json"
            names = json.loads(manifest.read_text(encoding="utf-8"))
            manifest.write_text(json.dumps(names + [stale.name]), encoding="utf-8")
            second = subprocess.run(command, text=True, capture_output=True, cwd=ROOT)
            self.assertEqual(0, second.returncode, second.stderr)
            self.assertEqual("Keep this project note\n", extra.read_text(encoding="utf-8"))
            self.assertFalse(stale.exists())

    def test_workspace_install_adopts_an_identical_legacy_skill(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            destination = workspace / ".agents/skills/tracked-story"
            shutil.copytree(ROOT / "skills/tracked-story", destination)
            completed = subprocess.run(
                [sys.executable, str(SYNC), "--workspace", str(workspace)],
                text=True, capture_output=True, cwd=ROOT,
            )
            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertTrue((destination / ".sdlc-managed.json").is_file())


    def _load_sync(self):
        import importlib.util

        spec = importlib.util.spec_from_file_location("sync_customizations", SYNC)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_legacy_skill_install_from_an_earlier_payload_is_adopted(self) -> None:
        module = self._load_sync()
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            legacy = workspace / ".agents/skills/tracked-story/SKILL.md"
            legacy.parent.mkdir(parents=True)
            legacy.write_bytes(b"older shared payload\n")
            module._historical_skill_trees = lambda source: iter(
                [{"SKILL.md": b"older shared payload\n"}]
            )

            module.install_workspace(workspace)

            self.assertIn("name: tracked-story", legacy.read_text(encoding="utf-8"))
            self.assertTrue((legacy.parent / ".sdlc-managed.json").is_file())

    def test_unmatched_same_name_skill_is_refused_and_preserved(self) -> None:
        module = self._load_sync()
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            own = workspace / ".claude/skills/tracked-story/SKILL.md"
            own.parent.mkdir(parents=True)
            own.write_text("# my own skill\n", encoding="utf-8")
            module._historical_skill_trees = lambda source: iter([])

            with self.assertRaisesRegex(ValueError, "Refusing to overwrite unmanaged skill"):
                module.install_workspace(workspace)

            self.assertEqual("# my own skill\n", own.read_text(encoding="utf-8"))

    def test_installed_agents_file_carries_no_machine_path(self) -> None:
        module = self._load_sync()
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            subprocess.run(["git", "init", "-q", str(workspace)], check=True)

            module.install_workspace(workspace)
            module.install_workspace(workspace)

            agents = (workspace / "AGENTS.md").read_text(encoding="utf-8")
            self.assertNotIn(module.REPO.as_posix(), agents)
            self.assertIn("SDLC_HOME", agents)
            self.assertIn(module.SOURCE_LOCATOR, agents)
            self.assertEqual(
                module.REPO.as_posix() + "\n",
                (workspace / module.SOURCE_LOCATOR).read_text(encoding="utf-8"),
            )
            exclude = (workspace / ".git/info/exclude").read_text(encoding="utf-8")
            self.assertEqual(1, exclude.splitlines().count(module.SOURCE_LOCATOR))


if __name__ == "__main__":
    unittest.main()
