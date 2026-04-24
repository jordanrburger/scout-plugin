"""Unit tests for scout.action_items.writer."""

from __future__ import annotations

from pathlib import Path

import pytest

from scout.action_items.writer import (
    atomic_write_lines,
    flip_checkbox,
    insert_below,
)


def test_atomic_write_replaces_file_contents(tmp_path: Path) -> None:
    target = tmp_path / "f.md"
    target.write_text("old\n")
    atomic_write_lines(target, ["new line 1", "new line 2"])
    assert target.read_text() == "new line 1\nnew line 2\n"


def test_atomic_write_uses_temp_then_rename(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Failure between tmp write and replace must leave original intact."""
    target = tmp_path / "f.md"
    target.write_text("original\n")
    real_replace = __import__("os").replace

    def boom(_src: str, _dst: str) -> None:
        raise OSError("simulated rename failure")

    import os

    monkeypatch.setattr(os, "replace", boom)
    with pytest.raises(OSError):
        atomic_write_lines(target, ["new"])
    assert target.read_text() == "original\n"  # untouched
    monkeypatch.setattr(os, "replace", real_replace)


def test_flip_checkbox_open_to_done(tmp_path: Path) -> None:
    target = tmp_path / "f.md"
    target.write_text("- [ ] task A\n- [ ] task B\n")
    flip_checkbox(target, line_number=1, to_done=True)
    assert target.read_text() == "- [x] task A\n- [ ] task B\n"


def test_flip_checkbox_done_to_open(tmp_path: Path) -> None:
    target = tmp_path / "f.md"
    target.write_text("- [x] task A\n")
    flip_checkbox(target, line_number=1, to_done=False)
    assert target.read_text() == "- [ ] task A\n"


def test_insert_below_appends_after_target_line(tmp_path: Path) -> None:
    target = tmp_path / "f.md"
    target.write_text("line 1\nline 2\nline 3\n")
    insert_below(target, line_number=2, text="  - inserted note")
    assert target.read_text() == "line 1\nline 2\n  - inserted note\nline 3\n"


def test_flip_checkbox_out_of_range_raises(tmp_path: Path) -> None:
    target = tmp_path / "f.md"
    target.write_text("- [ ] task\n")
    from scout.errors import ActionItemError

    with pytest.raises(ActionItemError, match="line"):
        flip_checkbox(target, line_number=99, to_done=True)
