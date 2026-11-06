#!/usr/bin/env python3
"""Run local, dependency-free checks; never stage, commit or publish."""
from pathlib import Path
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "core" / "src") + os.pathsep + env.get("PYTHONPATH", "")
    for args in (
        ["scripts/sync-customizations.py", "--check"],
        ["scripts/validate-skills.py"],
        ["-m", "unittest", "discover", "-s", "core/tests", "-v"],
    ):
        result = subprocess.run([sys.executable, *args], cwd=ROOT, env=env)
        if result.returncode:
            return result.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
