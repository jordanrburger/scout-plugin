"""Unit tests for scout.action_items.mark_done."""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import pytest

from scout.action_items.mark_done import mark_done
from scout.errors import ActionItemError


def _seed(tmp_path: Path, body: str) -> Path:
    f = tmp_path / "action-items-2026-04-15.md"
    f.write_text(body)
    return f


def test_marks_open_task_done_by_subject(tmp_path: Path) -> None:
    f = _seed(tmp_path, "- [ ] Submit Lever feedback\n- [ ] Other task\n")
    mark_done(f, subject="Lever feedback")
    assert "- [x] Submit Lever feedback" in f.read_text()
    assert "- [ ] Other task" in f.read_text()  # unchanged


def test_no_match_raises(tmp_path: Path) -> None:
    f = _seed(tmp_path, "- [ ] Existing task\n")
    with pytest.raises(ActionItemError, match="no match"):
        mark_done(f, subject="missing keyword")


def test_ambiguous_match_raises_listing_candidates(tmp_path: Path) -> None:
    f = _seed(tmp_path, "- [ ] Lever feedback A\n- [ ] Lever feedback B\n")
    with pytest.raises(ActionItemError, match="ambiguous|multiple") as exc:
        mark_done(f, subject="lever feedback")
    msg = str(exc.value)
    assert "Lever feedback A" in msg
    assert "Lever feedback B" in msg


def test_undo_flips_done_back_to_open(tmp_path: Path) -> None:
    f = _seed(tmp_path, "- [x] Done thing\n")
    mark_done(f, subject="Done thing", undo=True)
    assert "- [ ] Done thing" in f.read_text()


def test_resolves_today_when_path_omitted(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from scout import paths

    monkeypatch.setenv("SCOUT_DATA_DIR", str(tmp_path))
    (tmp_path / "action-items").mkdir()
    monkeypatch.setattr(paths, "_today", lambda: dt.date(2026, 4, 15))
    f = _seed(tmp_path / "action-items", "- [ ] task X\n")
    # No `path` argument → resolves via paths.action_items_daily_path()
    mark_done(None, subject="task X")
    assert "- [x] task X" in f.read_text()
