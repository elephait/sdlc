#!/usr/bin/env python3
"""Interactive and command-line entry point for AI coding setup and reports."""
from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
import re
import subprocess
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "core" / "src"))

from copilot_customization.db import DEFAULT_DB  # noqa: E402
from copilot_customization.service import recent_project_folders  # noqa: E402


def _load_script(name: str) -> Any:
    path = ROOT / "scripts" / name
    spec = importlib.util.spec_from_file_location(path.stem.replace("-", "_"), path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def current_git_root(current: Path | None = None) -> Path:
    cwd = (current or Path.cwd()).resolve()
    completed = subprocess.run(
        ["git", "-C", str(cwd), "rev-parse", "--show-toplevel"],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode:
        raise ValueError(f"Current folder is not inside a Git project: {cwd}")
    return Path(completed.stdout.strip()).resolve()


def show_reports(limit: int) -> int:
    return _load_script("reports.py").main(["--limit", str(limit)])


def onboard_project(workspace: Path, forwarded: list[str]) -> int:
    return _load_script("onboard.py").main(
        ["--workspace", str(workspace), *forwarded]
    )


def onboard_all(root: Path, forwarded: list[str]) -> int:
    return _load_script("onboard-all.py").main(
        ["--root", str(root), *forwarded]
    )


def validation_commands(project: Path) -> list[tuple[str, str]]:
    config = project / ".sdlc" / "project.yaml"
    if not config.is_file():
        raise ValueError(f"Project validation configuration was not found: {config}")
    commands: list[tuple[str, str]] = []
    in_validation = False
    current_check: str | None = None
    for line in config.read_text(encoding="utf-8-sig").splitlines():
        if re.match(r"^validation:\s*$", line):
            in_validation = True
            current_check = None
            continue
        if in_validation and line and not line.startswith((" ", "\t")):
            break
        if not in_validation:
            continue
        check = re.match(r"^  ([A-Za-z0-9_-]+):\s*$", line)
        if check:
            current_check = check.group(1)
            continue
        command = re.match(r"^    command:\s*(.+?)\s*$", line)
        if command and current_check:
            value = command.group(1).strip().strip("'\"")
            if value:
                commands.append((current_check, value))
    if not commands:
        raise ValueError(f"No validation commands are configured in {config}")
    return commands


def verify_project(project: Path) -> int:
    for name, command in validation_commands(project):
        print(f"\nVerify {name}: {command}", flush=True)
        completed = subprocess.run(command, cwd=project, shell=True)
        if completed.returncode:
            print(
                f"Verification stopped: {name} failed "
                f"(exit {completed.returncode}).",
                file=sys.stderr,
            )
            return completed.returncode
    print(f"\nVerification passed for {project}.")
    return 0


def parse_action_chain(selection: str) -> list[tuple[str, int | None]]:
    compact = "".join(selection.upper().split())
    if not compact:
        raise ValueError("Select a project number, R, V, or E.")
    if compact == "E":
        return [("end", None)]

    actions: list[tuple[str, int | None]] = []
    position = 0
    project = re.match(r"(10|[1-9])", compact)
    if project:
        actions.append(("project", int(project.group(1))))
        position = project.end()

    seen: set[str] = set()
    while position < len(compact):
        action = compact[position]
        if action not in {"R", "V"}:
            raise ValueError(
                "Use an optional project number first, followed by R and/or V "
                "(examples: 1R10V, 1VR, R10V)."
            )
        if action in seen:
            raise ValueError(f"{action} can appear only once in a command chain.")
        seen.add(action)
        position += 1
        if action == "V":
            actions.append(("verify", None))
            continue
        count_start = position
        while position < len(compact) and compact[position].isdigit():
            position += 1
        count = int(compact[count_start:position] or "5")
        actions.append(("reports", count))

    if not actions:
        raise ValueError("Select a project number, R, V, or E.")
    return actions


def interactive(
    db: Path,
    input_fn: Any = input,
    output_fn: Any = print,
    forwarded: list[str] | None = None,
) -> int:
    forwarded = list(forwarded) if forwarded is not None else ["--db", str(db)]
    while True:
        recent = recent_project_folders([], db, limit=9)
        try:
            current = current_git_root()
        except ValueError:
            current = None

        projects = list(recent)
        if not projects and current is not None:
            projects.append(current)

        output_fn("AI Code")
        if projects:
            output_fn(f"  1. Onboard latest project: {projects[0]}")
        else:
            output_fn("  1. Onboard latest project: unavailable")
        output_fn(
            f"  2. Onboard this folder if it is a Git project, plus Git projects under: "
            f"{Path.cwd().resolve()}"
        )
        for option, project in enumerate(projects[1:9], start=3):
            output_fn(f"  {option}. Onboard recent project: {project}")
        output_fn("  R. Show recent reports (default: 5); use R10 for 10")
        output_fn("  V. Verify the current Git project")
        output_fn("  E. End")
        output_fn("  Chain actions, for example: 1R10V or 1VR")

        default_selection = "1" if projects else "E"
        selection = (
            input_fn(f"Select option [{default_selection}]: ").strip().upper()
            or default_selection
        )
        actions = parse_action_chain(selection)
        if actions == [("end", None)]:
            output_fn("Ended.")
            return 0
        for action, value in actions:
            if action == "project":
                assert value is not None
                if value == 2:
                    if "--story" in forwarded or "--intent" in forwarded:
                        raise ValueError("--story and --intent cannot be used with bulk onboarding.")
                    result = onboard_all(Path.cwd().resolve(), forwarded)
                else:
                    project_index = 0 if value == 1 else value - 2
                    if not 0 <= project_index < len(projects):
                        raise ValueError(f"Project option is unavailable: {value}")
                    result = onboard_project(projects[project_index], forwarded)
            elif action == "reports":
                assert value is not None
                result = show_reports(value)
            else:
                if current is None:
                    raise ValueError("Current folder is not inside a Git project.")
                result = verify_project(current)
            if result:
                return result
        output_fn("")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--workspace", type=Path, help="Onboard this project.")
    action.add_argument(
        "--current",
        action="store_true",
        help="Onboard the Git project containing the current folder.",
    )
    action.add_argument(
        "--all",
        action="store_true",
        help="Onboard the current folder when it is a Git project and all Git "
             "projects directly under it.",
    )
    action.add_argument(
        "--reports",
        nargs="?",
        const=5,
        type=int,
        metavar="N",
        help="Show recent reports; defaults to 5 when N is omitted.",
    )
    action.add_argument(
        "--verify",
        action="store_true",
        help="Run validation configured for the current Git project.",
    )
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--skip-refresh", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--story")
    parser.add_argument("--intent")
    args = parser.parse_args(argv)

    try:
        if args.reports is not None:
            if args.reports < 0:
                raise ValueError("Report count must be a non-negative integer.")
            return show_reports(args.reports)
        if args.verify:
            return verify_project(current_git_root())

        forwarded = ["--db", str(args.db)]
        if args.skip_refresh:
            forwarded.append("--skip-refresh")
        if args.story:
            forwarded.extend(["--story", args.story])
        if args.intent:
            forwarded.extend(["--intent", args.intent])

        if args.all:
            if args.story or args.intent:
                parser.error("--story and --intent cannot be combined with --all")
            if args.dry_run:
                forwarded.append("--dry-run")
            return onboard_all(Path.cwd().resolve(), forwarded)
        if args.dry_run:
            parser.error("--dry-run requires --all")
        if args.workspace:
            return onboard_project(args.workspace.resolve(), forwarded)
        if args.current:
            return onboard_project(current_git_root(), forwarded)
        return interactive(args.db, forwarded=forwarded)
    except EOFError:
        print(
            "ERROR: input closed; use --workspace, --all, --reports or --verify.",
            file=sys.stderr,
        )
        return 1
    except (OSError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
