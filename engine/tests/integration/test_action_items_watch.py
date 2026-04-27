"""Integration test for scoutctl action-items watch.

Spawns the CLI as a subprocess, mutates the watched file, asserts a
diff line is printed within a small timeout. Marked `slow` so default
unit-test runs skip it; CI runs it explicitly.
"""

from __future__ import annotations

import os
import select
import subprocess
import time
from pathlib import Path

import pytest

pytestmark = pytest.mark.slow


def _scoutctl_path() -> str:
    """Resolve the scoutctl entry point inside the engine venv."""
    venv_bin = Path(__file__).parent.parent.parent / ".venv" / "bin"
    candidate = venv_bin / "scoutctl"
    if candidate.exists():
        return str(candidate)
    return "scoutctl"  # fall back to PATH lookup


def _read_until(proc: subprocess.Popen[str], substring: str, timeout: float) -> str:
    """Read stdout until `substring` appears or `timeout` elapses.

    Returns accumulated stdout. Uses `select` so a wedged subprocess
    doesn't hang the test.
    """
    deadline = time.monotonic() + timeout
    buf: list[str] = []
    assert proc.stdout is not None
    while time.monotonic() < deadline:
        ready, _, _ = select.select([proc.stdout], [], [], 0.2)
        if proc.stdout in ready:
            line = proc.stdout.readline()
            if not line:
                break
            buf.append(line)
            if substring in line:
                return "".join(buf)
    return "".join(buf)


def test_watch_emits_completed_line_on_checkbox_flip(tmp_path: Path) -> None:
    daily = tmp_path / "action-items-2026-04-26.md"
    daily.write_text(
        "## In Progress\n\n- [ ] [#A3F7] Submit Lever feedback\n",
    )

    env = {**os.environ, "NO_COLOR": "1"}  # ensure plain output even on TTY-emulating CI
    proc = subprocess.Popen(
        [_scoutctl_path(), "action-items", "watch", str(daily), "--no-color"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )

    try:
        # Give the watcher ~500ms to register its filesystem hook.
        time.sleep(0.5)

        # Mutate the file: flip the checkbox.
        daily.write_text(
            "## In Progress\n\n- [x] [#A3F7] Submit Lever feedback\n",
        )

        out = _read_until(proc, "completed", timeout=10.0)
        assert "completed" in out
        assert "[#A3F7]" in out
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
