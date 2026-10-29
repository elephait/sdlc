"""Isolated workspaces for tests that need a real repository and database."""

from __future__ import annotations

import os
import shutil
import stat
import tempfile
import time
from pathlib import Path
from uuid import uuid4

WORKSPACE_ROOT = Path(
    os.environ.get("SDLC_TEST_ROOT", tempfile.gettempdir())
) / "sdlc-test-work"


def make_workspace(label: str) -> Path:
    WORKSPACE_ROOT.mkdir(parents=True, exist_ok=True)
    workspace = WORKSPACE_ROOT / f"{label}-{uuid4().hex[:10]}"
    workspace.mkdir(parents=True)
    return workspace


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
