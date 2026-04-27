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


def test_action_items_mark_done_by_id_via_cli(tmp_path: Path) -> None:
    """Smoke test: scoutctl action-items mark-done --by-id A3F7 flips the matching line."""
    data_dir = tmp_path / "Scout"
    items_dir = data_dir / "action-items"
    items_dir.mkdir(parents=True)
    state_dir = data_dir / ".scout-state"
    state_dir.mkdir(parents=True)
    target = items_dir / "action-items-2026-04-15.md"
    target.write_text(
        "## In Progress\n\n- [ ] [#A3F7] 🔴 Test mark-done by id\n",
    )
    # Register the prefix↔ULID mapping so --by-id can look it up.
    id_map_path = state_dir / "id-map.json"
    id_map_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "entries": {
                    "01HXAAA0000000000000000000": {
                        "ulid": "01HXAAA0000000000000000000",
                        "short_prefix": "A3F7",
                        "last_title": "Test mark-done by id",
                        "last_file": "action-items-2026-04-15.md",
                        "last_line": 3,
                    }
                },
            }
        )
        + "\n"
    )

    env = {**os.environ, "SCOUT_DATA_DIR": str(data_dir)}
    r = _scoutctl(
        "action-items",
        "mark-done",
        "--by-id",
        "A3F7",
        str(target),
        env=env,
    )
    assert r.returncode == 0, r.stderr
    assert "- [x] [#A3F7] 🔴 Test mark-done by id" in target.read_text()


def test_action_items_list_surfaces_short_prefix(tmp_path: Path) -> None:
    """`scoutctl action-items list` surfaces `[#XXXX]` in the plain output."""
    data_dir = tmp_path / "Scout"
    items_dir = data_dir / "action-items"
    items_dir.mkdir(parents=True)
    fixture = Path(__file__).parent.parent / "fixtures" / "action-items-with-prefixes.md"
    target = items_dir / "action-items-2026-04-15.md"
    target.write_text(fixture.read_text())

    env = {**os.environ, "SCOUT_DATA_DIR": str(data_dir)}
    r = _scoutctl("action-items", "list", str(target), env=env)
    assert r.returncode == 0, r.stderr
    assert "[#A3F7]" in r.stdout
    assert "[#C9N4]" in r.stdout
    # An unprefixed open item: the line containing "announcement" must not
    # contain "[#" — otherwise the formatter is leaking an empty bracket.
    sent_line = [ln for ln in r.stdout.splitlines() if "announcement" in ln]
    assert sent_line and "[#" not in sent_line[0]
