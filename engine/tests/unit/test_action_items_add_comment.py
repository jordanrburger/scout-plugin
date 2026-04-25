"""Unit tests for scout.action_items.add_comment."""

from __future__ import annotations

from pathlib import Path

import pytest

from scout.action_items.add_comment import add_comment
from scout.errors import ActionItemError


def _seed(tmp_path: Path, body: str) -> Path:
    f = tmp_path / "action-items-2026-04-15.md"
    f.write_text(body)
    return f


def test_adds_comment_below_matched_task(tmp_path: Path) -> None:
    f = _seed(tmp_path, "- [ ] Task A\n- [ ] Task B\n")
    add_comment(f, subject="Task A", text="checked with vendor", timestamp=False)
    body = f.read_text()
    assert "checked with vendor" in body
    # The comment appears between Task A and Task B.
    assert body.index("Task A") < body.index("checked with vendor") < body.index("Task B")


def test_adds_comment_with_timestamp(tmp_path: Path) -> None:
    f = _seed(tmp_path, "- [ ] Task A\n")
    add_comment(f, subject="Task A", text="vendor confirmed", timestamp=True, author="jordan")
    body = f.read_text()
    # Comment should contain the author name, text, and a date-like pattern.
    assert "jordan" in body
    assert "vendor confirmed" in body
    # Should be formatted as blockquote: > author (YYYY-MM-DD HH:MM AM/PM ET): text
    assert "> jordan" in body


def test_comment_appended_after_existing_comments(tmp_path: Path) -> None:
    f = _seed(tmp_path, "- [ ] Task A\n  > scott (2026-04-15 10:00 AM ET): first comment\n- [ ] Task B\n")
    add_comment(f, subject="Task A", text="second comment", timestamp=False)
    body = f.read_text()
    # Both comments should be present.
    assert "first comment" in body
    assert "second comment" in body
    # second_comment comes after first_comment
    assert body.index("first comment") < body.index("second comment")
    # Both come before Task B
    assert body.index("second comment") < body.index("Task B")


def test_no_match_raises(tmp_path: Path) -> None:
    f = _seed(tmp_path, "- [ ] Task\n")
    with pytest.raises(ActionItemError, match="no match"):
        add_comment(f, subject="other", text="x")


def test_ambiguous_match_raises(tmp_path: Path) -> None:
    f = _seed(tmp_path, "- [ ] vendor A\n- [ ] vendor B\n")
    with pytest.raises(ActionItemError, match="ambiguous|multiple"):
        add_comment(f, subject="vendor", text="x")


def test_case_insensitive_matching(tmp_path: Path) -> None:
    f = _seed(tmp_path, "- [ ] Submit LEVER Feedback\n")
    add_comment(f, subject="lever", text="done", timestamp=False)
    body = f.read_text()
    assert "done" in body


def test_resolves_today_when_path_omitted(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import datetime as dt

    from scout import paths

    monkeypatch.setenv("SCOUT_DATA_DIR", str(tmp_path))
    (tmp_path / "action-items").mkdir()
    monkeypatch.setattr(paths, "_today", lambda: dt.date(2026, 4, 15))
    f = _seed(tmp_path / "action-items", "- [ ] task X\n")
    # No `path` argument → resolves via paths.action_items_daily_path()
    add_comment(None, subject="task X", text="done", timestamp=False)
    assert "done" in f.read_text()
