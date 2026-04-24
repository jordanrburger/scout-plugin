"""Unit tests for scout.action_items.list."""

from __future__ import annotations

from pathlib import Path

from scout.action_items.list import list_items

FIXTURE = Path(__file__).parent.parent / "fixtures" / "action-items-sample.md"


def test_list_open_only_default() -> None:
    items = list_items(FIXTURE)
    statuses = {i.status for i in items}
    assert statuses == {"open"}


def test_list_all_includes_done() -> None:
    items = list_items(FIXTURE, include_done=True)
    statuses = {i.status for i in items}
    assert "done" in statuses
    assert "open" in statuses


def test_list_filter_priority_high() -> None:
    items = list_items(FIXTURE, priority="high")
    assert all(i.priority == "🔴" for i in items)


def test_list_filter_section() -> None:
    items = list_items(FIXTURE, section="Watching")
    assert all(i.section == "Watching" for i in items)
