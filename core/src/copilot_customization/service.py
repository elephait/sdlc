from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import subprocess
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from .db import DEFAULT_DB, DEV_ROOT, database, initialize, require_under_dev

PROJECT_ROOT = Path(__file__).resolve().parents[2]
HOOK_SCRIPT_ROOT = PROJECT_ROOT / "scripts"
DEFAULT_REPORT_ROOT = PROJECT_ROOT / "reports" / "generated"
TERMINAL_OUTCOMES = {
    "DONE",
    "BLOCKED_NEEDS_USER",
    "FAILED",
    "STUCK",
    "LIMIT_REACHED",
    "SECURITY_STOP",
}
TRACKING_STALE_AFTER = timedelta(minutes=15)
DEFAULT_LEDGER_ROOT = Path(r"C:\dev\common\copilot\sdlc\ledger\stories")
PROJECT_MARKERS = {
    ".git",
    ".sdlc",
    "pom.xml",
    "build.gradle",
    "build.gradle.kts",
    "package.json",
    "pyproject.toml",
    "Cargo.toml",
    "go.mod",
}
PROJECT_SCAN_SKIPS = {
    ".git",
    ".idea",
    ".venv",
    ".vs",
    ".vscode",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "target",
}


def now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat()


def create_story(
    story_id: str,
    project: str,
    repository: str,
    intent: str,
    priority: str,
    source_url: str | None,
    db_path: Path = DEFAULT_DB,
) -> None:
    initialize(db_path)
    timestamp = now()
    with database(db_path) as connection:
        connection.execute(
            """
            INSERT INTO stories (
                story_id, project, repository, intent, status, priority,
                source_url, created_at, updated_at
            ) VALUES (?, ?, ?, ?, 'DRAFT', ?, ?, ?, ?)
            """,
            (
                story_id,
                project,
                repository,
                intent,
                priority,
                source_url,
                timestamp,
                timestamp,
            ),
        )


def onboard_project(
    workspace: Path,
    project: str | None = None,
    repository: str | None = None,
    story_id: str | None = None,
    intent: str | None = None,
    priority: str = "medium",
    ledger_root: Path | None = None,
    db_path: Path = DEFAULT_DB,
    tracking_hooks: str = "none",
) -> dict[str, Any]:
    if tracking_hooks not in {"none", "copilot-workspace"}:
        raise ValueError("tracking_hooks must be none or copilot-workspace")
    resolved_workspace = require_under_dev(workspace, "Workspace")
    if not resolved_workspace.is_dir():
        raise ValueError(f"Workspace does not exist: {resolved_workspace}")

    sdlc_root = resolved_workspace / ".sdlc"
    project_path = sdlc_root / "project.yaml"
    active_path = sdlc_root / "active-story.json"
    project_values: dict[str, str] = {}
    if project_path.is_file():
        project_values = _read_project_values(project_path)
    active: dict[str, Any] = {}
    if active_path.is_file():
        active = json.loads(active_path.read_text(encoding="utf-8-sig"))

    resolved_project = (
        project
        or project_values.get("project")
        or active.get("project")
        or resolved_workspace.name
    )
    resolved_repository = (
        repository
        or project_values.get("repository")
        or active.get("repository")
    )
    resolved_story = story_id or active.get("storyId")
    if not resolved_repository:
        raise ValueError(
            "Repository is required when the workspace has no existing "
            "SDLC configuration."
        )
    if not resolved_story:
        raise ValueError(
            "Story ID is required when the workspace has no active story."
        )

    project_relocated = False
    previous_workspace: Path | None = None
    configured_workspace = project_values.get("workspaceRoot")
    if configured_workspace:
        previous_workspace = Path(configured_workspace)
        if previous_workspace.resolve() != resolved_workspace:
            if previous_workspace.exists():
                raise ValueError(
                    "Existing project.yaml workspaceRoot conflicts with "
                    f"onboarding: {configured_workspace!r} != "
                    f"{str(resolved_workspace)!r}"
                )
            project_relocated = True

    if project_values:
        for key, expected in (
            ("project", resolved_project),
            ("repository", resolved_repository),
        ):
            configured = project_values.get(key)
            if configured and configured != expected:
                raise ValueError(
                    f"Existing project.yaml {key} conflicts with onboarding: "
                    f"{configured!r} != {expected!r}"
                )

    if active:
        if active.get("storyId") != resolved_story:
            raise ValueError(
                f"Workspace already has active story {active.get('storyId')}. "
                "Resolve or deactivate it before onboarding another story."
            )
        configured_ledger = Path(active["ledgerPath"])
        resolved_ledger = (
            configured_ledger
            if configured_ledger.is_absolute()
            else resolved_workspace / configured_ledger
        ).resolve()
        active_ledger_changed = False
        if project_relocated and configured_ledger.is_absolute():
            if previous_workspace is None:
                raise ValueError("Previous workspace is required for relocation.")
            try:
                workspace_relative_ledger = configured_ledger.relative_to(
                    previous_workspace
                )
            except ValueError:
                pass
            else:
                resolved_ledger = (
                    resolved_workspace / workspace_relative_ledger
                ).resolve()
                active_ledger_changed = True
    else:
        active_ledger_changed = False
        root = require_under_dev(
            ledger_root or DEFAULT_LEDGER_ROOT,
            "Ledger root",
        )
        resolved_ledger = root / resolved_project / resolved_story
    resolved_ledger = require_under_dev(resolved_ledger, "Ledger")

    initialize(db_path)
    timestamp = now()
    story_status = "preserved"
    with database(db_path) as connection:
        existing = connection.execute(
            "SELECT * FROM stories WHERE story_id = ?",
            (resolved_story,),
        ).fetchone()
        if existing:
            if (
                existing["project"] != resolved_project
                or existing["repository"] != resolved_repository
            ):
                raise ValueError(
                    f"Story {resolved_story} already belongs to "
                    f"{existing['project']} ({existing['repository']})."
                )
        else:
            if not intent:
                raise ValueError(
                    "Intent is required when onboarding a story that is not "
                    "already in the coordination database."
                )
            connection.execute(
                """
                INSERT INTO stories (
                    story_id, project, repository, intent, status, priority,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, 'DRAFT', ?, ?, ?)
                """,
                (
                    resolved_story,
                    resolved_project,
                    resolved_repository,
                    intent,
                    priority,
                    timestamp,
                    timestamp,
                ),
            )
            story_status = "created"

    sdlc_root.mkdir(parents=True, exist_ok=True)
    project_status = "updated" if project_relocated else "preserved"
    if project_relocated:
        replacements = {"workspaceRoot": str(resolved_workspace)}
        configured_project_ledger = project_values.get("ledgerPath")
        if configured_project_ledger and active:
            replacements["ledgerPath"] = str(resolved_ledger)
        _replace_project_values(project_path, replacements)
    if not project_path.exists():
        _atomic_write(
            project_path,
            "\n".join(
                [
                    "schemaVersion: 1",
                    f"project: {_yaml_scalar(resolved_project)}",
                    f"repository: {_yaml_scalar(resolved_repository)}",
                    f"workspaceRoot: {_yaml_scalar(str(resolved_workspace))}",
                    "",
                    "tracking:",
                    f"  storyId: {_yaml_scalar(resolved_story)}",
                    f"  ledgerPath: {_yaml_scalar(str(resolved_ledger))}",
                    "",
                ]
            ),
        )
        project_status = "created"

    active_status = "preserved"
    if active and active_ledger_changed:
        active["ledgerPath"] = str(resolved_ledger)
        _atomic_write(active_path, json.dumps(active, indent=2) + "\n")
        active_status = "updated"
    if not active_path.exists():
        _atomic_write(
            active_path,
            json.dumps(
                {
                    "storyId": resolved_story,
                    "project": resolved_project,
                    "repository": resolved_repository,
                    "ledgerPath": str(resolved_ledger),
                    "activatedAt": timestamp,
                },
                indent=2,
            )
            + "\n",
        )
        active_status = "created"

    resolved_ledger.mkdir(parents=True, exist_ok=True)
    event_path = resolved_ledger / "events.jsonl"
    event_path.touch(exist_ok=True)
    story_path = resolved_ledger / "story.md"
    ledger_story_status = "preserved"
    if not story_path.exists():
        _atomic_write(
            story_path,
            "\n".join(
                [
                    "---",
                    f'storyId: "{resolved_story}"',
                    f'project: "{resolved_project}"',
                    f'repository: "{resolved_repository}"',
                    'status: "DRAFT"',
                    f'priority: "{priority}"',
                    f'createdAt: "{timestamp}"',
                    "---",
                    "",
                    "# Intent",
                    "",
                    intent or "See the coordination database.",
                    "",
                    "# Acceptance criteria",
                    "",
                    "- [ ] Define story-specific acceptance criteria.",
                    "",
                ]
            ),
        )
        ledger_story_status = "created"

    tracking_hooks_status = (
        _install_tracking_hooks(resolved_workspace)
        if tracking_hooks == "copilot-workspace" else "not-installed"
    )
    record_project_use(resolved_workspace, db_path)
    return {
        "workspace": str(resolved_workspace),
        "project": resolved_project,
        "repository": resolved_repository,
        "storyId": resolved_story,
        "ledgerPath": str(resolved_ledger),
        "eventPath": str(event_path),
        "database": str(db_path.resolve()),
        "status": {
            "projectConfig": project_status,
            "activeStory": active_status,
            "databaseStory": story_status,
            "ledgerStory": ledger_story_status,
            "trackingHooks": tracking_hooks_status,
        },
        "next": {
            "startNewCopilotSession": tracking_hooks == "copilot-workspace",
            "policyActivation": "host-managed",
            "analysisCommand": (
                "python -m copilot_customization.cli tracking-report "
                f'--workspace "{resolved_workspace}"'
            ),
        },
    }


def _install_tracking_hooks(workspace: Path) -> str:
    runtime_script = workspace / ".sdlc" / "hooks" / "tracking_hook.py"
    hook_config = workspace / ".github" / "hooks" / "copilot-sdlc.json"
    hooks = {
        name: [
            {
                "type": "command",
                "command": 'python ".sdlc\\hooks\\tracking_hook.py"',
                "timeout": 5,
            }
        ]
        for name in (
            "SessionStart",
            "PostToolUse",
            "PostToolUseFailure",
            "Stop",
        )
    }
    files = {
        runtime_script: (
            HOOK_SCRIPT_ROOT / "tracking_hook.py"
        ).read_text(encoding="utf-8"),
        hook_config: json.dumps(
            {"version": 1, "hooks": hooks},
            indent=2,
        )
        + "\n",
    }
    existed = [path.exists() for path in files]
    changed = False
    for path, expected in files.items():
        current = path.read_text(encoding="utf-8-sig") if path.is_file() else None
        if current != expected:
            _atomic_write(path, expected)
            changed = True
    if not any(existed):
        return "created"
    return "updated" if changed else "preserved"


def discover_project_folders(search_root: Path = DEV_ROOT) -> list[Path]:
    root = require_under_dev(search_root, "Project search root")
    projects: list[Path] = []
    for current, directories, files in os.walk(root):
        entries = set(directories) | set(files)
        directories[:] = [
            name for name in directories if name not in PROJECT_SCAN_SKIPS
        ]
        if entries & PROJECT_MARKERS:
            projects.append(Path(current).resolve())
    return sorted(set(projects), key=lambda path: str(path).lower())


def record_project_use(
    workspace: Path,
    db_path: Path = DEFAULT_DB,
) -> None:
    resolved = require_under_dev(workspace, "Workspace")
    initialize(db_path)
    with database(db_path) as connection:
        connection.execute(
            """
            INSERT INTO project_usage (
                workspace_path, project_name, last_used_at, use_count
            ) VALUES (?, ?, ?, 1)
            ON CONFLICT(workspace_path) DO UPDATE SET
                project_name = excluded.project_name,
                last_used_at = excluded.last_used_at,
                use_count = project_usage.use_count + 1
            """,
            (str(resolved), resolved.name, now()),
        )


def recent_project_folders(
    discovered: list[Path],
    db_path: Path = DEFAULT_DB,
    limit: int = 5,
) -> list[Path]:
    initialize(db_path)
    with database(db_path) as connection:
        usage_rows = connection.execute(
            """
            SELECT workspace_path
              FROM project_usage
             ORDER BY last_used_at DESC
            """
        ).fetchall()
    ranked: list[Path] = []
    for row in usage_rows:
        candidate = Path(row["workspace_path"])
        if candidate.is_dir() and candidate not in ranked:
            ranked.append(candidate.resolve())
    remaining = [path for path in discovered if path not in ranked]
    remaining.sort(key=_project_activity, reverse=True)
    ranked.extend(remaining)
    return ranked[:limit]


def select_project_folder(
    db_path: Path = DEFAULT_DB,
    search_root: Path = DEV_ROOT,
    input_fn: Any = input,
    output_fn: Any = print,
) -> Path:
    discovered = discover_project_folders(search_root)
    if not discovered:
        raise ValueError(f"No project folders found under {search_root}.")
    recent = recent_project_folders(discovered, db_path)
    output_fn("Recently used projects:")
    for index, path in enumerate(recent, start=1):
        suffix = " [default]" if index == 1 else ""
        output_fn(f"  {index}. {path}{suffix}")
    selection = input_fn(
        f"Project folder name under {search_root} or recent number [1]: "
    ).strip()
    if not selection:
        return recent[0]
    if selection.isdigit():
        index = int(selection)
        if 1 <= index <= len(recent):
            return recent[index - 1]
        raise ValueError(f"Recent project number is out of range: {selection}")

    candidate = Path(selection)
    if candidate.is_absolute():
        resolved = require_under_dev(candidate, "Workspace")
        if not resolved.is_dir():
            raise ValueError(f"Project folder does not exist: {resolved}")
        return resolved

    exact = [
        path for path in discovered if path.name.lower() == selection.lower()
    ]
    matches = exact or [
        path for path in discovered if selection.lower() in path.name.lower()
    ]
    if not matches:
        raise ValueError(
            f"No project folder matching {selection!r} was found under "
            f"{search_root}."
        )
    if len(matches) == 1:
        return matches[0]
    output_fn(f"Multiple projects match {selection!r}:")
    for index, path in enumerate(matches, start=1):
        output_fn(f"  {index}. {path}")
    match_selection = input_fn("Select project number [1]: ").strip()
    if not match_selection:
        return matches[0]
    if not match_selection.isdigit():
        raise ValueError("Project selection must be a number.")
    index = int(match_selection)
    if not 1 <= index <= len(matches):
        raise ValueError(f"Project number is out of range: {match_selection}")
    return matches[index - 1]


def _project_activity(path: Path) -> float:
    candidates = [
        path / ".sdlc" / "active-story.json",
        path / ".sdlc" / "project.yaml",
        path / ".git",
    ]
    timestamps = [
        candidate.stat().st_mtime for candidate in candidates if candidate.exists()
    ]
    return max(timestamps, default=path.stat().st_mtime)


def _read_project_values(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8-sig")
    values: dict[str, str] = {}
    for key in ("project", "repository", "workspaceRoot", "storyId", "ledgerPath"):
        match = re.search(rf"(?m)^{key}:\s*(.+?)\s*$", text)
        if match:
            values[key] = match.group(1).strip().strip("'\"")
    return values


def _replace_project_values(path: Path, replacements: dict[str, str]) -> None:
    text = path.read_text(encoding="utf-8-sig")
    updated = text
    for key, value in replacements.items():
        updated, count = re.subn(
            rf"(?m)^{re.escape(key)}:\s*.+?$",
            lambda _: f"{key}: {_yaml_scalar(value)}",
            updated,
        )
        if count != 1:
            raise ValueError(f"Expected exactly one {key} entry in {path}.")
    _atomic_write(path, updated)


def _yaml_scalar(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def start_session(
    story_id: str,
    role: str,
    model: str | None,
    session_id: str | None,
    db_path: Path = DEFAULT_DB,
    host: str | None = None,
) -> str:
    identifier = session_id or str(uuid4())
    with database(db_path) as connection:
        existing = connection.execute(
            "SELECT story_id FROM sessions WHERE session_id = ?",
            (identifier,),
        ).fetchone()
        if existing:
            if existing["story_id"] == story_id:
                return identifier
            raise ValueError(
                f"Session ID {identifier} already belongs to story "
                f"{existing['story_id']}. Omit --session-id to generate a "
                "unique ID, or provide a different ID."
            )
        connection.execute(
            """
            INSERT INTO sessions (
                session_id, story_id, role, model, host, started_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (identifier, story_id, role, model, host, now()),
        )
    return identifier


def stop_session(
    session_id: str,
    outcome: str,
    db_path: Path = DEFAULT_DB,
) -> None:
    if outcome not in TERMINAL_OUTCOMES:
        raise ValueError(
            f"Outcome must be one of: {', '.join(sorted(TERMINAL_OUTCOMES))}"
        )
    with database(db_path) as connection:
        row = connection.execute(
            "SELECT ended_at, outcome FROM sessions WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        if not row:
            raise ValueError(f"Unknown session: {session_id}")
        if row["ended_at"]:
            if row["outcome"] == outcome:
                return
            raise ValueError(
                f"Session {session_id} already closed as {row['outcome']}; "
                "record a new session rather than rewriting its outcome."
            )
        connection.execute(
            """
            UPDATE sessions
               SET ended_at = ?, outcome = ?
             WHERE session_id = ?
            """,
            (now(), outcome, session_id),
        )


def record_session_review(
    session_id: str,
    reviewed_by: str,
    summary: str,
    db_path: Path = DEFAULT_DB,
) -> int:
    with database(db_path) as connection:
        session = connection.execute(
            "SELECT 1 FROM sessions WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        if not session:
            raise ValueError(f"Unknown session: {session_id}")
        cursor = connection.execute(
            """
            INSERT INTO session_reviews (
                session_id, reviewed_by, reviewed_at, summary
            ) VALUES (?, ?, ?, ?)
            """,
            (session_id, reviewed_by, now(), summary),
        )
    return int(cursor.lastrowid)


# Titles name the AI that made the commit: "ai commit by claude: <summary>".
_TITLE = re.compile(
    r"^ai (commit|code review)(?: by ([A-Za-z0-9][A-Za-z0-9._-]*))?: "
)


def ai_label(*candidates: str | None) -> str:
    """First usable AI name, as a lowercase token safe for a commit title.

    A co-author identity such as "Claude Sonnet 5.5 <noreply@anthropic.com>"
    contributes only the name before the address.
    """
    for candidate in candidates:
        name = re.sub(r"<[^>]*>", "", candidate or "").strip().lower()
        token = re.sub(r"[^a-z0-9._-]+", "-", name).strip("-._")
        if token:
            return token
    raise ValueError(
        "Commit title needs the AI's name: pass --ai-name, --co-author or "
        "--prepared-by, or set $SDLC_AI_NAME."
    )


def named_title(message: str, label: str) -> str:
    """Return `message` as `ai commit by <label>: ...` or `ai code review by ...`.

    An existing named title is kept as written; the legacy unnamed prefix and
    a bare summary are given the name.
    """
    title = message.strip()
    match = _TITLE.match(title)
    if match and match.group(2):
        return title
    kind = match.group(1) if match else "commit"
    summary = title[match.end():] if match else title
    return f"ai {kind} by {label}: {summary}"


def commit_ready(
    workspace: Path,
    message: str,
    prepared_by: str,
    summary: str,
    findings: list[str],
    db_path: Path = DEFAULT_DB,
    validation_summary: str | None = None,
    co_author: str | None = None,
    ai_name: str | None = None,
) -> dict[str, Any]:
    resolved_workspace = require_under_dev(workspace, "Workspace")
    active_path = resolved_workspace / ".sdlc" / "active-story.json"
    if not active_path.is_file():
        raise ValueError(f"Tracking is not active: {active_path} was not found.")
    active = json.loads(active_path.read_text(encoding="utf-8-sig"))
    story_id = str(active["storyId"])
    repository_root = Path(
        _run_git(resolved_workspace, "rev-parse", "--show-toplevel")
    ).resolve()
    staged_files = [
        item
        for item in _run_git(
            repository_root,
            "diff",
            "--cached",
            "--name-only",
        ).splitlines()
        if item
    ]
    if not staged_files:
        raise ValueError(
            "No staged files are ready to commit. Stage the reviewed files "
            "before invoking commit-ready."
        )
    _validate_readme_state(resolved_workspace, repository_root)
    ledger = _active_ledger(active, resolved_workspace)
    _validate_handoff_inputs(resolved_workspace, ledger)
    previous_commit = _head_commit(repository_root)
    staged_tree = _staged_tree(repository_root)

    trailer = co_author or os.environ.get("SDLC_CO_AUTHOR")
    title = named_title(
        message,
        ai_label(ai_name, os.environ.get("SDLC_AI_NAME"), trailer, prepared_by),
    )
    gates = _enforce_gates(
        story_id, title, staged_files, db_path, previous_commit, staged_tree
    )
    policy_command = f'git -C "{repository_root}" commit -m "{title}"'
    policy = _commit_policy_decision(repository_root, policy_command)
    if policy.get("permissionDecision") != "allow":
        raise ValueError(str(policy.get("permissionDecisionReason")))

    # Another process may have committed or staged files while the gates were
    # being checked; refuse to commit a tree the recorded gates did not cover.
    if _head_commit(repository_root) != previous_commit or (
        _staged_tree(repository_root) != staged_tree
    ):
        raise ValueError(
            "HEAD or the staged tree changed while commit-ready was running "
            "(another process committed or staged files). Re-record the gates "
            "for the current stage and retry."
        )
    commit_args = ["commit", "-m", title]
    if trailer:
        commit_args.extend(["-m", f"Co-authored-by: {trailer}"])
    _run_git(repository_root, *commit_args)
    commit_hash = _run_git(repository_root, "rev-parse", "HEAD")
    report = _write_commit_analysis(
        ledger,
        resolved_workspace,
        repository_root,
        story_id,
        commit_hash,
        previous_commit,
        prepared_by,
        summary,
        findings,
        staged_files,
        gates,
        db_path,
        validation_summary,
    )
    return {
        "commit": commit_hash,
        "title": title,
        "gates": gates,
        "analysisReport": report["path"],
        "analysis": report["report"],
    }


def _run_git(cwd: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(cwd), *args],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise ValueError(completed.stderr.strip() or completed.stdout.strip())
    return completed.stdout.strip()


def _validate_readme_state(workspace: Path, repository_root: Path) -> None:
    readme = workspace / "README.md"
    if not readme.is_file():
        raise ValueError(f"Commit readiness requires README.md: {readme}")
    relative = readme.relative_to(repository_root)
    tracked = subprocess.run(
        [
            "git",
            "-C",
            str(repository_root),
            "ls-files",
            "--error-unmatch",
            str(relative),
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    status = _run_git(
        repository_root,
        "status",
        "--porcelain",
        "--",
        str(relative),
    )
    if tracked.returncode != 0 and not status.startswith("A"):
        raise ValueError("README.md must be tracked or staged before commit readiness.")
    if status and len(status) >= 2 and status[1] != " ":
        raise ValueError(
            "README.md has unstaged changes. Reconcile and stage it before "
            "commit readiness."
        )


def _validate_handoff_inputs(workspace: Path, ledger: Path) -> None:
    readme = workspace / "README.md"
    story = ledger / "story.md"
    if not readme.is_file():
        raise ValueError(f"Commit handoff requires README.md: {readme}")
    if not story.is_file():
        raise ValueError(f"Commit handoff requires tracked story: {story}")
    (ledger / "reviews").mkdir(parents=True, exist_ok=True)


def _commit_policy_decision(
    repository_root: Path,
    command: str,
) -> dict[str, Any]:
    script = HOOK_SCRIPT_ROOT / "scope_hook.py"
    completed = subprocess.run(
        [sys.executable, str(script)],
        input=json.dumps(
            {
                "hookEventName": "preToolUse",
                "cwd": str(repository_root),
                "toolName": "powershell",
                "toolArgs": {"command": command},
            }
        ),
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise ValueError(
            completed.stderr.strip() or "Commit policy validation failed."
        )
    try:
        output = json.loads(completed.stdout)
        decision = output["hookSpecificOutput"]
    except (json.JSONDecodeError, KeyError) as error:
        raise ValueError(
            "Commit policy hook returned an unusable response: "
            + (completed.stderr.strip() or completed.stdout.strip() or "(empty)")
        ) from error
    return decision


def _active_ledger(active: dict[str, Any], workspace: Path) -> Path:
    configured = Path(active["ledgerPath"])
    return require_under_dev(
        configured if configured.is_absolute() else workspace / configured,
        "Ledger",
    )


def _write_commit_analysis(
    ledger: Path,
    workspace: Path,
    repository_root: Path,
    story_id: str,
    commit_hash: str,
    previous_commit: str | None,
    prepared_by: str,
    summary: str,
    findings: list[str],
    staged_files: list[str],
    gates: dict[str, str | None],
    db_path: Path,
    validation_summary: str | None,
) -> dict[str, Any]:
    reviews = ledger / "reviews"
    previous = _latest_commit_analysis(reviews)
    cutoff = previous["generatedAt"] if previous else None
    metrics, _ = _commit_evidence(story_id, None, db_path)
    incremental_metrics, derived_findings = _commit_evidence(
        story_id,
        cutoff,
        db_path,
    )
    session_report_count, _ = _session_report_evidence(
        ledger,
        workspace,
        None,
    )
    incremental_session_reports, session_report_findings = _session_report_evidence(
        ledger,
        workspace,
        cutoff,
    )
    metrics["sessionReports"] = session_report_count
    incremental_metrics["sessionReports"] = incremental_session_reports
    previous_findings = set(previous.get("importantFindings", [])) if previous else set()
    combined = list(
        dict.fromkeys(
            [*findings, *session_report_findings, *derived_findings]
        )
    )
    important_findings = (
        combined
        if previous is None
        else [finding for finding in combined if finding not in previous_findings]
    )
    # Stated for every commit that has no telemetry of its own. It sits after
    # the de-duplication on purpose: a finding already reported on an earlier
    # commit is still true here, and dropping it would make an unmeasured
    # commit look measured.
    if (
        incremental_metrics.get("sessions") == 0
        and incremental_metrics.get("events") == 0
    ):
        important_findings.append(
            "No session or event telemetry was recorded for this commit; "
            "duration, retries and cost cannot be measured."
        )
    comparison = _metric_comparison(previous, metrics)
    generated_at = now()
    report = {
        "commit": commit_hash,
        "previousCommit": previous_commit,
        "generatedAt": generated_at,
        "preparedBy": prepared_by,
        "scope": "accumulated" if previous is None else "sincePreviousCommit",
        "summary": summary,
        "stagedFiles": staged_files,
        "gates": gates,
        "importantFindings": important_findings,
        "validation": {
            "status": "recorded" if validation_summary else "notRecorded",
            "summary": validation_summary,
        },
        "metrics": metrics,
        "evidenceSincePrevious": (
            incremental_metrics if previous is not None else None
        ),
        "comparison": comparison,
        "handoff": _commit_handoff(
            workspace,
            ledger,
            repository_root,
            commit_hash,
            staged_files,
            gates,
            prepared_by,
            generated_at,
            validation_summary,
        ),
    }
    path = reviews / f"commit-{commit_hash}-analysis.json"
    _atomic_write(path, json.dumps(report, indent=2) + "\n")
    return {"path": str(path), "report": report}


def _commit_handoff(
    workspace: Path,
    ledger: Path,
    repository_root: Path,
    commit_hash: str,
    committed_files: list[str],
    gates: dict[str, str | None],
    prepared_by: str,
    verified_at: str,
    validation_summary: str | None,
) -> dict[str, Any]:
    readme = workspace / "README.md"
    story = ledger / "story.md"
    if not readme.is_file():
        raise ValueError(f"Commit handoff requires README.md: {readme}")
    if not story.is_file():
        raise ValueError(f"Commit handoff requires tracked story: {story}")
    committed: list[dict[str, str | None]] = []
    for file_path in committed_files:
        try:
            blob = _run_git(
                repository_root,
                "rev-parse",
                f"{commit_hash}:{file_path}",
            )
        except ValueError:
            blob = None
        committed.append({"path": file_path, "blob": blob})
    return {
        "preparedFor": "fresh session or LLM review",
        "verifiedAt": verified_at,
        "synchronizedBy": prepared_by,
        "attestation": (
            "README, tracked story, implementation, and available evidence "
            "were reconciled before the local commit."
        ),
        "validation": {
            "status": "recorded" if validation_summary else "notRecorded",
            "summary": validation_summary,
        },
        "gates": gates,
        "readme": {
            "path": str(readme),
            "sha256": hashlib.sha256(readme.read_bytes()).hexdigest(),
        },
        "story": {
            "path": str(story),
            "sha256": hashlib.sha256(story.read_bytes()).hexdigest(),
        },
        "committedFiles": committed,
        "reviewInstructions": [
            "Read the concise README for operation, architecture, and limits.",
            "Read story.md for detailed intent, acceptance, and decisions.",
            "Review committed files at the recorded Git blob IDs.",
            "Verify important findings, metric deltas, and residual risks.",
        ],
    }


def _session_report_evidence(
    ledger: Path,
    workspace: Path,
    cutoff: str | None,
) -> tuple[int, list[str]]:
    candidates = {
        *(
            (ledger / "reviews").glob("*session-analysis*.json")
            if (ledger / "reviews").is_dir()
            else []
        ),
        *(
            (workspace / "reports" / "generated").glob(
                "*session-analysis*.json"
            )
            if (workspace / "reports" / "generated").is_dir()
            else []
        ),
    }
    reports: list[dict[str, Any]] = []
    for path in candidates:
        report = json.loads(path.read_text(encoding="utf-8-sig"))
        generated_at = report.get("generatedAt")
        if cutoff and generated_at:
            if datetime.fromisoformat(str(generated_at)) <= datetime.fromisoformat(
                cutoff
            ):
                continue
        reports.append(report)
    findings: list[str] = []
    for report in reports:
        session_id = report.get("coverage", {}).get("sessionId", "unknown")
        intention = report.get("intention")
        if intention:
            findings.append(f"Session {session_id} intention: {intention}")
        assessment = report.get("assessment", {})
        root_cause = assessment.get("rootCause")
        corrective_action = assessment.get("correctiveAction")
        if root_cause:
            finding = f"Session {session_id} finding: {root_cause}"
            if corrective_action:
                finding += f" Corrective action: {corrective_action}"
            findings.append(finding)
        findings.extend(report.get("importantFindings", []))
    return len(reports), findings


def _latest_commit_analysis(reviews: Path) -> dict[str, Any] | None:
    if not reviews.is_dir():
        return None
    candidates = sorted(
        reviews.glob("commit-*-analysis.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        return None
    return json.loads(candidates[0].read_text(encoding="utf-8-sig"))


def _commit_evidence(
    story_id: str,
    cutoff: str | None,
    db_path: Path,
) -> tuple[dict[str, Any], list[str]]:
    initialize(db_path)
    time_filter = " AND timestamp > ?" if cutoff else ""
    session_filter = " AND started_at > ?" if cutoff else ""
    pending_review_filter = " AND s.started_at > ?" if cutoff else ""
    parameters: tuple[Any, ...] = (story_id, cutoff) if cutoff else (story_id,)
    with database(db_path) as connection:
        events = connection.execute(
            f"""
            SELECT e.*,
                   COALESCE(
                       (
                           SELECT r.summary
                             FROM resolutions r
                            WHERE r.failure_event_id = e.event_id
                            ORDER BY r.created_at DESC, r.resolution_id DESC
                            LIMIT 1
                       ),
                       e.resolution
                   ) AS effective_resolution
              FROM events e
             WHERE e.story_id = ?{time_filter}
             ORDER BY e.timestamp
            """,
            parameters,
        ).fetchall()
        sessions = connection.execute(
            f"""
            SELECT *
              FROM sessions
             WHERE story_id = ?{session_filter}
             ORDER BY started_at
            """,
            parameters,
        ).fetchall()
        pending_reviews = connection.execute(
            f"""
            SELECT COUNT(*)
              FROM sessions s
             WHERE s.story_id = ?
               {pending_review_filter}
               AND NOT EXISTS (
                   SELECT 1
                     FROM session_reviews sr
                    WHERE sr.session_id = s.session_id
               )
            """,
            parameters,
        ).fetchone()[0]
    failures = [event for event in events if not event["success"]]
    metrics = {
        "sessions": len(sessions),
        "events": len(events),
        "toolCalls": sum(event["tool"] is not None for event in events),
        "failedToolCalls": sum(
            event["tool"] is not None and not event["success"] for event in events
        ),
        "resolvedFailures": sum(
            not event["success"] and bool(event["effective_resolution"])
            for event in events
        ),
        "unresolvedFailures": sum(
            not event["success"] and not event["effective_resolution"]
            for event in events
        ),
        "pendingSessionReviews": pending_reviews,
    }
    derived = [
        (
            f"{event['error_code'] or 'UNCLASSIFIED'}: "
            f"{event['failure_message'] or event['category'] or 'Failure'}"
            + (
                f" Resolved by: {event['effective_resolution']}"
                if event["effective_resolution"]
                else " Remains unresolved."
            )
        )
        for event in failures
    ]
    return metrics, derived


def _metric_comparison(
    previous: dict[str, Any] | None,
    current: dict[str, Any],
) -> dict[str, Any] | None:
    if previous is None:
        return None
    previous_metrics = previous.get("metrics", {})
    deltas = {
        key: current_value - int(previous_metrics.get(key, 0))
        for key, current_value in current.items()
    }
    risk_metrics = {
        "failedToolCalls",
        "unresolvedFailures",
        "pendingSessionReviews",
    }
    return {
        "previousCommit": previous.get("commit"),
        "deltas": deltas,
        "improvements": [
            key for key in risk_metrics if deltas.get(key, 0) < 0
        ],
        "regressions": [
            key for key in risk_metrics if deltas.get(key, 0) > 0
        ],
    }


def record_event(
    story_id: str,
    event_type: str,
    session_id: str | None = None,
    tool: str | None = None,
    category: str | None = None,
    success: bool = True,
    duration_ms: int | None = None,
    error_code: str | None = None,
    failure_message: str | None = None,
    resolution: str | None = None,
    importance: str = "normal",
    meaningful_progress: bool | None = None,
    details: dict[str, Any] | None = None,
    db_path: Path = DEFAULT_DB,
) -> tuple[int, bool]:
    if not success and not failure_message:
        raise ValueError("Failed events require --failure-message.")
    if resolution and success:
        raise ValueError("Use resolve-event to link a resolution to a failed event.")
    if meaningful_progress is not None:
        if event_type != "Iteration":
            raise ValueError("Progress can only be recorded on an Iteration event.")
        if session_id is None:
            raise ValueError("Iteration progress requires a session.")
    with database(db_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO events (
                story_id, session_id, timestamp, event_type, tool, category,
                success, duration_ms, error_code, failure_message, resolution,
                importance, meaningful_progress, details_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                story_id,
                session_id,
                now(),
                event_type,
                tool,
                category,
                int(success),
                duration_ms,
                error_code,
                failure_message,
                resolution,
                importance,
                None if meaningful_progress is None else int(meaningful_progress),
                json.dumps(details, sort_keys=True) if details else None,
            ),
        )
        stalled = _is_stalled(connection, story_id, session_id)
        return int(cursor.lastrowid), stalled


def _is_stalled(
    connection: sqlite3.Connection,
    story_id: str,
    session_id: str | None,
    threshold: int = 3,
) -> bool:
    if session_id is None:
        # A stall is a per-session signal; without a session there is nothing
        # to count, and `session_id = NULL` would silently return no rows.
        return False
    rows = connection.execute(
        """
        SELECT meaningful_progress
          FROM events
         WHERE story_id = ?
           AND session_id = ?
           AND event_type = 'Iteration'
           AND meaningful_progress IS NOT NULL
         ORDER BY event_id DESC
         LIMIT ?
        """,
        (story_id, session_id, threshold),
    ).fetchall()
    return len(rows) == threshold and all(row["meaningful_progress"] == 0 for row in rows)


def record_decision(
    story_id: str,
    summary: str,
    rationale: str | None,
    session_id: str | None,
    db_path: Path = DEFAULT_DB,
) -> int:
    with database(db_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO decisions (
                story_id, session_id, summary, rationale, created_at
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (story_id, session_id, summary, rationale, now()),
        )
        return int(cursor.lastrowid)


def record_resolution(
    failure_event_id: int,
    summary: str,
    session_id: str | None,
    db_path: Path = DEFAULT_DB,
) -> int:
    with database(db_path) as connection:
        failure = connection.execute(
            """
            SELECT story_id
              FROM events
             WHERE event_id = ? AND success = 0
            """,
            (failure_event_id,),
        ).fetchone()
        if not failure:
            raise ValueError(f"Unknown failed event: {failure_event_id}")
        if session_id is not None:
            session = connection.execute(
                """
                SELECT 1 FROM sessions
                 WHERE session_id = ? AND story_id = ?
                """,
                (session_id, failure["story_id"]),
            ).fetchone()
            if not session:
                raise ValueError(
                    f"Session {session_id} does not belong to failure story."
                )
        cursor = connection.execute(
            """
            INSERT INTO resolutions (
                failure_event_id, session_id, summary, created_at
            ) VALUES (?, ?, ?, ?)
            """,
            (failure_event_id, session_id, summary, now()),
        )
        return int(cursor.lastrowid)


def record_customization(
    component: str,
    version: str,
    source_path: Path,
    model: str | None,
    metadata: dict[str, Any] | None,
    db_path: Path = DEFAULT_DB,
) -> int:
    resolved = require_under_dev(source_path, "Customization source")
    digest = hashlib.sha256(resolved.read_bytes()).hexdigest()
    with database(db_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO customization_versions (
                component, version, source_path, content_sha256, model,
                recorded_at, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                component,
                version,
                str(resolved),
                digest,
                model,
                now(),
                json.dumps(metadata, sort_keys=True) if metadata else None,
            ),
        )
        return int(cursor.lastrowid)


GATE_NAMES = ("analysis", "implementation", "review", "customization", "docs")
GATE_STATUSES = ("passed", "failed", "waived")
# Gates that attest to the exact staged content, not just the story's intent.
TREE_BOUND_GATES = {"implementation", "customization"}
# Intent and acceptance outlive a single commit; they are not re-recorded.
STORY_LEVEL_GATES = {"analysis"}
_CUSTOMIZATION_PREFIXES = ("policy/", "skills/", "core/", "scripts/")
_CUSTOMIZATION_FILES = {
    "AGENTS.md",
    "CLAUDE.md",
    "onboard.cmd",
    "onboard-all.cmd",
    "reports.cmd",
}


def _is_customization_path(path: str) -> bool:
    # Strip only a leading "./"; lstrip("./") would eat the dot of ".agents/".
    normalized = path.replace("\\", "/").removeprefix("./")
    return bool(
        normalized.startswith(_CUSTOMIZATION_PREFIXES)
        or normalized.startswith(".agents/skills/")
        or "-customization/" in normalized
        or normalized in _CUSTOMIZATION_FILES
    )


def required_gates(message: str, staged_files: list[str]) -> list[str]:
    """Gates a commit of this shape must already have passed or waived."""
    gates = (
        {"review", "docs"}
        if (_TITLE.match(message) or [None, None])[1] == "code review"
        else {"analysis", "implementation"}
    )
    if any(_is_customization_path(path) for path in staged_files):
        gates.add("customization")
    return sorted(gates)


def _resolve_gate_artifact(workspace: Path, ledger: Path, artifact: str) -> Path:
    raw = Path(artifact)
    candidates = [raw] if raw.is_absolute() else [workspace / raw, ledger / raw]
    for candidate in candidates:
        resolved = require_under_dev(candidate, "Gate artifact")
        if resolved.is_file():
            return resolved
    return require_under_dev(candidates[0], "Gate artifact")


def _head_commit(cwd: Path) -> str | None:
    try:
        return _run_git(cwd, "rev-parse", "HEAD")
    except ValueError:
        return None


VERIFY_TIMEOUT_SECONDS = 600


def run_verify(workspace: Path) -> dict[str, Any]:
    """Run the repository's verification suite and return structured evidence.

    `verify.py` exercises the working tree, not the index, so an unstaged
    change would make its result describe something other than the commit.
    """
    resolved = require_under_dev(workspace, "Workspace")
    try:
        root = Path(_run_git(resolved, "rev-parse", "--show-toplevel")).resolve()
    except ValueError as error:
        raise ValueError(
            f"--run-verify requires a Git repository: {resolved}"
        ) from error
    script = root / "scripts" / "verify.py"
    if not script.is_file():
        raise ValueError(f"Verification script was not found: {script}")
    dirty = subprocess.run(
        ["git", "-C", str(root), "diff", "--quiet"],
        capture_output=True,
        check=False,
    )
    if dirty.returncode != 0:
        raise ValueError(
            "verify.py runs against the working tree; commit, stash or revert "
            "unstaged changes before using --run-verify."
        )
    tree_before = _staged_tree(root)
    try:
        completed = subprocess.run(
            [sys.executable, str(script)],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=VERIFY_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as error:
        raise ValueError(
            f"verify.py exceeded {VERIFY_TIMEOUT_SECONDS}s; gate not recorded."
        ) from error
    if _staged_tree(root) != tree_before:
        raise ValueError(
            "The staged tree changed while verify.py ran, so its result does "
            "not describe the commit. Stage first, then retry."
        )
    output = (completed.stdout or "") + (completed.stderr or "")
    match = re.search(r"Ran (\d+) tests?", output)
    return {
        "command": "python scripts/verify.py",
        "exitCode": completed.returncode,
        "testCount": int(match.group(1)) if match else None,
        "treeHash": tree_before,
        "result": "passed" if completed.returncode == 0 else "failed",
        "outputTail": "\n".join(output.splitlines()[-40:]),
    }


def _staged_tree(cwd: Path) -> str | None:
    try:
        return _run_git(cwd, "write-tree")
    except ValueError:
        return None


def _gate_baseline(workspace: Path) -> tuple[str | None, str | None]:
    """HEAD and staged-tree hashes of the repository containing `workspace`.

    `git write-tree` is resolved from the repository root because it is
    prefix-sensitive when run from a subdirectory. A workspace that is not a
    Git repository (or has no commit yet) yields `None`, which still compares
    equal for fixtures without history.
    """
    try:
        root = Path(_run_git(workspace, "rev-parse", "--show-toplevel")).resolve()
    except ValueError:
        return None, None
    return _head_commit(root), _staged_tree(root)


def record_gate(
    workspace: Path,
    story_id: str,
    gate: str,
    status: str = "passed",
    evidence: str = "",
    approved_by: str | None = None,
    recorded_by: str | None = None,
    artifact: str | None = None,
    session_id: str | None = None,
    details: dict[str, Any] | None = None,
    db_path: Path = DEFAULT_DB,
) -> dict[str, Any]:
    """Record one handoff gate and write its reviewable artifact under the ledger.

    A pass or a waiver needs a named approver and evidence; a failed gate keeps
    the reason and blocks the commit it was meant to authorise.
    """
    if gate not in GATE_NAMES:
        raise ValueError(f"Gate must be one of: {', '.join(GATE_NAMES)}")
    if status not in GATE_STATUSES:
        raise ValueError(f"Status must be one of: {', '.join(GATE_STATUSES)}")
    evidence = (evidence or "").strip()
    approver = (approved_by or "").strip()
    recorder = (recorded_by or "").strip() or None
    if status in {"passed", "waived"}:
        if not evidence:
            raise ValueError("A passed or waived gate requires --evidence.")
        if not approver:
            raise ValueError("A passed or waived gate requires --approved-by.")

    resolved_workspace = require_under_dev(workspace, "Workspace")
    active_path = resolved_workspace / ".sdlc" / "active-story.json"
    if not active_path.is_file():
        raise ValueError(f"Tracking is not active: {active_path} was not found.")
    active = json.loads(active_path.read_text(encoding="utf-8-sig"))
    if str(active.get("storyId")) != story_id:
        raise ValueError(
            f"Story {story_id} is not the active story "
            f"({active.get('storyId')}); gate the active story or fix the ID."
        )
    ledger = _active_ledger(active, resolved_workspace)
    initialize(db_path)
    head_commit, staged_tree = _gate_baseline(resolved_workspace)
    verification = (details or {}).get("verification")
    verified_tree = (
        verification.get("treeHash") if isinstance(verification, dict) else None
    )
    if verified_tree and staged_tree and verified_tree != staged_tree:
        raise ValueError(
            "The staged tree changed after verify.py ran; re-run the gate "
            "with --run-verify so the result describes the staged content."
        )
    if gate not in TREE_BOUND_GATES:
        staged_tree = None

    artifact_path: str | None = None
    artifact_sha256: str | None = None
    if artifact:
        resolved_artifact = _resolve_gate_artifact(
            resolved_workspace, ledger, artifact
        )
        if status != "failed" and not resolved_artifact.is_file():
            raise ValueError(f"Gate artifact was not found: {artifact}")
        artifact_path = str(resolved_artifact)
        if resolved_artifact.is_file():
            artifact_sha256 = hashlib.sha256(
                resolved_artifact.read_bytes()
            ).hexdigest()

    timestamp = now()
    gates_dir = ledger / "gates"
    gates_dir.mkdir(parents=True, exist_ok=True)
    report_path = gates_dir / f"{gate}.md"
    lines = [
        "---",
        f'storyId: "{story_id}"',
        f'gate: "{gate}"',
        f'status: "{status}"',
        f'approvedBy: "{approver}"',
        f'recordedAt: "{timestamp}"',
    ]
    if recorder:
        lines.append(f'recordedBy: "{recorder}"')
    if head_commit:
        lines.append(f'headCommit: "{head_commit}"')
    if staged_tree:
        lines.append(f'treeHash: "{staged_tree}"')
    verification = (details or {}).get("verification")
    if isinstance(verification, dict):
        lines.append(
            "verification: "
            f"\"{verification.get('result')} "
            f"({verification.get('testCount')} tests, "
            f"exit {verification.get('exitCode')})\""
        )
    if artifact_path:
        lines.append(f'artifact: "{artifact_path}"')
    if artifact_sha256:
        lines.append(f'artifactSha256: "{artifact_sha256}"')
    lines.extend(["---", "", f"# {gate} gate", "", evidence or "(no evidence recorded)"])
    _atomic_write(report_path, "\n".join(lines) + "\n")

    with database(db_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO gates (
                story_id, session_id, gate, status, artifact_path,
                artifact_sha256, evidence, approved_by, recorded_by,
                recorded_at, head_commit, tree_hash, details_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                story_id,
                session_id,
                gate,
                status,
                artifact_path,
                artifact_sha256,
                evidence or "(no evidence recorded)",
                approver or "(not recorded)",
                recorder,
                timestamp,
                head_commit,
                staged_tree,
                json.dumps(details, sort_keys=True) if details else None,
            ),
        )
        gate_id = int(cursor.lastrowid)
    return {
        "gateId": gate_id,
        "storyId": story_id,
        "gate": gate,
        "status": status,
        "approvedBy": approver,
        "recordedBy": recorder,
        "artifact": artifact_path,
        "artifactSha256": artifact_sha256,
        "headCommit": head_commit,
        "treeHash": staged_tree,
        "report": str(report_path),
    }


def gates_for_story(
    story_id: str,
    db_path: Path = DEFAULT_DB,
) -> dict[str, dict[str, Any]]:
    """Latest recorded state of each gate for a story."""
    initialize(db_path)
    with database(db_path) as connection:
        rows = connection.execute(
            """
            SELECT g.*
              FROM gates g
              JOIN (
                    SELECT gate, MAX(gate_id) AS gate_id
                      FROM gates
                     WHERE story_id = ?
                     GROUP BY gate
                   ) latest
                ON latest.gate_id = g.gate_id
            """,
            (story_id,),
        ).fetchall()
    return {row["gate"]: dict(row) for row in rows}


def _enforce_gates(
    story_id: str,
    message: str,
    staged_files: list[str],
    db_path: Path,
    head_commit: str | None,
    tree_hash: str | None,
) -> dict[str, str | None]:
    required = required_gates(message, staged_files)
    recorded = gates_for_story(story_id, db_path)
    missing = []
    for gate in required:
        record = recorded.get(gate) or {}
        status = record.get("status", "missing")
        recorded_head = record.get("head_commit") or None
        recorded_tree = record.get("tree_hash") or None
        if status not in {"passed", "waived"}:
            missing.append(f"{gate} ({status})")
        elif gate not in STORY_LEVEL_GATES and recorded_head != head_commit:
            missing.append(
                f"{gate} (stale: recorded for "
                f"{recorded_head or 'no commit'}, HEAD is "
                f"{head_commit or 'no commit'})"
            )
        elif gate in TREE_BOUND_GATES and recorded_tree != tree_hash:
            missing.append(
                f"{gate} (stale: staged tree changed since the gate was recorded)"
            )
    if missing:
        raise ValueError(
            "Missing or stale required handoff gate(s): "
            + ", ".join(missing)
            + ". Stage the reviewed files, then record each gate with "
            "`gate --gate <name> --evidence <what was checked> --approved-by "
            "<who approved>`; a waiver needs an approver and a reason."
        )
    return {gate: (recorded.get(gate) or {}).get("status") for gate in required}


def import_jsonl(
    story_id: str,
    source: Path,
    db_path: Path = DEFAULT_DB,
) -> int:
    items: list[tuple[int, dict[str, Any]]] = []
    for line_number, line in enumerate(
        source.read_text(encoding="utf-8-sig").splitlines(), start=1
    ):
        if not line.strip():
            continue
        item = json.loads(line)
        if not isinstance(item, dict):
            raise ValueError(f"Line {line_number}: expected a JSON object.")
        success = item.get("success", True)
        if not isinstance(success, bool):
            raise ValueError(
                f"Line {line_number}: success must be a JSON boolean."
            )
        items.append((line_number, item))

    with database(db_path) as connection:
        for line_number, item in items:
            success = item.get("success", True)
            failure_message = item.get("failureMessage")
            if not success and not failure_message:
                failure_message = f"Imported failure: {item.get('errorCode')}"
            try:
                connection.execute(
                    """
                    INSERT INTO events (
                        story_id, session_id, timestamp, event_type, tool,
                        category, success, duration_ms, error_code,
                        failure_message, resolution, importance
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        story_id,
                        item.get("sessionId"),
                        item.get("timestamp") or now(),
                        item.get("event", "ImportedEvent"),
                        item.get("tool"),
                        item.get("category"),
                        int(success),
                        item.get("durationMs"),
                        item.get("errorCode"),
                        failure_message,
                        item.get("resolution"),
                        "important" if not success else "normal",
                    ),
                )
            except sqlite3.Error as error:
                raise ValueError(f"Line {line_number}: {error}") from error
    return len(items)


def analyze_jsonl(
    source: Path,
    story_id: str | None = None,
    session_id: str | None = None,
) -> dict[str, Any]:
    events: list[dict[str, Any]] = []
    for line_number, line in enumerate(
        source.read_text(encoding="utf-8-sig").splitlines(), start=1
    ):
        if not line.strip():
            continue
        item = json.loads(line)
        if not isinstance(item, dict):
            raise ValueError(f"Line {line_number}: expected a JSON object.")
        if story_id is not None and item.get("storyId") != story_id:
            continue
        if session_id is not None and item.get("sessionId") != session_id:
            continue
        success = item.get("success", True)
        if not isinstance(success, bool):
            raise ValueError(
                f"Line {line_number}: success must be a JSON boolean."
            )
        events.append(item)

    tool_events = [
        item for item in events if item.get("event") == "PostToolUse"
    ]
    failures = [item for item in tool_events if not item.get("success", True)]
    timestamps = [
        datetime.fromisoformat(str(item["timestamp"]))
        for item in events
        if item.get("timestamp")
    ]
    errors = Counter(
        str(item.get("errorCode") or "UNCLASSIFIED") for item in failures
    )
    sessions = sorted(
        {
            str(item["sessionId"])
            for item in events
            if item.get("sessionId") is not None
        }
    )
    return {
        "source": str(source.resolve()),
        "storyId": story_id,
        "sessionId": session_id,
        "eventCount": len(events),
        "sessions": sessions,
        "firstEventAt": min(timestamps).isoformat() if timestamps else None,
        "lastEventAt": max(timestamps).isoformat() if timestamps else None,
        "wallClockDurationMs": (
            int((max(timestamps) - min(timestamps)).total_seconds() * 1000)
            if timestamps
            else 0
        ),
        "toolCalls": len(tool_events),
        "failedToolCalls": len(failures),
        "toolFailureRate": (
            len(failures) / len(tool_events) if tool_events else 0.0
        ),
        "topErrors": errors.most_common(5),
        "failures": [
            {
                "timestamp": item.get("timestamp"),
                "sessionId": item.get("sessionId"),
                "tool": item.get("tool"),
                "errorCode": item.get("errorCode"),
                "failureMessage": item.get("failureMessage"),
                "resolution": item.get("resolution"),
            }
            for item in failures
        ],
    }


def tracking_report(
    workspace: Path,
    session_id: str | None = None,
    db_path: Path = DEFAULT_DB,
    include_stale_analysis: bool = False,
) -> dict[str, Any]:
    active_path = workspace.resolve() / ".sdlc" / "active-story.json"
    if not active_path.is_file():
        raise ValueError(f"Tracking is not active: {active_path} was not found.")
    active = json.loads(active_path.read_text(encoding="utf-8-sig"))
    configured_ledger = Path(active["ledgerPath"])
    ledger_path = (
        configured_ledger
        if configured_ledger.is_absolute()
        else active_path.parent.parent / configured_ledger
    ).resolve()
    event_path = ledger_path / "events.jsonl"
    record_project_use(workspace, db_path)
    recent_sessions = _recent_story_sessions(active["storyId"], db_path)
    sessions_needing_review = [
        session
        for session in recent_sessions
        if session["reviewStatus"] == "pending"
    ]
    reviewed_sessions = [
        {
            key: value
            for key, value in session.items()
            if key != "failures"
        }
        for session in recent_sessions
        if session["reviewStatus"] == "reviewed"
    ]
    evidence_times = [
        timestamp
        for session in recent_sessions
        for timestamp in (
            session["startedAt"],
            session["endedAt"],
            session["lastEventAt"],
        )
        if timestamp
    ]
    newest_evidence_at = max(
        evidence_times,
        key=datetime.fromisoformat,
        default=None,
    )
    retrospective = _latest_session_analysis(
        ledger_path,
        workspace.resolve(),
        newest_evidence_at,
    )
    if not event_path.is_file():
        health = _tracking_health(
            workspace.resolve(),
            newest_evidence_at,
            None,
        )
        report = {
            "trackingEnabled": True,
            **health,
            "storyId": active["storyId"],
            "ledgerPath": str(ledger_path),
            "eventPath": str(event_path),
            "sessionsNeedingReview": sessions_needing_review,
            "reviewedSessions": reviewed_sessions,
            "hookLedger": {
                "eventCount": 0,
                "message": (
                    "No tracking events have been captured. Start a new agent "
                    "session after enabling the tracking-only hooks."
                ),
            },
        }
        _attach_retrospective(report, retrospective, include_stale_analysis)
        return report
    analysis = analyze_jsonl(event_path, active["storyId"], session_id)
    health = _tracking_health(
        workspace.resolve(),
        newest_evidence_at,
        analysis.get("lastEventAt"),
    )
    report = {
        "trackingEnabled": True,
        **health,
        "storyId": active["storyId"],
        "ledgerPath": str(ledger_path),
        "eventPath": str(event_path),
        "sessionsNeedingReview": sessions_needing_review,
        "reviewedSessions": reviewed_sessions,
        "hookLedger": analysis,
    }
    _attach_retrospective(report, retrospective, include_stale_analysis)
    return report


def _tracking_health(
    workspace: Path,
    coordination_evidence_at: str | None,
    hook_evidence_at: str | None,
) -> dict[str, Any]:
    evidence = [
        datetime.fromisoformat(timestamp)
        for timestamp in (coordination_evidence_at, hook_evidence_at)
        if timestamp
    ]
    latest = max(evidence, default=None)
    observed_at = datetime.now(timezone.utc).astimezone()
    warnings: list[str] = []
    restart_required = False

    hook_paths = (
        workspace / ".github" / "hooks" / "copilot-sdlc.json",
        workspace / ".sdlc" / "hooks" / "tracking_hook.py",
    )
    hook_updates = [
        datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).astimezone()
        for path in hook_paths
        if path.is_file()
    ]
    latest_hook_update = max(hook_updates, default=None)

    if latest is None:
        status = "missing"
        age_seconds = None
        warnings.append(
            "CRITICAL: tracking is configured but no session evidence has "
            "been captured."
        )
    else:
        age_seconds = max(0, int((observed_at - latest).total_seconds()))
        status = (
            "stale"
            if observed_at - latest > TRACKING_STALE_AFTER
            else "healthy"
        )
        if status == "stale":
            warnings.append(
                "CRITICAL: the newest tracking evidence is older than "
                f"{int(TRACKING_STALE_AFTER.total_seconds() // 60)} minutes. "
                "This report is historical, not current-session evidence."
            )

    if latest_hook_update and (latest is None or latest_hook_update > latest):
        restart_required = True
        status = "stale" if latest else "missing"
        warnings.append(
            "Tracking hooks changed after the newest captured evidence. "
            "Start a new agent session before relying on this report."
        )

    return {
        "trackingHealthy": status == "healthy",
        "trackingStatus": status,
        "latestEvidenceAt": latest.isoformat() if latest else None,
        "evidenceAgeSeconds": age_seconds,
        "latestHookUpdateAt": (
            latest_hook_update.isoformat() if latest_hook_update else None
        ),
        "restartRequired": restart_required,
        "warnings": warnings,
    }


def _attach_retrospective(
    report: dict[str, Any],
    retrospective: dict[str, Any] | None,
    include_stale_analysis: bool,
) -> None:
    if retrospective is None:
        return
    if retrospective["freshness"]["status"] != "stale":
        report["latestSessionAnalysis"] = retrospective
        return
    historical = {
        "path": retrospective["path"],
        "freshness": retrospective["freshness"],
        "sessionId": retrospective["report"].get("coverage", {}).get(
            "sessionId"
        ),
        "intention": retrospective["report"].get("intention"),
        "note": (
            "Full stale analysis is omitted by default. Use "
            "--include-stale-analysis to inspect it."
        ),
    }
    if include_stale_analysis:
        historical["report"] = retrospective["report"]
    report["historicalSessionAnalysis"] = historical


def _latest_session_analysis(
    ledger_path: Path,
    workspace: Path,
    newest_evidence_at: str | None,
) -> dict[str, Any] | None:
    candidates = sorted(
        [
            *(
                (ledger_path / "reviews").glob("*session-analysis*.json")
                if (ledger_path / "reviews").is_dir()
                else []
            ),
            *(
                (workspace / "reports" / "generated").glob(
                    "*session-analysis*.json"
                )
                if (workspace / "reports" / "generated").is_dir()
                else []
            ),
        ],
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        return None
    path = candidates[0]
    analysis = json.loads(path.read_text(encoding="utf-8-sig"))
    if not analysis.get("intention"):
        intention = _story_intent(ledger_path / "story.md")
        if intention:
            analysis["intention"] = intention
            analysis["intentionSource"] = "story.md fallback"
    definitions = analysis.setdefault("metricDefinitions", {})
    definitions.setdefault(
        "cancelledTurns",
        (
            "Captured assistant turns whose session API status was cancelled "
            "before normal completion, commonly because the user stopped or "
            "replaced a request or execution was interrupted. This does not "
            "mean completed tool effects were rolled back, and it is separate "
            "from failedToolCalls."
        ),
    )
    generated_at = analysis.get("generatedAt")
    stale = False
    if generated_at and newest_evidence_at:
        stale = datetime.fromisoformat(newest_evidence_at) > datetime.fromisoformat(
            str(generated_at)
        )
    freshness = {
        "status": "stale" if stale else "current",
        "generatedAt": generated_at,
        "newerEvidenceAt": newest_evidence_at if stale else None,
    }
    if stale:
        freshness["reason"] = (
            "Newer coordination-session evidence exists. This retrospective "
            "is retained for history but is not the latest session state."
        )
    return {
        "path": str(path),
        "freshness": freshness,
        "report": analysis,
    }


def _recent_story_sessions(
    story_id: str,
    db_path: Path,
    limit: int = 5,
) -> list[dict[str, Any]]:
    with database(db_path) as connection:
        rows = connection.execute(
            """
            SELECT s.session_id,
                   s.role,
                   s.model,
                   s.host,
                   s.started_at,
                   s.ended_at,
                   s.outcome,
                   COUNT(e.event_id) AS event_count,
                   SUM(CASE WHEN e.tool IS NOT NULL THEN 1 ELSE 0 END)
                       AS tool_calls,
                   SUM(
                       CASE WHEN e.tool IS NOT NULL AND e.success = 0
                            THEN 1 ELSE 0 END
                   ) AS failed_tool_calls,
                   MAX(e.timestamp) AS last_event_at
                   ,
                   (
                       SELECT sr.reviewed_by
                         FROM session_reviews sr
                        WHERE sr.session_id = s.session_id
                        ORDER BY sr.reviewed_at DESC, sr.review_id DESC
                        LIMIT 1
                   ) AS reviewed_by,
                   (
                       SELECT sr.reviewed_at
                         FROM session_reviews sr
                        WHERE sr.session_id = s.session_id
                        ORDER BY sr.reviewed_at DESC, sr.review_id DESC
                        LIMIT 1
                   ) AS reviewed_at,
                   (
                       SELECT sr.summary
                         FROM session_reviews sr
                        WHERE sr.session_id = s.session_id
                        ORDER BY sr.reviewed_at DESC, sr.review_id DESC
                        LIMIT 1
                   ) AS review_summary
              FROM sessions s
              LEFT JOIN events e ON e.session_id = s.session_id
             WHERE s.story_id = ?
             GROUP BY s.session_id,
                      s.role,
                      s.model,
                      s.host,
                      s.started_at,
                      s.ended_at,
                      s.outcome
             ORDER BY CASE WHEN reviewed_at IS NULL THEN 0 ELSE 1 END,
                      s.started_at DESC
             LIMIT ?
            """,
            (story_id, limit),
        ).fetchall()
        sessions = [
            {
                "sessionId": row["session_id"],
                "role": row["role"],
                "model": row["model"],
                "host": row["host"],
                "startedAt": row["started_at"],
                "endedAt": row["ended_at"],
                "outcome": row["outcome"],
                "eventCount": row["event_count"],
                "toolCalls": row["tool_calls"] or 0,
                "failedToolCalls": row["failed_tool_calls"] or 0,
                "lastEventAt": row["last_event_at"],
                "reviewStatus": (
                    "reviewed" if row["reviewed_at"] else "pending"
                ),
                "review": (
                    {
                        "reviewedBy": row["reviewed_by"],
                        "reviewedAt": row["reviewed_at"],
                        "summary": row["review_summary"],
                    }
                    if row["reviewed_at"]
                    else None
                ),
                "failures": [
                    {
                        "timestamp": event["timestamp"],
                        "tool": event["tool"],
                        "category": event["category"],
                        "errorCode": event["error_code"],
                        "failureMessage": event["failure_message"],
                        "resolution": event["resolution"],
                    }
                    for event in connection.execute(
                        """
                        SELECT timestamp,
                               tool,
                               category,
                               error_code,
                               failure_message,
                               resolution
                          FROM events
                         WHERE session_id = ?
                           AND success = 0
                         ORDER BY timestamp DESC
                         LIMIT 5
                        """,
                        (row["session_id"],),
                    ).fetchall()
                ],
            }
            for row in rows
        ]
    return sessions


def _story_intent(path: Path) -> str | None:
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8-sig")
    match = re.search(
        r"(?ms)^# Intent\s*\n+(.*?)(?=^# |\Z)",
        text,
    )
    if not match:
        return None
    return " ".join(match.group(1).split())


def generate_scorecard(
    story_id: str,
    outcome: str,
    runtime_verified: bool,
    db_path: Path = DEFAULT_DB,
    report_root: Path = DEFAULT_REPORT_ROOT,
) -> dict[str, Any]:
    report_root = require_under_dev(report_root, "Report root")
    report_root.mkdir(parents=True, exist_ok=True)
    with database(db_path) as connection:
        story = connection.execute(
            "SELECT * FROM stories WHERE story_id = ?", (story_id,)
        ).fetchone()
        if not story:
            raise ValueError(f"Unknown story: {story_id}")
        events = connection.execute(
            """
            SELECT * FROM events
             WHERE story_id = ? AND archived_at IS NULL
             ORDER BY event_id
            """,
            (story_id,),
        ).fetchall()
        summaries = connection.execute(
            """
            SELECT * FROM event_summaries
             WHERE story_id = ?
            """,
            (story_id,),
        ).fetchall()
        sessions = connection.execute(
            "SELECT * FROM sessions WHERE story_id = ? ORDER BY started_at",
            (story_id,),
        ).fetchall()

        timestamp_values = [row["timestamp"] for row in events]
        for row in summaries:
            if row["first_timestamp"]:
                timestamp_values.append(row["first_timestamp"])
            if row["last_timestamp"]:
                timestamp_values.append(row["last_timestamp"])
        timestamps = [datetime.fromisoformat(value) for value in timestamp_values]
        wall_clock_ms = (
            int((max(timestamps) - min(timestamps)).total_seconds() * 1000)
            if timestamps
            else 0
        )
        post_tools = [row for row in events if row["event_type"] == "PostToolUse"]
        failures = connection.execute(
            """
            SELECT e.*,
                   coalesce(
                       e.resolution,
                       (
                           SELECT group_concat(r.summary, '; ')
                             FROM resolutions r
                            WHERE r.failure_event_id = e.event_id
                       )
                   ) AS linked_resolution
              FROM events e
             WHERE e.story_id = ?
               AND e.event_type = 'PostToolUse'
               AND e.success = 0
             ORDER BY e.event_id
            """,
            (story_id,),
        ).fetchall()
        if outcome == "passed" and not events and not summaries:
            raise ValueError(
                "Cannot mark a story passed without recorded event evidence."
            )
        unresolved_failures = [
            row for row in failures if not row["linked_resolution"]
        ]
        if outcome == "passed" and unresolved_failures:
            identifiers = ", ".join(
                str(row["event_id"]) for row in unresolved_failures
            )
            raise ValueError(
                "Cannot mark a story passed with unresolved failed events: "
                f"{identifiers}"
            )
        report_id = uuid4().hex
        failure_path = report_root / f"{story_id}-{report_id}-failures.md"
        _write_failure_report(story_id, failures, failure_path)

        models = sorted({row["model"] for row in sessions if row["model"]})
        summarized_tool_calls = sum(
            row["event_count"]
            for row in summaries
            if row["event_type"] == "PostToolUse"
        )
        metrics = {
            "wallClockDurationMs": wall_clock_ms,
            "modelCalls": None,
            "inputTokens": None,
            "outputTokens": None,
            "cacheReadTokens": None,
            "cacheWriteTokens": None,
            "toolCalls": len(post_tools) + summarized_tool_calls,
            "failedToolCalls": {
                "value": len(failures),
                "details": str(failure_path),
            },
            "buildAttempts": sum(
                row["category"] == "build-attempt" for row in events
            )
            + sum(
                row["event_count"]
                for row in summaries
                if row["category"] == "build-attempt"
            ),
            "filesReread": sum(row["category"] == "file-reread" for row in events)
            + sum(
                row["event_count"]
                for row in summaries
                if row["category"] == "file-reread"
            ),
            "subagentsUsed": sum(
                row["event_type"] == "SubagentStart" for row in events
            )
            + sum(
                row["event_count"]
                for row in summaries
                if row["event_type"] == "SubagentStart"
            ),
            "models": models,
        }
        scorecard = {
            "storyId": story_id,
            "generatedAt": now(),
            "outcome": outcome,
            "runtimeVerified": runtime_verified,
            "metrics": metrics,
            "notes": [
                "Token fields remain null without authoritative runtime telemetry."
            ],
        }
        report_path = report_root / f"{story_id}-{report_id}-scorecard.json"
        _atomic_write(report_path, json.dumps(scorecard, indent=2))
        connection.execute(
            """
            INSERT INTO scorecards (
                story_id, generated_at, outcome, runtime_verified,
                metrics_json, report_path
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                story_id,
                scorecard["generatedAt"],
                outcome,
                int(runtime_verified),
                json.dumps(metrics, sort_keys=True),
                str(report_path),
            ),
        )
        return scorecard


def _write_failure_report(
    story_id: str,
    failures: list[sqlite3.Row],
    path: Path,
) -> None:
    lines = [
        f"# Failed tool calls for {story_id}",
        "",
        "| Event | Timestamp | Tool | Error | Failure | Resolution |",
        "|---:|---|---|---|---|---|",
    ]
    for row in failures:
        lines.append(
            "| {event_id} | {timestamp} | {tool} | {error} | {failure} | {resolution} |".format(
                event_id=row["event_id"],
                timestamp=_escape(row["timestamp"]),
                tool=_escape(row["tool"]),
                error=_escape(row["error_code"]),
                failure=_escape(row["failure_message"]),
                resolution=_escape(row["linked_resolution"] or "Unresolved"),
            )
        )
    if not failures:
        lines.append("| - | - | - | - | No failed tool calls | - |")
    _atomic_write(path, "\n".join(lines) + "\n")


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    temporary.write_text(content, encoding="utf-8")
    temporary.replace(path)


def _escape(value: Any) -> str:
    return str(value or "").replace("|", r"\|").replace("\n", " ")


def compact_events(
    older_than_days: int,
    purge_archived_days: int | None,
    db_path: Path = DEFAULT_DB,
) -> dict[str, int]:
    if older_than_days < 0:
        raise ValueError("older-than-days must be nonnegative.")
    if purge_archived_days is not None and purge_archived_days <= 0:
        raise ValueError("purge-archived-days must be greater than zero.")
    cutoff = (datetime.now(timezone.utc) - timedelta(days=older_than_days)).isoformat()
    timestamp = now()
    with database(db_path) as connection:
        rows = connection.execute(
            """
            SELECT story_id, substr(timestamp, 1, 10) AS event_date,
                   event_type, coalesce(tool, '') AS tool,
                   coalesce(category, '') AS category,
                   count(*) AS event_count,
                   coalesce(sum(duration_ms), 0) AS total_duration_ms,
                   min(timestamp) AS first_timestamp,
                   max(timestamp) AS last_timestamp
              FROM events
             WHERE archived_at IS NULL
               AND importance = 'trivial'
               AND success = 1
               AND event_type NOT IN ('Decision', 'Approval', 'Iteration')
               AND meaningful_progress IS NULL
               AND failure_message IS NULL
               AND resolution IS NULL
               AND error_code IS NULL
               AND timestamp < ?
             GROUP BY story_id, substr(timestamp, 1, 10),
                      event_type, tool, category
            """,
            (cutoff,),
        ).fetchall()
        for row in rows:
            connection.execute(
                """
                INSERT INTO event_summaries (
                    story_id, event_date, event_type, tool, category,
                    event_count, total_duration_ms, first_timestamp,
                    last_timestamp, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(story_id, event_date, event_type, tool, category)
                DO UPDATE SET
                    event_count = event_count + excluded.event_count,
                    total_duration_ms =
                        total_duration_ms + excluded.total_duration_ms,
                    first_timestamp = min(
                        coalesce(first_timestamp, excluded.first_timestamp),
                        excluded.first_timestamp
                    ),
                    last_timestamp = max(
                        coalesce(last_timestamp, excluded.last_timestamp),
                        excluded.last_timestamp
                    )
                """,
                (*row, timestamp),
            )
        archived = connection.execute(
            """
            UPDATE events
               SET archived_at = ?
             WHERE archived_at IS NULL
               AND importance = 'trivial'
               AND success = 1
               AND event_type NOT IN ('Decision', 'Approval', 'Iteration')
               AND meaningful_progress IS NULL
               AND failure_message IS NULL
               AND resolution IS NULL
               AND error_code IS NULL
               AND timestamp < ?
            """,
            (timestamp, cutoff),
        ).rowcount
        purged = 0
        if purge_archived_days is not None:
            purge_cutoff = (
                datetime.now(timezone.utc) - timedelta(days=purge_archived_days)
            ).isoformat()
            purged = connection.execute(
                """
                DELETE FROM events
                 WHERE archived_at IS NOT NULL
                   AND archived_at < ?
                   AND importance = 'trivial'
                   AND success = 1
                """,
                (purge_cutoff,),
            ).rowcount
        return {"archived": archived, "purged": purged}


def bottleneck_report(
    story_id: str,
    db_path: Path = DEFAULT_DB,
) -> dict[str, Any]:
    with database(db_path) as connection:
        events = connection.execute(
            "SELECT * FROM events WHERE story_id = ? ORDER BY event_id",
            (story_id,),
        ).fetchall()
        summarized_tool_calls = connection.execute(
            """
            SELECT coalesce(sum(event_count), 0)
              FROM event_summaries
             WHERE story_id = ? AND event_type = 'PostToolUse'
            """,
            (story_id,),
        ).fetchone()[0]
    tool_events = [row for row in events if row["event_type"] == "PostToolUse"]
    failures = [row for row in tool_events if not row["success"]]
    error_counts = Counter(row["error_code"] or "UNCLASSIFIED" for row in failures)
    recommendations = []
    if len(failures) >= 3:
        recommendations.append(
            "Review the top repeated failure class before another implementation iteration."
        )
    if _three_stalled(events):
        recommendations.append(
            "Stop the current approach, re-evaluate the logic chain, and ask one focused clarification if needed."
        )
    return {
        "storyId": story_id,
        "toolCalls": len(tool_events) + summarized_tool_calls,
        "failedToolCalls": len(failures),
        "toolFailureRate": (
            len(failures) / (len(tool_events) + summarized_tool_calls)
            if tool_events or summarized_tool_calls
            else 0.0
        ),
        "topErrors": error_counts.most_common(5),
        "recommendations": recommendations,
    }


def list_events(
    story_id: str,
    session_id: str | None = None,
    include_archived: bool = False,
    db_path: Path = DEFAULT_DB,
) -> list[dict[str, Any]]:
    with database(db_path) as connection:
        story = connection.execute(
            "SELECT 1 FROM stories WHERE story_id = ?",
            (story_id,),
        ).fetchone()
        if not story:
            raise ValueError(f"Unknown story: {story_id}")
        rows = connection.execute(
            """
            SELECT e.*,
                   coalesce(
                       e.resolution,
                       (
                           SELECT group_concat(r.summary, '; ')
                             FROM resolutions r
                            WHERE r.failure_event_id = e.event_id
                       )
                   ) AS linked_resolution
              FROM events e
             WHERE e.story_id = ?
               AND (? IS NULL OR e.session_id = ?)
               AND (? = 1 OR e.archived_at IS NULL)
             ORDER BY e.event_id
            """,
            (
                story_id,
                session_id,
                session_id,
                int(include_archived),
            ),
        ).fetchall()
    return [
        {
            "eventId": row["event_id"],
            "timestamp": row["timestamp"],
            "sessionId": row["session_id"],
            "eventType": row["event_type"],
            "tool": row["tool"],
            "category": row["category"],
            "success": bool(row["success"]),
            "durationMs": row["duration_ms"],
            "errorCode": row["error_code"],
            "failureMessage": row["failure_message"],
            "resolution": row["linked_resolution"],
            "importance": row["importance"],
            "meaningfulProgress": (
                None
                if row["meaningful_progress"] is None
                else bool(row["meaningful_progress"])
            ),
            "details": (
                json.loads(row["details_json"]) if row["details_json"] else None
            ),
            "archivedAt": row["archived_at"],
        }
        for row in rows
    ]


def _three_stalled(events: list[sqlite3.Row]) -> bool:
    by_session: dict[str, list[int]] = {}
    for row in events:
        if (
            row["event_type"] == "Iteration"
            and row["session_id"] is not None
            and row["meaningful_progress"] is not None
        ):
            by_session.setdefault(row["session_id"], []).append(
                row["meaningful_progress"]
            )
    return any(
        len(progress) >= 3 and progress[-3:] == [0, 0, 0]
        for progress in by_session.values()
    )
