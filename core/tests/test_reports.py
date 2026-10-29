from __future__ import annotations

import importlib.util
import os
import sys
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from support import make_workspace, remove_workspace  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]


def load_reports():
    spec = importlib.util.spec_from_file_location(
        "sdlc_reports", ROOT / "scripts" / "reports.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ReportsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.workspace = make_workspace("reports")
        self.addCleanup(remove_workspace, self.workspace)
        self.module = load_reports()

    def touch(self, name: str, age_seconds: int) -> Path:
        path = self.workspace / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}", encoding="utf-8")
        stamp = time.time() - age_seconds
        os.utime(path, (stamp, stamp))
        return path

    def test_newest_first_and_limit(self) -> None:
        self.touch("old-scorecard.json", 300)
        self.touch("session-analysis.json", 10)
        self.touch("review-notes.md", 100)
        self.touch("ignored.txt", 1)

        rows = self.module.collect([self.workspace], limit=2)
        self.assertEqual(2, len(rows))
        self.assertEqual("session-analysis.json", rows[0].name)
        self.assertEqual("review-notes.md", rows[1].name)

        everything = self.module.collect([self.workspace], limit=0)
        self.assertEqual(3, len(everything))

    def test_duplicate_sources_are_listed_once(self) -> None:
        self.touch("scorecard-1.json", 5)
        rows = self.module.collect([self.workspace, self.workspace], limit=0)
        self.assertEqual(1, len(rows))

    def test_kind_is_readable(self) -> None:
        self.assertEqual("scorecard", self.module.kind_of(Path("x-scorecard.json")))
        self.assertEqual("analysis", self.module.kind_of(Path("commit-abc-analysis.json")))
        self.assertEqual("review", self.module.kind_of(Path("review.md")))


if __name__ == "__main__":
    unittest.main()
