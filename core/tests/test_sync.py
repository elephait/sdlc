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
            self.assertTrue((workspace / ".claude/CLAUDE.md").is_file())
            self.assertTrue(
                (workspace / ".agents/skills/tracked-story/SKILL.md").is_file()
            )


if __name__ == "__main__":
    unittest.main()
