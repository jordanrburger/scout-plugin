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


def test_add_prefix_to_unprefixed_line(tmp_path: Path) -> None:
    target = tmp_path / "f.md"
    target.write_text("- [ ] 🔴 task title\n- [ ] [#X9Y2] other\n")
    from scout.action_items.writer import add_prefix_to_line

    add_prefix_to_line(target, line_number=1, prefix="A3F7")
    assert target.read_text() == "- [ ] [#A3F7] 🔴 task title\n- [ ] [#X9Y2] other\n"


def test_add_prefix_handles_no_priority_emoji(tmp_path: Path) -> None:
    target = tmp_path / "f.md"
    target.write_text("- [ ] just a plain task\n")
    from scout.action_items.writer import add_prefix_to_line

    add_prefix_to_line(target, line_number=1, prefix="A3F7")
    assert target.read_text() == "- [ ] [#A3F7] just a plain task\n"


def test_add_prefix_refuses_if_line_already_prefixed(tmp_path: Path) -> None:
    target = tmp_path / "f.md"
    target.write_text("- [ ] [#X9Y2] already prefixed\n")
    from scout.action_items.writer import add_prefix_to_line
    from scout.errors import ActionItemError

    with pytest.raises(ActionItemError, match="already has prefix"):
        add_prefix_to_line(target, line_number=1, prefix="A3F7")


def test_flip_checkbox_preserves_existing_prefix(tmp_path: Path) -> None:
    target = tmp_path / "f.md"
    target.write_text("- [ ] [#A3F7] task\n")
    from scout.action_items.writer import flip_checkbox

    flip_checkbox(target, line_number=1, to_done=True)
    assert target.read_text() == "- [x] [#A3F7] task\n"


def test_add_prefix_refuses_when_line_number_out_of_range(tmp_path: Path) -> None:
    target = tmp_path / "f.md"
    target.write_text("- [ ] only line\n")
    from scout.action_items.writer import add_prefix_to_line
    from scout.errors import ActionItemError

    with pytest.raises(ActionItemError, match="out of range"):
        add_prefix_to_line(target, line_number=99, prefix="A3F7")


def test_add_prefix_refuses_when_line_is_not_a_checkbox(tmp_path: Path) -> None:
    target = tmp_path / "f.md"
    target.write_text("plain text without checkbox\n")
    from scout.action_items.writer import add_prefix_to_line
    from scout.errors import ActionItemError

    with pytest.raises(ActionItemError, match="doesn't start with a checkbox marker"):
        add_prefix_to_line(target, line_number=1, prefix="A3F7")


def test_add_prefix_to_specific_line_in_multi_line_file(tmp_path: Path) -> None:
    """Pin 1-indexed semantics — line 3 in a multi-line file mutates only line 3."""
    target = tmp_path / "f.md"
    target.write_text("# Header\n\n- [ ] 🔴 first task\n- [ ] 🟡 second task\n- [ ] 🟢 third task\n")
    from scout.action_items.writer import add_prefix_to_line

    add_prefix_to_line(target, line_number=4, prefix="B5K2")

    assert target.read_text() == (
        "# Header\n\n- [ ] 🔴 first task\n- [ ] [#B5K2] 🟡 second task\n- [ ] 🟢 third task\n"
    )
