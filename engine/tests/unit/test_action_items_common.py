"""Unit tests for scout.action_items._common — shared mutator helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

from scout.action_items._common import find_line_number, resolve_target
from scout.action_items.parser import ActionItem
from scout.errors import ActionItemError
from scout.id_map import IdMap, IdMapEntry


def test_find_line_number_returns_1_indexed(tmp_path: Path) -> None:
    f = tmp_path / "x.md"
    f.write_text("alpha\nbeta\ngamma\n")
    assert find_line_number(f, "beta") == 2
    assert find_line_number(f, "alpha") == 1


def test_find_line_number_raises_when_missing(tmp_path: Path) -> None:
    f = tmp_path / "x.md"
    f.write_text("only line\n")
    with pytest.raises(ActionItemError, match="could not locate"):
        find_line_number(f, "missing line")


def test_resolve_target_by_id_returns_entry_and_match(fake_data_dir: Path) -> None:
    m = IdMap.load(fake_data_dir)
    m.register(IdMapEntry("01HXAAA", "A3F7", "task X", "today.md", 5))
    m.save()
    items = [
        ActionItem(
            priority="🔴",
            title="task X",
            status="open",
            section="In Progress",
            context_links=[],
            notes=[],
            details=[],
            raw_line="- [ ] [#A3F7] 🔴 task X",
            short_prefix="A3F7",
        ),
        ActionItem(
            priority="",
            title="other",
            status="open",
            section="In Progress",
            context_links=[],
            notes=[],
            details=[],
            raw_line="- [ ] other",
            short_prefix=None,
        ),
    ]
    target, ulid, via = resolve_target(items=items, data_dir=fake_data_dir, by_id="A3F7", by_subject=None)
    assert target.title == "task X"
    assert ulid == "01HXAAA"
    assert via == "id"


def test_resolve_target_by_subject_substring(fake_data_dir: Path) -> None:
    items = [
        ActionItem(
            priority="🔴",
            title="Reply to vendor on contract",
            status="open",
            section="To Do",
            context_links=[],
            notes=[],
            details=[],
            raw_line="- [ ] 🔴 Reply to vendor on contract",
            short_prefix=None,
        ),
    ]
    target, ulid, via = resolve_target(items=items, data_dir=fake_data_dir, by_id=None, by_subject="vendor")
    assert target.title == "Reply to vendor on contract"
    assert ulid == ""
    assert via == "subject"


def test_resolve_target_rejects_both_args_unset(fake_data_dir: Path) -> None:
    with pytest.raises(ActionItemError, match="exactly one"):
        resolve_target(items=[], data_dir=fake_data_dir, by_id=None, by_subject=None)


def test_resolve_target_rejects_both_args_set(fake_data_dir: Path) -> None:
    with pytest.raises(ActionItemError, match="exactly one"):
        resolve_target(items=[], data_dir=fake_data_dir, by_id="A3F7", by_subject="x")


def test_resolve_target_unknown_id_raises(fake_data_dir: Path) -> None:
    with pytest.raises(ActionItemError, match="prefix.*not found"):
        resolve_target(items=[], data_dir=fake_data_dir, by_id="ZZZZ", by_subject=None)


def test_resolve_target_ambiguous_subject_raises(fake_data_dir: Path) -> None:
    items = [
        ActionItem(
            priority="",
            title="Reply to alice",
            status="open",
            section="To Do",
            context_links=[],
            notes=[],
            details=[],
            raw_line="- [ ] Reply to alice",
            short_prefix=None,
        ),
        ActionItem(
            priority="",
            title="Reply to bob",
            status="open",
            section="To Do",
            context_links=[],
            notes=[],
            details=[],
            raw_line="- [ ] Reply to bob",
            short_prefix=None,
        ),
    ]
    with pytest.raises(ActionItemError, match="ambiguous"):
        resolve_target(items=items, data_dir=fake_data_dir, by_id=None, by_subject="reply")


def test_resolve_target_prefix_in_idmap_but_missing_from_items_raises(
    fake_data_dir: Path,
) -> None:
    """If the IdMap knows a prefix but the parsed items list doesn't include it
    (e.g., user passed `--by-id A3F7` while looking at the wrong day's file),
    raise a clear error rather than silently no-op."""
    m = IdMap.load(fake_data_dir)
    m.register(IdMapEntry("01HXAAA", "A3F7", "task X", "today.md", 5))
    m.save()
    # Items list is empty — simulates the wrong-file case.
    with pytest.raises(ActionItemError, match="is in id-map but not present"):
        resolve_target(items=[], data_dir=fake_data_dir, by_id="A3F7", by_subject=None)
