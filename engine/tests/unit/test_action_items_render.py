"""Unit tests for scout.action_items.render.

Smoke-level: render a fixture file and verify the output references the
tasks the parser extracted. Pixel-perfect Rich output is intentionally
not asserted — that would be brittle.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from scout.action_items.render import render

FIXTURE = Path(__file__).parent.parent / "fixtures" / "action-items-sample.md"


def test_render_runs_on_fixture_without_error() -> None:
    out = render(FIXTURE)
    assert isinstance(out, str)
    assert len(out) > 0


def test_render_includes_open_task_titles() -> None:
    out = render(FIXTURE)
    assert "Submit Lever feedback" in out
    assert "Reply to Q2 budget thread" in out


def test_render_missing_file_raises(tmp_path: Path) -> None:
    from scout.errors import ActionItemError

    missing = tmp_path / "no-such-file.md"
    with pytest.raises(ActionItemError, match="not found"):
        render(missing)
