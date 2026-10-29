from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

from .db import DEFAULT_DB, initialize
from .service import (
    analyze_jsonl,
    bottleneck_report,
    commit_ready,
    compact_events,
    create_story,
    generate_scorecard,
    gates_for_story,
    import_jsonl,
    list_events,
    onboard_project,
    record_customization,
    record_decision,
    record_event,
    record_gate,
    record_resolution,
    record_session_review,
    select_project_folder,
    start_session,
    stop_session,
    tracking_report,
)


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="copilot-sdlc")
    root.add_argument("--db", type=Path, default=DEFAULT_DB)
    commands = root.add_subparsers(dest="command", required=True)

    commands.add_parser("init")

    onboard = commands.add_parser("project-onboard")
    onboard.add_argument("--workspace", type=Path)
    onboard.add_argument("--project")
    onboard.add_argument("--repository")
    onboard.add_argument("--story")
    onboard.add_argument("--intent")
    onboard.add_argument(
        "--priority",
        choices=("critical", "high", "medium", "low"),
        default="medium",
    )
    onboard.add_argument("--ledger-root", type=Path)
    onboard.add_argument(
        "--tracking-hooks", choices=("none", "copilot-workspace"), default="none",
        help="Use none with a host plugin or Codex; workspace hooks are opt-in.",
    )

    story = commands.add_parser("story-create")
    story.add_argument("--id", required=True)
    story.add_argument("--project", required=True)
    story.add_argument("--repository", required=True)
    story.add_argument("--intent", required=True)
    story.add_argument(
        "--priority", choices=("critical", "high", "medium", "low"), default="medium"
    )
    story.add_argument("--source-url")

    session = commands.add_parser("session-start")
    session.add_argument("--story", required=True)
    session.add_argument("--role", required=True)
    session.add_argument("--model")
    session.add_argument(
        "--host",
        help="Harness that ran the session: copilot, claude, codex or deepseek.",
    )
    session.add_argument("--session-id")

    session_stop = commands.add_parser("session-stop")
    session_stop.add_argument("--session", required=True)
    session_stop.add_argument("--outcome", required=True)

    session_review = commands.add_parser("session-review")
    session_review.add_argument("--session", required=True)
    session_review.add_argument("--reviewed-by", required=True)
    session_review.add_argument("--summary", required=True)

    ready = commands.add_parser("commit-ready")
    ready.add_argument("--workspace", type=Path)
    ready.add_argument("--message", required=True)
    ready.add_argument("--prepared-by", required=True)
    ready.add_argument("--summary", required=True)
    ready.add_argument("--finding", action="append", default=[])
    ready.add_argument(
        "--validation-summary",
        help="Commit-specific validation evidence, or omit when unavailable.",
    )
    ready.add_argument(
        "--co-author",
        help='Commit trailer identity, e.g. "Claude <noreply@anthropic.com>". '
        "Defaults to $SDLC_CO_AUTHOR; with neither, no trailer is added "
        "rather than attributing the commit to another harness.",
    )

    ready.add_argument(
        "--ai-name",
        help="AI named in the title, e.g. claude, deepseek, codex or copilot "
        "(`ai commit by claude: ...`). Defaults to $SDLC_AI_NAME, then the "
        "--co-author name, then --prepared-by.",
    )

    event = commands.add_parser("event")
    event.add_argument("--story", required=True)
    event.add_argument("--session")
    event.add_argument("--type", required=True)
    event.add_argument("--tool")
    event.add_argument("--category")
    event.add_argument("--failed", action="store_true")
    event.add_argument("--duration-ms", type=int)
    event.add_argument("--error-code")
    event.add_argument("--failure-message")
    event.add_argument("--resolution")
    event.add_argument(
        "--importance",
        choices=("trivial", "normal", "important", "decision"),
        default="normal",
    )
    progress = event.add_mutually_exclusive_group()
    progress.add_argument("--progress", action="store_true")
    progress.add_argument("--no-progress", action="store_true")
    event.add_argument("--details-json")

    decision = commands.add_parser("decision")
    decision.add_argument("--story", required=True)
    decision.add_argument("--session")
    decision.add_argument("--summary", required=True)
    decision.add_argument("--rationale")

    resolution = commands.add_parser("resolve-event")
    resolution.add_argument("--event-id", type=int, required=True)
    resolution.add_argument("--summary", required=True)
    resolution.add_argument("--session")

    gate = commands.add_parser(
        "gate", help="Record a handoff gate with its evidence and approver."
    )
    gate.add_argument("--story", required=True)
    gate.add_argument(
        "--gate",
        dest="gate_name",
        required=True,
        choices=("analysis", "implementation", "review", "customization", "docs"),
    )
    gate.add_argument(
        "--status", choices=("passed", "failed", "waived"), default="passed"
    )
    gate.add_argument("--evidence", required=True)
    gate.add_argument("--approved-by")
    gate.add_argument("--artifact", help="Reviewable artifact path for this gate.")
    gate.add_argument("--session")
    gate.add_argument("--workspace", type=Path)
    gate.add_argument("--details-json")

    gate_status = commands.add_parser(
        "gate-status", help="Show the latest recorded state of each gate."
    )
    gate_status.add_argument("--story", required=True)

    customization = commands.add_parser("customization-record")
    customization.add_argument("--component", required=True)
    customization.add_argument("--version", required=True)
    customization.add_argument("--source", type=Path, required=True)
    customization.add_argument("--model")
    customization.add_argument("--metadata-json")
    customization.add_argument(
        "--metadata",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Repeatable PowerShell-safe metadata entry.",
    )

    importer = commands.add_parser("import-jsonl")
    importer.add_argument("--story", required=True)
    importer.add_argument("--source", type=Path, required=True)

    events_list = commands.add_parser("events-list")
    events_list.add_argument("--story", required=True)
    events_list.add_argument("--session")
    events_list.add_argument("--include-archived", action="store_true")

    jsonl_report = commands.add_parser("jsonl-report")
    jsonl_report.add_argument("--source", type=Path, required=True)
    jsonl_report.add_argument("--story")
    jsonl_report.add_argument("--session")

    active_report = commands.add_parser("tracking-report")
    active_report.add_argument("--workspace", type=Path)
    active_report.add_argument("--session")
    active_report.add_argument("--include-stale-analysis", action="store_true")
    active_report.add_argument(
        "--allow-stale",
        action="store_true",
        help="Return success even when capture evidence is missing or stale.",
    )

    scorecard = commands.add_parser("scorecard")
    scorecard.add_argument("--story", required=True)
    scorecard.add_argument(
        "--outcome",
        choices=("pending", "passed", "partial", "failed", "blocked"),
        required=True,
    )
    scorecard.add_argument("--runtime-verified", action="store_true")
    scorecard.add_argument("--report-root", type=Path)

    compact = commands.add_parser("compact")
    compact.add_argument("--older-than-days", type=int, default=30)
    compact.add_argument("--purge-archived-days", type=int)

    report = commands.add_parser("bottlenecks")
    report.add_argument("--story", required=True)
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "init":
            initialize(args.db)
            print(args.db)
        elif args.command == "project-onboard":
            workspace = args.workspace or select_project_folder(args.db)
            print(
                json.dumps(
                    onboard_project(
                        workspace,
                        args.project,
                        args.repository,
                        args.story,
                        args.intent,
                        args.priority,
                        args.ledger_root,
                        args.db,
                        args.tracking_hooks,
                    ),
                    indent=2,
                )
            )
        elif args.command == "story-create":
            create_story(
                args.id,
                args.project,
                args.repository,
                args.intent,
                args.priority,
                args.source_url,
                args.db,
            )
            print(args.id)
        elif args.command == "session-start":
            print(
                start_session(
                    args.story,
                    args.role,
                    args.model,
                    args.session_id,
                    db_path=args.db,
                    host=args.host,
                )
            )
        elif args.command == "session-stop":
            stop_session(args.session, args.outcome, args.db)
        elif args.command == "session-review":
            print(
                record_session_review(
                    args.session,
                    args.reviewed_by,
                    args.summary,
                    args.db,
                )
            )
        elif args.command == "commit-ready":
            workspace = args.workspace or select_project_folder(args.db)
            print(
                json.dumps(
                    commit_ready(
                        workspace,
                        args.message,
                        args.prepared_by,
                        args.summary,
                        args.finding,
                        args.db,
                        args.validation_summary,
                        args.co_author,
                        args.ai_name,
                    ),
                    indent=2,
                )
            )
        elif args.command == "event":
            progress = (
                True if args.progress else False if args.no_progress else None
            )
            details = json.loads(args.details_json) if args.details_json else None
            event_id, stalled = record_event(
                story_id=args.story,
                event_type=args.type,
                session_id=args.session,
                tool=args.tool,
                category=args.category,
                success=not args.failed,
                duration_ms=args.duration_ms,
                error_code=args.error_code,
                failure_message=args.failure_message,
                resolution=args.resolution,
                importance=args.importance,
                meaningful_progress=progress,
                details=details,
                db_path=args.db,
            )
            print(json.dumps({"eventId": event_id, "stalled": stalled}))
            if stalled:
                print(
                    "STOP_AND_RETHINK: three iterations produced no meaningful progress. "
                    "Re-evaluate the logic chain or ask one focused clarification.",
                    file=sys.stderr,
                )
                return 2
        elif args.command == "decision":
            print(
                record_decision(
                    args.story,
                    args.summary,
                    args.rationale,
                    args.session,
                    args.db,
                )
            )
        elif args.command == "resolve-event":
            print(
                record_resolution(
                    args.event_id,
                    args.summary,
                    args.session,
                    args.db,
                )
            )
        elif args.command == "gate":
            workspace = args.workspace or select_project_folder(args.db)
            details = json.loads(args.details_json) if args.details_json else None
            print(
                json.dumps(
                    record_gate(
                        workspace=workspace,
                        story_id=args.story,
                        gate=args.gate_name,
                        status=args.status,
                        evidence=args.evidence,
                        approved_by=args.approved_by,
                        artifact=args.artifact,
                        session_id=args.session,
                        details=details,
                        db_path=args.db,
                    ),
                    indent=2,
                )
            )
        elif args.command == "gate-status":
            print(
                json.dumps(
                    gates_for_story(args.story, args.db),
                    indent=2,
                )
            )
        elif args.command == "customization-record":
            metadata = (
                json.loads(args.metadata_json) if args.metadata_json else None
            )
            if args.metadata:
                metadata = metadata or {}
                for entry in args.metadata:
                    if "=" not in entry:
                        raise ValueError(
                            f"Metadata must use KEY=VALUE format: {entry}"
                        )
                    key, value = entry.split("=", 1)
                    if not key:
                        raise ValueError("Metadata key cannot be empty.")
                    metadata[key] = value
            print(
                record_customization(
                    args.component,
                    args.version,
                    args.source,
                    args.model,
                    metadata,
                    args.db,
                )
            )
        elif args.command == "import-jsonl":
            print(import_jsonl(args.story, args.source, args.db))
        elif args.command == "events-list":
            print(
                json.dumps(
                    list_events(
                        args.story,
                        args.session,
                        args.include_archived,
                        args.db,
                    ),
                    indent=2,
                )
            )
        elif args.command == "jsonl-report":
            print(
                json.dumps(
                    analyze_jsonl(args.source, args.story, args.session),
                    indent=2,
                )
            )
        elif args.command == "tracking-report":
            workspace = args.workspace or select_project_folder(args.db)
            report = tracking_report(
                workspace,
                args.session,
                args.db,
                args.include_stale_analysis,
            )
            print(json.dumps(report, indent=2))
            if not report["trackingHealthy"] and not args.allow_stale:
                return 2
        elif args.command == "scorecard":
            kwargs = {}
            if args.report_root:
                kwargs["report_root"] = args.report_root
            print(
                json.dumps(
                    generate_scorecard(
                        args.story,
                        args.outcome,
                        args.runtime_verified,
                        args.db,
                        **kwargs,
                    ),
                    indent=2,
                )
            )
        elif args.command == "compact":
            print(
                json.dumps(
                    compact_events(
                        args.older_than_days,
                        args.purge_archived_days,
                        args.db,
                    )
                )
            )
        elif args.command == "bottlenecks":
            print(json.dumps(bottleneck_report(args.story, args.db), indent=2))
        return 0
    except (
        ValueError,
        FileNotFoundError,
        json.JSONDecodeError,
        sqlite3.IntegrityError,
        sqlite3.OperationalError,
    ) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
