from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEV_ROOT = Path(r"C:\dev")

try:  # Windows
    import msvcrt

    def _lock(handle) -> None:
        msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)

    def _unlock(handle) -> None:
        msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)

except ImportError:  # POSIX
    import fcntl

    def _lock(handle) -> None:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

    def _unlock(handle) -> None:
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


CLEAN_STOP_REASONS = {
    "complete",
    "user_exit",
    "clear",
    "logout",
    "prompt_input_exit",
    "other",
}


def main() -> int:
    payload = json.load(sys.stdin)
    active_path = find_active_story(Path(payload.get("cwd") or Path.cwd()))
    if active_path is None:
        print("{}")
        return 0

    active = json.loads(active_path.read_text(encoding="utf-8-sig"))
    configured_ledger = Path(active["ledgerPath"])
    ledger = require_under_dev(
        (
            configured_ledger
            if configured_ledger.is_absolute()
            else active_path.parent.parent / configured_ledger
        ),
        "Ledger",
    )
    event_path = ledger / "events.jsonl"
    event = build_event(payload, active)
    append_jsonl(event_path, event)

    if event["event"] == "SessionStart":
        context = (
            f"SDLC tracking is active for {event['storyId']}. "
            f"Events are written to {event_path}."
        )
        # Claude Code and VS Code read hookSpecificOutput; the top-level key
        # is kept for hosts that read the older shape.
        print(
            json.dumps(
                {
                    "hookSpecificOutput": {
                        "hookEventName": "SessionStart",
                        "additionalContext": context,
                    },
                    "additionalContext": context,
                }
            )
        )
    else:
        print("{}")
    return 0


def find_active_story(cwd: Path) -> Path | None:
    resolved = cwd.resolve()
    for directory in (resolved, *resolved.parents):
        candidate = directory / ".sdlc" / "active-story.json"
        if candidate.is_file():
            return candidate
    return None


def require_under_dev(path: Path, label: str) -> Path:
    resolved = path.resolve()
    try:
        resolved.relative_to(DEV_ROOT)
    except ValueError as error:
        raise ValueError(f"{label} must be under C:\\dev: {resolved}") from error
    return resolved


def build_event(
    payload: dict[str, Any],
    active: dict[str, Any],
) -> dict[str, Any]:
    hook_event = str(
        payload.get("hook_event_name") or payload.get("hookEventName") or ""
    )
    session_id = payload.get("session_id") or payload.get("sessionId")
    timestamp = payload.get("timestamp") or now()
    tool = payload.get("tool_name") or payload.get("toolName")
    details: dict[str, Any] = {"hookEvent": hook_event}
    for source, target in (
        ("source", "source"),
        ("reason", "reason"),
        ("agent_id", "agentId"),
        ("agent_type", "agentType"),
        ("parent_agent_id", "parentAgentId"),
    ):
        if payload.get(source) is not None:
            details[target] = payload[source]

    success = True
    error_code = None
    failure_message = None
    event_type = hook_event or "HookEvent"
    if hook_event in {"Stop", "SessionEnd"}:
        # Hosts that report no reason (Claude Code's Stop) are not failures.
        reason = str(payload.get("reason") or "")
        success = not reason or reason in CLEAN_STOP_REASONS
        if not success:
            error_code = "SESSION_STOP_FAILURE"
            failure_message = f"Session stopped with reason: {reason}"
    elif hook_event == "PostToolUseFailure":
        success = False
        error_code = "TOOL_FAILURE"
        failure_message = str(payload.get("error") or "Tool call failed")

    return {
        "timestamp": timestamp,
        "storyId": active["storyId"],
        "project": active.get("project"),
        "sessionId": session_id,
        "event": event_type,
        "tool": tool,
        "category": "agent-tool" if tool else "session-lifecycle",
        "success": success,
        "durationMs": None,
        "errorCode": error_code,
        "failureMessage": failure_message,
        "details": details,
    }


def append_jsonl(path: Path, event: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = path.with_suffix(f"{path.suffix}.lock")
    with lock_path.open("a+b") as lock:
        lock.seek(0, 2)
        if lock.tell() == 0:
            lock.write(b"\0")
            lock.flush()
        lock.seek(0)
        deadline = time.monotonic() + 4
        while True:
            try:
                _lock(lock)
                break
            except OSError:
                if time.monotonic() >= deadline:
                    raise TimeoutError(f"Timed out locking tracking ledger: {path}")
                time.sleep(0.05)
        try:
            with path.open("a", encoding="utf-8", newline="\n") as stream:
                stream.write(json.dumps(event, separators=(",", ":")) + "\n")
                stream.flush()
        finally:
            lock.seek(0)
            _unlock(lock)


def now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (KeyError, ValueError, OSError, json.JSONDecodeError) as error:
        print(f"TRACKING ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
