"""Unit tests for scout.action_items.snooze.

Source contract (from ~/Scout/action-items/snooze.py):
- Source line is REMOVED entirely (not replaced with a marker).
- A carry-in entry is appended to a '## 🛌 Snoozed' section in the target file:
    - [ ] {task body} _(carried in from {source_date})_
- Matching scans ALL tasks regardless of checkbox state (open and closed).
- until must be strictly after today (raises ActionItemError with 'past' substring).
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import pytest

from scout.action_items.snooze import snooze
from scout.errors import ActionItemError


def test_moves_task_to_future_daily_file(tmp_path: Path) -> None:
    src = tmp_path / "action-items-2026-04-15.md"
    src.write_text("## To Do\n\n- [ ] Reply to vendor\n- [ ] Other thing\n")
    dst = snooze(src, subject="Reply to vendor", until=dt.date(2026, 5, 1))
    assert dst == tmp_path / "action-items-2026-05-01.md"
    assert dst.exists()
    assert "Reply to vendor" in dst.read_text()
    # Source line is removed.
    src_after = src.read_text()
    assert "Reply to vendor" not in src_after
    # Unrelated task is untouched.
    assert "- [ ] Other thing" in src_after


def test_carry_in_annotation_in_dest(tmp_path: Path) -> None:
    src = tmp_path / "action-items-2026-04-15.md"
    src.write_text("- [ ] Call mechanic\n")
    dst = snooze(src, subject="Call mechanic", until=dt.date(2026, 5, 1))
    content = dst.read_text()
    assert "Call mechanic" in content
    assert "carried in from 2026-04-15" in content


def test_dest_has_snoozed_section(tmp_path: Path) -> None:
    src = tmp_path / "action-items-2026-04-15.md"
    src.write_text("- [ ] Buy milk\n")
    dst = snooze(src, subject="Buy milk", until=dt.date(2026, 5, 1))
    content = dst.read_text()
    assert "🛌 Snoozed" in content


def test_appends_to_existing_dest_file(tmp_path: Path) -> None:
    src = tmp_path / "action-items-2026-04-15.md"
    src.write_text("- [ ] New task\n")
    dst_path = tmp_path / "action-items-2026-05-01.md"
    dst_path.write_text("# Action Items — 2026-05-01\n\n## To Do\n\n- [ ] Pre-existing\n")
    dst = snooze(src, subject="New task", until=dt.date(2026, 5, 1))
    content = dst.read_text()
    assert "Pre-existing" in content
    assert "New task" in content


def test_removes_continuation_lines(tmp_path: Path) -> None:
    """Task block removal includes indented sub-items."""
    src = tmp_path / "action-items-2026-04-15.md"
    src.write_text("- [ ] Big task\n  - sub item A\n  - sub item B\n- [ ] Other task\n")
    snooze(src, subject="Big task", until=dt.date(2026, 5, 1))
    src_after = src.read_text()
    assert "Big task" not in src_after
    assert "sub item" not in src_after
    assert "- [ ] Other task" in src_after


def test_no_match_raises(tmp_path: Path) -> None:
    src = tmp_path / "action-items-2026-04-15.md"
    src.write_text("- [ ] something\n")
    with pytest.raises(ActionItemError, match="no match"):
        snooze(src, subject="missing", until=dt.date(2026, 5, 1))


def test_ambiguous_match_raises(tmp_path: Path) -> None:
    src = tmp_path / "action-items-2026-04-15.md"
    src.write_text("- [ ] vendor A\n- [ ] vendor B\n")
    with pytest.raises(ActionItemError, match="ambiguous|multiple"):
        snooze(src, subject="vendor", until=dt.date(2026, 5, 1))


def test_until_in_the_past_raises(tmp_path: Path) -> None:
    src = tmp_path / "action-items-2026-04-15.md"
    src.write_text("- [ ] task\n")
    with pytest.raises(ActionItemError, match="past"):
        snooze(src, subject="task", until=dt.date(2026, 4, 14))


def test_case_insensitive_match(tmp_path: Path) -> None:
    src = tmp_path / "action-items-2026-04-15.md"
    src.write_text("- [ ] Reply To Vendor\n")
    dst = snooze(src, subject="reply to vendor", until=dt.date(2026, 5, 1))
    assert "Reply To Vendor" in dst.read_text()


def test_matches_closed_tasks_too(tmp_path: Path) -> None:
    """Snooze can act on an already-closed task (source matches regardless of mark)."""
    src = tmp_path / "action-items-2026-04-15.md"
    src.write_text("- [x] Finished but reschedule\n")
    dst = snooze(src, subject="Finished but reschedule", until=dt.date(2026, 5, 1))
    assert "Finished but reschedule" in dst.read_text()


def test_returns_dest_path(tmp_path: Path) -> None:
    src = tmp_path / "action-items-2026-04-15.md"
    src.write_text("- [ ] task\n")
    result = snooze(src, subject="task", until=dt.date(2026, 5, 1))
    assert result == tmp_path / "action-items-2026-05-01.md"


def test_dedup_does_not_double_append(tmp_path: Path) -> None:
    """Re-snoozing skips if exact same subject already present in target section.

    Dedup compares the plain-text subject of existing entries.  An entry with
    an identical rest (no carry-in annotation yet) is treated as a duplicate.
    Note: entries that already carry a '_(carried in from …)_' annotation will
    NOT be detected as duplicates because the annotation changes the subject
    text — this matches the source's behaviour verbatim.
    """
    src = tmp_path / "action-items-2026-04-15.md"
    src.write_text("- [ ] task\n")
    dst_path = tmp_path / "action-items-2026-05-01.md"
    # Pre-existing entry has the SAME subject (no annotation yet).
    dst_path.write_text("## 🛌 Snoozed\n\n- [ ] task\n")
    snooze(src, subject="task", until=dt.date(2026, 5, 1))
    count = dst_path.read_text().count("task")
    # Only one mention — dedup prevented a second append.
    assert count == 1
