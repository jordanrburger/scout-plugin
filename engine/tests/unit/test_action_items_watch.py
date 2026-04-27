"""Unit tests for the pure core of scout.action_items.watch.

The watchdog wiring is tested in tests/integration/test_action_items_watch.py.
"""

from __future__ import annotations

import datetime as dt

from scout.action_items.watch import process_change

_NOW = dt.datetime(2026, 4, 26, 14, 32, 15)


def test_process_change_emits_no_lines_when_text_identical() -> None:
    text = "## In Progress\n\n- [ ] [#A3F7] task A\n"
    lines = process_change(prev_text=text, curr_text=text, now=_NOW, color=False)
    assert lines == []


def test_process_change_emits_completed_line_when_checkbox_flipped() -> None:
    prev = "## In Progress\n\n- [ ] [#A3F7] task A\n"
    curr = "## In Progress\n\n- [x] [#A3F7] task A\n"
    lines = process_change(prev_text=prev, curr_text=curr, now=_NOW, color=False)
    assert len(lines) == 1
    assert "completed" in lines[0]
    assert "[#A3F7]" in lines[0]


def test_process_change_emits_added_line_when_new_item_appears() -> None:
    prev = "## In Progress\n\n- [ ] [#A3F7] task A\n"
    curr = "## In Progress\n\n- [ ] [#A3F7] task A\n- [ ] [#B5K2] task B\n"
    lines = process_change(prev_text=prev, curr_text=curr, now=_NOW, color=False)
    assert len(lines) == 1
    assert "added" in lines[0]
    assert "[#B5K2]" in lines[0]


def test_process_change_handles_unparseable_prev_gracefully() -> None:
    """Initial seed (empty file) shouldn't crash the watcher."""
    lines = process_change(prev_text="", curr_text="- [ ] [#A3F7] task\n", now=_NOW, color=False)
    # Single added event for the new task.
    assert len(lines) == 1
    assert "added" in lines[0]
