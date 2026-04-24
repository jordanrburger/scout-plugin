"""Integration tests for scoutctl action-items via subprocess."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def _scoutctl(*args: str, env: dict[str, str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "scout.cli", *args],
        capture_output=True,
        text=True,
        env=env,
        cwd=cwd,
    )


def test_action_items_list_open_only(tmp_path: Path) -> None:
    data_dir = tmp_path / "Scout"
    items_dir = data_dir / "action-items"
    items_dir.mkdir(parents=True)
    fixture = Path(__file__).parent.parent / "fixtures" / "action-items-sample.md"
    target = items_dir / "action-items-2026-04-15.md"
    target.write_text(fixture.read_text())

    env = {**os.environ, "SCOUT_DATA_DIR": str(data_dir)}
    r = _scoutctl("action-items", "list", str(target), "--json", env=env)
    assert r.returncode == 0, r.stderr
    payload = json.loads(r.stdout)
    statuses = {row["status"] for row in payload}
    assert statuses == {"open"}


def test_action_items_mark_done_via_cli(tmp_path: Path) -> None:
    data_dir = tmp_path / "Scout"
    items_dir = data_dir / "action-items"
    items_dir.mkdir(parents=True)
    target = items_dir / "action-items-2026-04-15.md"
    target.write_text("- [ ] sample task\n")

    env = {**os.environ, "SCOUT_DATA_DIR": str(data_dir)}
    r = _scoutctl(
        "action-items",
        "mark-done",
        "--subject",
        "sample",
        str(target),
        env=env,
    )
    assert r.returncode == 0, r.stderr
    assert "- [x] sample task" in target.read_text()


def test_action_items_watch_returns_scout_error_exit_code() -> None:
    """Plan 2 stubs `watch` with a Plan 3 placeholder."""
    r = _scoutctl("action-items", "watch", env={**os.environ})
    # ScoutError.exit_code == 1
    assert r.returncode == 1
    assert "Plan 3" in r.stderr
