"""Unit tests for scout.action_items.list."""

from __future__ import annotations

from pathlib import Path

from scout.action_items.list import format_items, list_items

FIXTURE = Path(__file__).parent.parent / "fixtures" / "action-items-sample.md"
PREFIX_FIXTURE = Path(__file__).parent.parent / "fixtures" / "action-items-with-prefixes.md"


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


def test_list_includes_short_prefix_when_present() -> None:
    """The list output prefixes each item with `[#XXXX]` when one exists."""
    items = list_items(PREFIX_FIXTURE, include_done=True)
    output = format_items(items)
    assert "[#A3F7]" in output
    assert "[#B5K2]" in output


def test_list_omits_prefix_for_unprefixed_lines() -> None:
    """Unprefixed items render without any `[#` substring on their line."""
    items = list_items(PREFIX_FIXTURE, include_done=True)
    output = format_items(items)
    # "Send Scout plugin announcement" is unprefixed in the fixture.
    sent_line = [ln for ln in output.splitlines() if "announcement" in ln]
    assert sent_line and "[#" not in sent_line[0]
