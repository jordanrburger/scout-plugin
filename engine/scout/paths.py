"""Path resolution for Scout engine and data dirs.

All paths are expanded (~) and resolved (symlinks, relative segments).
"""

from __future__ import annotations

import os
from pathlib import Path

from scout.errors import DataDirError

DEFAULT_DATA_DIR_NAME = "Scout"


def resolve_path(p: str | Path) -> Path:
    """Expand ~ and resolve symlinks/relative segments to an absolute Path."""
    return Path(p).expanduser().resolve()


def data_dir(explicit: str | Path | None = None) -> Path:
    """Resolve the Scout data directory.

    Precedence:
      1. Explicit argument
      2. $SCOUT_DATA_DIR env var
      3. ~/Scout

    Does NOT validate that the dir exists — callers use require_data_dir().
    """
    if explicit is not None:
        return resolve_path(explicit)

    env = os.environ.get("SCOUT_DATA_DIR")
    if env:
        return resolve_path(env)

    return resolve_path(Path.home() / DEFAULT_DATA_DIR_NAME)


def logs_dir(data: Path | None = None) -> Path:
    return (data or data_dir()) / ".scout-logs"


def cache_dir(data: Path | None = None) -> Path:
    return (data or data_dir()) / ".scout-cache"


def state_dir(data: Path | None = None) -> Path:
    return (data or data_dir()) / ".scout-state"


def config_path(data: Path | None = None) -> Path:
    return (data or data_dir()) / ".scout-config.yaml"


def kb_dir(data: Path | None = None) -> Path:
    return (data or data_dir()) / "knowledge-base"


def action_items_dir(data: Path | None = None) -> Path:
    return (data or data_dir()) / "action-items"


def require_data_dir(data: Path | None = None) -> Path:
    """Return the data dir, raising DataDirError if it does not exist."""
    d = data or data_dir()
    if not d.exists():
        raise DataDirError(f"Scout data dir does not exist: {d}\nRun: scoutctl setup data-dir")
    if not d.is_dir():
        raise DataDirError(f"Scout data dir is not a directory: {d}")
    return d
