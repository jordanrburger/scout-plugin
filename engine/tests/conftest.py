"""Shared pytest fixtures."""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

import pytest


@pytest.fixture
def fake_data_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """A writable tmp data dir wired up via SCOUT_DATA_DIR."""
    d = tmp_path / "Scout"
    d.mkdir()
    (d / ".scout-logs").mkdir()
    (d / ".scout-cache").mkdir()
    (d / ".scout-state").mkdir()
    (d / "knowledge-base").mkdir()
    (d / "action-items").mkdir()
    monkeypatch.setenv("SCOUT_DATA_DIR", str(d))
    yield d


@pytest.fixture
def clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Unset any SCOUT_* env vars that might leak between tests."""
    for key in list(os.environ):
        if key.startswith("SCOUT_"):
            monkeypatch.delenv(key, raising=False)
