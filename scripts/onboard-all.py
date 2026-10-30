#!/usr/bin/env python3
"""Refresh and install host adapters, then onboard project tracking.

Default behaviour, in order:
  1. regenerate the Copilot, Claude, Codex and DeepSeek payloads from shared sources
  2. scan the workspace root and its immediate children for projects and add
     tracking where none exists

Existing active stories are preserved; stale machine-local ledger paths may be
repaired. Run with ``--dry-run`` to see the plan without writing, or
``--skip-refresh`` to touch tracking only.

Usage:
    python scripts/onboard-all.py
    python scripts/onboard-all.py --root C:\\dev\\common --dry-run
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "core" / "src"))

from copilot_customization.db import DEFAULT_DB  # noqa: E402
from copilot_customization.service import onboard_project, onboarding_identity  # noqa: E402

SKIP_NAMES = {
    ".git",
    ".sdlc-test-work",
    ".sdlc-ledger",
    ".archive",
    ".dsh-acl-recovery",
    "node_modules",
    "__pycache__",
}


def run(label: str, command: list[str]) -> int:
    print(f"\n{label}", flush=True)
    completed = subprocess.run([sys.executable, *command], cwd=REPO)
    if completed.returncode:
        print(f"Stopped: {label} failed (exit {completed.returncode}).", file=sys.stderr)
    return completed.returncode


def is_project(path: Path) -> bool:
    return path.is_dir() and (path / ".git").exists()


def scan(root: Path) -> list[Path]:
    projects = [root] if is_project(root) else []
    projects.extend(sorted(
        path
        for path in root.iterdir()
        if path.name not in SKIP_NAMES
        and not path.name.startswith(".")
        and is_project(path)
    ))
    return projects


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--root",
        type=Path,
        default=REPO.parent,
        help="Project or folder whose immediate children are projects "
             "(default: the folder above this repository).",
    )
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument(
        "--all",
        action="store_true",
        help="Accepted when called through `aicode.cmd --all`; it is already the default here.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Report the plan only.")
    parser.add_argument(
        "--reports",
        nargs="?",
        const=5,
        type=int,
        metavar="N",
        default=0,
        help="After onboarding, show recent reports; defaults to 5.",
    )
    parser.add_argument("--skip-refresh", action="store_true", help="Skip adapter generation and installation.")
    parser.add_argument("--skip-tracking", action="store_true", help="Skip the project scan.")
    args = parser.parse_args(argv)

    if not args.skip_refresh and not args.dry_run:
        code = run("Refresh all host payloads", ["scripts/sync-customizations.py"])
        if code:
            return code

    if args.skip_tracking:
        return 0

    root = args.root.resolve()
    if not root.is_dir():
        print(f"ERROR: root does not exist: {root}", file=sys.stderr)
        return 1

    print(f"\nTracking projects under {root}")
    failures = 0
    for project in scan(root):
        active = project / ".sdlc" / "active-story.json"
        bound = None
        if active.is_file():
            try:
                bound = json.loads(active.read_text(encoding="utf-8-sig")).get("storyId")
            except (OSError, json.JSONDecodeError):
                bound = "unreadable"

        try:
            repository, story = onboarding_identity(project)
        except (ValueError, OSError) as error:
            print(f"  failed     {project.name:<28} {error}", file=sys.stderr)
            failures += 1
            continue
        if args.dry_run:
            if bound:
                print(f"  would preserve  {project.name:<28} story {story} ({repository})")
            else:
                print(f"  would add  {project.name:<28} story {story} ({repository})")
            continue
        if not args.skip_refresh:
            code = run(
                f"Install host customizations for {project.name}",
                ["scripts/sync-customizations.py", "--workspace", str(project)],
            )
            if code:
                failures += 1
                continue
        try:
            result = onboard_project(
                project,
                repository=repository,
                story_id=story,
                intent="Adopt existing project into shared SDLC tracking.",
                ledger_root=root / ".sdlc-ledger",
                db_path=args.db,
                tracking_hooks="none",
            )
        except (ValueError, OSError) as error:
            print(f"  failed     {project.name:<28} {error}", file=sys.stderr)
            failures += 1
            continue
        if bound:
            config_status = result["status"]["projectConfig"]
            detail = (
                "configuration updated"
                if config_status == "updated"
                else "existing tracking"
            )
            print(f"  preserved  {project.name:<28} story {result['storyId']} ({detail})")
        else:
            print(f"  added      {project.name:<28} story {result['storyId']} ({repository})")

    print("\nHost readiness")
    for label, path in (
        ("copilot plugin", REPO / "copilot-customization" / "plugin"),
        ("claude plugin", REPO / "claude-customization" / "plugin"),
        ("codex/deepseek instructions", REPO / "AGENTS.md"),
        ("generated skills", REPO / ".agents" / "skills"),
        ("deepseek guide", REPO / "deepseek-customization" / "deepseek.md"),
    ):
        print(f"  {'ok ' if path.exists() else 'missing '} {label}: {path.relative_to(REPO)}")
    print("\nEnable the Copilot and Claude plugins once in their apps; this command never changes host settings.")
    if args.reports and not args.dry_run:
        print()
        sys.stdout.flush()
        subprocess.run(
            [sys.executable, str(REPO / "scripts" / "reports.py"), "--limit", str(args.reports)],
            cwd=REPO,
        )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
