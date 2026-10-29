#!/usr/bin/env python3
"""List the most recent analysis, scorecard, review and handoff artifacts.

Sources, newest first:
    core/reports/generated/     scorecards, failure reports, session analysis
    <active ledger>/reviews/    commit handoff and analysis reports
    md/reviews/                 human review write-ups

Usage:
    python scripts/reports.py
    python scripts/reports.py --limit 5
    python scripts/reports.py --limit 0      # everything
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
KINDS = (
    ("scorecard", "scorecard"),
    ("failures", "failures"),
    ("-analysis", "analysis"),
    ("review", "review"),
    ("handoff", "handoff"),
)


def active_ledger(repo: Path = REPO) -> Path | None:
    path = repo / ".sdlc" / "active-story.json"
    if not path.is_file():
        return None
    try:
        return Path(json.loads(path.read_text(encoding="utf-8-sig"))["ledgerPath"])
    except (OSError, KeyError, json.JSONDecodeError):
        return None


def kind_of(path: Path) -> str:
    lowered = path.name.lower()
    for marker, label in KINDS:
        if marker in lowered:
            return label
    return path.suffix.lstrip(".") or "file"


def collect(sources: list[Path | None], limit: int = 10) -> list[Path]:
    found: dict[Path, Path] = {}
    for source in sources:
        if source is None or not source.is_dir():
            continue
        for path in source.rglob("*"):
            if path.is_file() and path.suffix in {".json", ".md"}:
                found[path.resolve()] = path.resolve()
    ordered = sorted(found.values(), key=lambda p: p.stat().st_mtime, reverse=True)
    return ordered if limit <= 0 else ordered[:limit]


def describe(path: Path) -> str:
    try:
        shown = path.relative_to(REPO)
    except ValueError:
        shown = path
    stamp = datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
    return f"{stamp}  {path.stat().st_size:>7,} B  {kind_of(path):<10} {shown}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--limit", type=int, default=10, help="Rows to show; 0 for all.")
    parser.add_argument("--ledger", type=Path, help="Override the active story ledger.")
    args = parser.parse_args(argv)

    ledger = args.ledger or active_ledger()
    sources = [REPO / "core" / "reports" / "generated", ledger / "reviews" if ledger else None, REPO / "md" / "reviews"]
    reports = collect(sources, args.limit)
    if not reports:
        print("No reports found. Run a scored story or a commit handoff first.")
        return 0
    print(f"Recent reports ({len(reports)})")
    for path in reports:
        print("  " + describe(path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
