from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from collections.abc import Iterator
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = PROJECT_ROOT / "data" / "copilot_sdlc.db"
SCHEMA_PATH = PROJECT_ROOT / "sql" / "schema.sql"
DEV_ROOT = Path(r"C:\dev")


def require_under_dev(path: Path, label: str) -> Path:
    resolved = path.resolve()
    try:
        resolved.relative_to(DEV_ROOT)
    except ValueError as error:
        raise ValueError(f"{label} must be under C:\\dev: {resolved}") from error
    return resolved


def connect(path: Path = DEFAULT_DB) -> sqlite3.Connection:
    resolved = require_under_dev(path, "Database")
    resolved.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(resolved, timeout=30)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 30000")
    return connection


@contextmanager
def database(path: Path = DEFAULT_DB) -> Iterator[sqlite3.Connection]:
    connection = connect(path)
    try:
        with connection:
            yield connection
    finally:
        connection.close()


def initialize(path: Path = DEFAULT_DB) -> None:
    with database(path) as connection:
        connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        _ensure_column(
            connection,
            "event_summaries",
            "first_timestamp",
            "TEXT",
        )
        _ensure_column(
            connection,
            "event_summaries",
            "last_timestamp",
            "TEXT",
        )
        # Host attribution arrived after the first databases existed; keep the
        # migration additive so an active story's evidence is never rewritten.
        _ensure_column(connection, "sessions", "host", "TEXT")


def _ensure_column(
    connection: sqlite3.Connection,
    table: str,
    column: str,
    definition: str,
) -> None:
    columns = {
        row["name"] for row in connection.execute(f"PRAGMA table_info({table})")
    }
    if column not in columns:
        connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
