"""Event dataclass returned by mutators.

In v0.4, mutators return an `Event` but nothing persists it. v0.5 will
add an `emit()` function that appends to the SQLite event store; the
shape defined here is its wire format. See v0.4 spec §13.2 and the v0.5+
event-architecture vision spec.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Event:
    """A single mutation event.

    Fields:
        id: ULID for the event itself (distinct from any entity ULID
            referenced in the payload).
        ts: ISO 8601 UTC timestamp with millisecond precision and 'Z'
            suffix, e.g. "2026-04-26T12:34:56.789Z".
        kind: Flat namespace, e.g. "action_item.completed".
        source: Origin tag, e.g. "cli:mark_done", "hook:connector-log".
        payload: Arbitrary JSON-compatible dict. Per-kind schemas are
            documented in the v0.5+ event-architecture spec.
    """

    id: str
    ts: str
    kind: str
    source: str
    payload: dict[str, Any]


def now_iso() -> str:
    """ISO 8601 UTC string with millisecond precision and 'Z' suffix."""
    n = dt.datetime.now(tz=dt.UTC)
    return n.strftime("%Y-%m-%dT%H:%M:%S.") + f"{n.microsecond // 1000:03d}Z"
