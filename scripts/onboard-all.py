#!/usr/bin/env python3
"""Refresh every host adapter, validate, and track untracked projects.

Default behaviour, in order:
  1. regenerate the Copilot, Claude, Codex and DeepSeek payloads from shared sources
  2. run the local verification suite
  3. scan the workspace root for projects and add tracking where none exists

An existing ``.sdlc/active-story.json`` is never rewritten and never rebound:
the project is reported as preserved and skipped. Run with ``--dry-run`` to see
the plan without writing, or ``--skip-refresh`` to touch tracking only.

Usage:
    python scripts/onboard-all.py
    python scripts/onboard-all.py --root C:\\dev\\common --dry-run
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "core" / "src"))

from copilot_customization.db import DEFAULT_DB  # noqa: E402
from copilot_customization.service import onboard_project  # noqa: E402

PROJECT_MARKERS = (
    ".git",
    "pyproject.toml",
    "package.json",
    "pom.xml",
    "build.gradle",
    "Cargo.toml",
    "go.mod",
)
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
    return path.is_dir() and any((path / marker).exists() for marker in PROJECT_MARKERS)


def repository_name(path: Path) -> str:
    try:
        completed = subprocess.run(
            ["git", "-C", str(path), "remote", "get-url", "origin"],
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError:
        completed = None
    if completed is not None and completed.returncode == 0:
        match = re.search(r"[/:]([^/:]+/[^/]+?)(?:\.git)?$", completed.stdout.strip())
        if match:
            return match.group(1)
    return f"local/{path.name}"


def story_id_for(path: Path) -> str:
    stem = re.sub(r"[^A-Za-z0-9]+", "-", path.name).strip("-").upper() or "PROJECT"
    return f"{stem}-001"


def scan(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.iterdir()
        if path.name not in SKIP_NAMES
        and not path.name.startswith(".")
        and is_project(path)
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--root",
        type=Path,
        default=REPO.parent,
        help="Folder whose immediate children are projects (default: the folder above this repository).",
    )
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument(
        "--all",
        action="store_true",
        help="Accepted when called through `onboard.cmd --all`; it is already the default here.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Report the plan only.")
    parser.add_argument(
        "--reports",
        type=int,
        metavar="N",
        default=0,
        help="After onboarding, show the N most recent analysis reports.",
    )
    parser.add_argument("--skip-refresh", action="store_true", help="Skip sync and verify.")
    parser.add_argument("--skip-tracking", action="store_true", help="Skip the project scan.")
    args = parser.parse_args(argv)

    if not args.skip_refresh and not args.dry_run:
        code = run("Refresh all host payloads", ["scripts/sync-customizations.py"])
        if code:
            return code
        code = run("Validate shared code and generated payloads", ["scripts/verify.py"])
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
        if active.is_file():
            try:
                bound = json.loads(active.read_text(encoding="utf-8-sig")).get("storyId")
            except (OSError, json.JSONDecodeError):
                bound = "unreadable"
            print(f"  preserved  {project.name:<28} story {bound} (existing tracking)")
            continue

        story = story_id_for(project)
        repository = repository_name(project)
        if args.dry_run:
            print(f"  would add  {project.name:<28} story {story} ({repository})")
            continue
        try:
            result = onboard_project(
                project,
                project=project.name,
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
