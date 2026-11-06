"""Isolated workspaces for tests that need a real repository and database.

Two constraints decide the location. ``tempfile.mkdtemp`` requests mode 0o700,
which produces a directory the Windows sandbox cannot traverse, so tests create
their own directory with inherited permissions. The directory also lives beside
the repository in the writable sandbox root (``C:\\dev\\common`` here) rather
than in the user profile, so a run never leaves state inside the repository.
``SDLC_TEST_ROOT`` can point it elsewhere on a machine where the repository
parent is not writable.
"""

from __future__ import annotations

import os
import shutil
import stat
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator
from uuid import uuid4

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKSPACE_ROOT = Path(
    os.environ.get("SDLC_TEST_ROOT") or REPO_ROOT.parent / ".sdlc-test-work"
)


def make_workspace(label: str) -> Path:
    WORKSPACE_ROOT.mkdir(parents=True, exist_ok=True)
    workspace = WORKSPACE_ROOT / f"{label}-{uuid4().hex[:10]}"
    workspace.mkdir()
    return workspace


@contextmanager
def workspace(label: str) -> Iterator[Path]:
    """A temporary project directory, removed even when the test fails."""
    path = make_workspace(label)
    try:
        yield path
    finally:
        remove_workspace(path)


def remove_workspace(workspace: Path) -> None:
    """Remove the fixture, clearing the read-only bits Git leaves on objects."""
    for root, _directories, files in os.walk(workspace):
        for name in files:
            path = Path(root) / name
            try:
                path.chmod(stat.S_IWRITE | stat.S_IREAD)
            except OSError:
                pass
    shutil.rmtree(workspace, ignore_errors=True)
    for _ in range(5):
        try:
            workspace.rmdir()
            return
        except FileNotFoundError:
            return
        except OSError:
            time.sleep(0.05)
