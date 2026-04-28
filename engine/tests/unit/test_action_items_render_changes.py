"""Unit tests for scout.action_items.render.render_changes."""

from __future__ import annotations

import datetime as dt

from scout.action_items.diff import ChangeEvent
from scout.action_items.render import render_changes

_NOW = dt.datetime(2026, 4, 26, 14, 32, 15)


def test_added_line_format() -> None:
    e = ChangeEvent(kind="added", item_id="A3F7", title="task A", section="To Do")
    lines = render_changes([e], now=_NOW, color=False)
    assert len(lines) == 1
    assert lines[0] == "[14:32:15] + added     [#A3F7] task A (To Do)"


def test_removed_line_format() -> None:
    e = ChangeEvent(kind="removed", item_id="A3F7", title="task A", section="To Do")
    lines = render_changes([e], now=_NOW, color=False)
    assert lines[0] == "[14:32:15] - removed   [#A3F7] task A (To Do)"


def test_completed_line_format() -> None:
    e = ChangeEvent(kind="completed", item_id="A3F7", title="task A", section="In Progress")
    lines = render_changes([e], now=_NOW, color=False)
    assert lines[0] == "[14:32:15] ✓ completed [#A3F7] task A (In Progress)"


def test_reopened_line_format() -> None:
    e = ChangeEvent(kind="reopened", item_id="A3F7", title="task A", section="In Progress")
    lines = render_changes([e], now=_NOW, color=False)
    assert lines[0] == "[14:32:15] ↻ reopened  [#A3F7] task A (In Progress)"


def test_title_changed_line_format() -> None:
    e = ChangeEvent(
        kind="title_changed",
        item_id="A3F7",
        title="new title",
        section="In Progress",
        extras={"old_title": "old title", "new_title": "new title"},
    )
    lines = render_changes([e], now=_NOW, color=False)
    assert lines[0] == '[14:32:15] ✎ renamed   [#A3F7] "old title" → "new title"'


def test_unprefixed_item_id_omits_brackets() -> None:
    e = ChangeEvent(kind="added", item_id="", title="legacy task", section="To Do")
    lines = render_changes([e], now=_NOW, color=False)
    assert lines[0] == "[14:32:15] + added     legacy task (To Do)"


def test_color_output_includes_ansi_codes() -> None:
    e = ChangeEvent(kind="completed", item_id="A3F7", title="task", section="In Progress")
    lines = render_changes([e], now=_NOW, color=True)
    # Rich emits ANSI escapes for colored text. We don't pin the exact codes
    # but assert the line contains an ANSI escape introducer.
    assert "\x1b[" in lines[0]


def test_multiple_events_render_in_order() -> None:
    events = [
        ChangeEvent(kind="completed", item_id="A3F7", title="A", section="In Progress"),
        ChangeEvent(kind="added", item_id="B5K2", title="B", section="To Do"),
    ]
    lines = render_changes(events, now=_NOW, color=False)
    assert len(lines) == 2
    assert "completed" in lines[0]
    assert "added" in lines[1]


def test_empty_events_yields_empty_list() -> None:
    assert render_changes([], now=_NOW, color=False) == []
