#!/usr/bin/env python3
"""Refresh and validate all SDLC adapters, then refresh this project's tracking."""
from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--story", help="Optional story ID; existing active binding is preserved by default.")
    parser.add_argument("--intent", default="Optimize shared agent customization",
                        help="Intent used only when creating the story in the local database.")
    args = parser.parse_args(argv)
    onboard = ["scripts/sdlc.py", "project-onboard", "--workspace", str(ROOT),
               "--tracking-hooks", "none", "--intent", args.intent]
    if args.story:
        onboard.extend(["--story", args.story])
    for label, command in (
        ("Refresh Copilot, Claude, Codex and DeepSeek customizations", ["scripts/sync-customizations.py"]),
        ("Validate shared code and generated customizations", ["scripts/verify.py"]),
        ("Refresh SDLC tracking", onboard),
    ):
        print(f"\n{label}", flush=True)
        completed = subprocess.run([sys.executable, *command], cwd=ROOT)
        if completed.returncode:
            print(f"Stopped: {label} failed (exit {completed.returncode}).", file=sys.stderr)
            return completed.returncode
    print("\nSDLC customization and tracking are ready. Start a new chat in your chosen host.")
    print("Copilot/Claude plugin enablement remains a one-time host setup; see README.md.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
