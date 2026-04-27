"""Shared helpers for action-item mutators.

Factored out of mark_done/snooze/add_comment so each mutator's public
function is a thin wrapper around resolution + the actual mutation +
Event construction.
"""

from __future__ import annotations

from pathlib import Path

from scout.action_items.parser import ActionItem
from scout.errors import ActionItemError
from scout.id_map import IdMap


def find_line_number(path: Path, raw_line: str) -> int:
    """1-indexed line number where `raw_line` first appears as a complete line."""
    lines = path.read_text(encoding="utf-8").splitlines()
    for n, line in enumerate(lines, start=1):
        if line == raw_line:
            return n
    raise ActionItemError(f"could not locate line in {path.name}: {raw_line!r}")


def resolve_target(
    *,
    items: list[ActionItem],
    data_dir: Path,
    by_id: str | None,
    by_subject: str | None,
) -> tuple[ActionItem, str, str]:
    """Resolve which `ActionItem` a mutator should act on.

    Returns `(target, item_ulid, via)` where `via` is `"id"` or
    `"subject"`. `item_ulid` may be empty string if a `--by-subject` lookup
    matched a legacy unprefixed line and no IdMap entry exists for it.

    Raises `ActionItemError` on bad arguments, unknown prefix, no match,
    or ambiguous match.
    """
    if (by_id is None) == (by_subject is None):
        raise ActionItemError("resolve_target requires exactly one of by_id or by_subject")

    id_map = IdMap.load(data_dir)

    if by_id is not None:
        entry = id_map.lookup_by_prefix(by_id)
        if entry is None:
            raise ActionItemError(
                f"prefix [#{by_id}] not found in id-map; if this is a legacy line, retry with --by-subject"
            )
        match = next((i for i in items if i.short_prefix == by_id), None)
        if match is None:
            raise ActionItemError(f"prefix [#{by_id}] is in id-map but not present in this file")
        return match, entry.ulid, "id"

    # by_subject path
    assert by_subject is not None  # enforced by the exactly-one-of check above
    matches = [i for i in items if i.status == "open" and by_subject.lower() in i.raw_line.lower()]
    if len(matches) == 0:
        raise ActionItemError(f"no open task matched subject: {by_subject!r}")
    if len(matches) > 1:
        raise ActionItemError(
            f"ambiguous subject {by_subject!r}; matched:\n" + "\n".join(f"  - {m.title}" for m in matches)
        )
    match = matches[0]
    item_ulid = ""
    if match.short_prefix:
        sub_entry = id_map.lookup_by_prefix(match.short_prefix)
        if sub_entry is not None:
            item_ulid = sub_entry.ulid
    return match, item_ulid, "subject"
