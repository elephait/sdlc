from __future__ import annotations

import argparse
import json
import ntpath
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


COMMIT_PREFIXES = ("ai commit: ", "ai code review: ")
CREDENTIAL_APPROVALS = Path(".sdlc") / "credential-commit-approvals.jsonl"
CREDENTIAL_NAMES = {
    ".env",
    ".npmrc",
    ".pypirc",
    "credentials",
    "credentials.json",
    "id_dsa",
    "id_ed25519",
    "id_rsa",
    "secrets.json",
}
CREDENTIAL_SUFFIXES = {
    ".jks",
    ".key",
    ".kdbx",
    ".p12",
    ".pem",
    ".pfx",
}
RED = "\033[91m"
RESET = "\033[0m"
DANGER = "🔴 DANGER"


def strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from strings(item)


def under_dev(value):
    normalized = ntpath.normpath(value).lower()
    return normalized == "c:\\dev" or normalized.startswith("c:\\dev\\")


def run_git(cwd: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(cwd), *args],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise ValueError(completed.stderr.strip() or "Git command failed.")
    return completed.stdout


def git_root(cwd: Path) -> Path:
    return Path(run_git(cwd, "rev-parse", "--show-toplevel").strip()).resolve()


def is_credential_file(path: str) -> bool:
    normalized = path.replace("\\", "/")
    name = normalized.rsplit("/", 1)[-1].lower()
    if normalized.lower() == CREDENTIAL_APPROVALS.as_posix().lower():
        return False
    return (
        name in CREDENTIAL_NAMES
        or name.startswith(".env.")
        or Path(name).suffix.lower() in CREDENTIAL_SUFFIXES
        or re.search(
            r"(^|[._-])(credentials?|secrets?)([._-]|$)",
            name,
        )
        is not None
    )


def staged_credentials(cwd: Path) -> dict[str, str]:
    root = git_root(cwd)
    names = run_git(
        root,
        "diff",
        "--cached",
        "--name-only",
        "--diff-filter=ACMR",
        "-z",
    ).split("\0")
    credentials = {}
    for name in names:
        if name and is_credential_file(name):
            credentials[name] = run_git(root, "rev-parse", f":{name}").strip()
    return credentials


def approval_path(cwd: Path) -> Path:
    return git_root(cwd) / CREDENTIAL_APPROVALS


def has_credential_approval(cwd: Path, files: dict[str, str]) -> bool:
    path = approval_path(cwd)
    if not path.is_file():
        return False
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        if record.get("files") == files and record.get("approvedBy"):
            return True
    return False


def record_credential_approval(
    cwd: Path,
    approved_by: str,
    reason: str | None,
) -> dict[str, object]:
    files = staged_credentials(cwd)
    if not files:
        raise ValueError("No staged credential-like files require approval.")
    record = {
        "approvedBy": approved_by,
        "approvedAt": datetime.now(timezone.utc).astimezone().isoformat(),
        "reason": reason,
        "files": files,
    }
    path = approval_path(cwd)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(record, separators=(",", ":")) + "\n")
    return record


def commit_title(command: str, cwd: Path) -> str | None:
    message = re.search(
        r"""(?ix)
        (?:^|\s)(?:-m|--message)
        (?:=|\s+)
        (?:
            "([^"]*)"
            |
            '([^']*)'
            |
            ([^\s]+)
        )
        """,
        command,
    )
    if message:
        return next(value for value in message.groups() if value is not None)
    if re.search(r"(?i)\bgit\s+commit\b.*\b--amend\b.*\b--no-edit\b", command):
        return run_git(cwd, "log", "-1", "--format=%s").strip()
    return None


def git_command_cwd(command: str, fallback: Path) -> Path:
    match = re.search(
        r"""(?ix)
        \bgit\b[^\r\n;|]*?\s-C\s+
        (?:
            "([^"]+)"
            |
            '([^']+)'
            |
            ([^\s;|]+)
        )
        """,
        command,
    )
    if not match:
        return fallback
    value = next(item for item in match.groups() if item is not None)
    candidate = Path(value)
    return candidate if candidate.is_absolute() else fallback / candidate


def hook_decision(payload: dict[str, object]) -> dict[str, str]:
    text = "\n".join(strings(payload))
    tool = str(payload.get("toolName") or payload.get("tool_name") or "")
    tool_input = payload.get("toolArgs", payload.get("tool_input"))
    tool_text = "\n".join(strings(tool_input))
    cwd = str(payload.get("cwd", ""))
    decision = "allow"
    reason = r"Allowed by the C:\dev universal policy."

    if re.search(r"(?i)\bgit\b[^\r\n;|]*\bpush\b", text):
        decision = "ask"
        reason = (
            "Git push or equivalent remote publication requires explicit approval."
        )

    commit = re.search(r"(?i)\bgit\b[^\r\n;|]*\bcommit\b", tool_text)
    if commit:
        repository = git_command_cwd(tool_text, Path(cwd or Path.cwd()))
        title = commit_title(tool_text, repository)
        if title is None or not title.startswith(COMMIT_PREFIXES):
            decision = "deny"
            reason = (
                "AI-performed commit titles must start with one of "
                f"{COMMIT_PREFIXES!r}."
            )
        else:
            credentials = staged_credentials(repository)
            if credentials and not has_credential_approval(repository, credentials):
                decision = "deny"
                listed = ", ".join(sorted(credentials))
                reason = (
                    f"{DANGER}: credential-like files are staged: {listed}. "
                    "Default action: remove them from the commit. Otherwise ask "
                    "the user for explicit approval, then record the approver, "
                    "optional reason, timestamp, and staged content hashes with "
                    "scope_hook.py approve before retrying."
                )

    mutating_tool = re.search(r"(?i)(apply_patch|edit|create|delete|write)", tool)
    shell_mutation = re.search(
        r"(?i)\b(Set-Content|Add-Content|Remove-Item|Copy-Item|Move-Item|New-Item|Out-File)\b|>",
        tool_text,
    )
    if mutating_tool or shell_mutation:
        candidates = re.findall(
            r"""(?ix)
            ["']([A-Z]:[\\/][^"']+)["']
            |
            \b([A-Z]:[\\/][^\s,;|]+)
            """,
            tool_text,
        )
        absolute_paths = [left or right for left, right in candidates]
        if cwd and not under_dev(ntpath.abspath(cwd)):
            decision = "deny"
            reason = r"A mutating operation has a working directory outside C:\dev."
        for candidate in absolute_paths:
            if not under_dev(candidate):
                decision = "deny"
                reason = r"A mutating operation referenced a path outside C:\dev."
                break

    return {
        "permissionDecision": decision,
        "permissionDecisionReason": reason,
    }


def approval_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    approve = commands.add_parser("approve")
    approve.add_argument("--workspace", type=Path, default=Path.cwd())
    approve.add_argument("--approved-by", required=True)
    approve.add_argument("--reason")
    return parser


def main() -> int:
    if len(sys.argv) > 1:
        args = approval_parser().parse_args()
        record = record_credential_approval(
            args.workspace,
            args.approved_by,
            args.reason,
        )
        print(
            f"{RED}{DANGER}: committing credential files can expose secrets."
            f"{RESET}",
            file=sys.stderr,
        )
        print(json.dumps(record, indent=2))
        return 0
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    **hook_decision(json.load(sys.stdin)),
                }
            }
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"SCOPE ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
