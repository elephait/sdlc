#!/usr/bin/env python3
"""Refresh and validate all SDLC adapters, then refresh tracking for a chosen project."""
from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "core" / "src"))

from copilot_customization.db import DEFAULT_DB  # noqa: E402
from copilot_customization.service import select_project_folder  # noqa: E402

SDLC_INTENT = "Optimize shared agent customization"


def choose_workspace(workspace: Path | None, db: Path) -> Path:
    """Explicit --workspace wins; otherwise pick from recent projects.

    The default (Enter) is the most recently used project. With no terminal to
    answer a prompt, the default is taken rather than blocking on input().
    """
    if workspace:
        return workspace.resolve()
    if not sys.stdin.isatty():
        from copilot_customization.service import (
            discover_project_folders,
            recent_project_folders,
        )

        recent = recent_project_folders(discover_project_folders(), db)
        if not recent:
            raise ValueError("No project folders found; pass --workspace.")
        print(f"No terminal; using the default project: {recent[0]}")
        return recent[0]
    return select_project_folder(db)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path,
                        help="Project to track. Omit to choose from recent projects (Enter = most recent).")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--skip-refresh", action="store_true",
                        help="Refresh tracking only; do not regenerate adapters or run validation.")
    parser.add_argument("--story", help="Optional story ID; existing active binding is preserved by default.")
    parser.add_argument("--intent",
                        help="Intent used only when creating the story in the local database "
                             f"(default for this checkout: {SDLC_INTENT!r}).")
    args = parser.parse_args(argv)
    try:
        workspace = choose_workspace(args.workspace, args.db)
    except (ValueError, OSError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"Project: {workspace}", flush=True)
    intent = args.intent or (SDLC_INTENT if workspace == ROOT else None)
    onboard = ["scripts/sdlc.py", "--db", str(args.db), "project-onboard",
               "--workspace", str(workspace), "--tracking-hooks", "none"]
    if intent:
        onboard.extend(["--intent", intent])
    if args.story:
        onboard.extend(["--story", args.story])
    steps = [
        ("Refresh Copilot, Claude, Codex and DeepSeek customizations", ["scripts/sync-customizations.py"]),
        ("Validate shared code and generated customizations", ["scripts/verify.py"]),
        (f"Refresh SDLC tracking for {workspace.name}", onboard),
    ]
    if args.skip_refresh:
        steps = steps[-1:]
    for label, command in steps:
        print(f"\n{label}", flush=True)
        completed = subprocess.run([sys.executable, *command], cwd=ROOT)
        if completed.returncode:
            print(f"Stopped: {label} failed (exit {completed.returncode}).", file=sys.stderr)
            return completed.returncode
    if args.skip_refresh:
        print(f"\nTracking refreshed for {workspace}; adapters were not refreshed or validated. Existing sessions continue.")
    else:
        print(f"\nSDLC customization and tracking are ready for {workspace}. Use a new chat to load updated instructions.")
        print("Copilot/Claude plugin enablement remains a one-time host setup; see README.md.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
