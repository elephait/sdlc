from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

SYNC = Path(__file__).resolve().parents[2] / "scripts" / "sync-customizations.py"


class GeneratedFilesTests(unittest.TestCase):
    def test_host_plugins_match_shared_sources(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(SYNC), "--check"],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)


if __name__ == "__main__":
    unittest.main()
