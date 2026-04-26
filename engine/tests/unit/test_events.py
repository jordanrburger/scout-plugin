"""Unit tests for scout.events.Event."""

from __future__ import annotations

import dataclasses
import datetime as dt
import re

import pytest

from scout.events import Event, now_iso


def test_event_is_frozen() -> None:
    e = Event(
        id="01HXABC0000000000000000000",
        ts="2026-04-26T12:00:00.000Z",
        kind="action_item.completed",
        source="cli:mark_done",
        payload={"item_id": "01HXAAA0000000000000000000"},
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        e.kind = "action_item.snoozed"  # type: ignore[misc]


def test_event_has_required_fields() -> None:
    e = Event(
        id="01HXABC0000000000000000000",
        ts="2026-04-26T12:00:00.000Z",
        kind="action_item.completed",
        source="cli:mark_done",
        payload={},
    )
    assert e.id and e.ts and e.kind and e.source
    assert e.payload == {}


def test_now_iso_returns_iso8601_z() -> None:
    s = now_iso()
    # Match: YYYY-MM-DDTHH:MM:SS.mmmZ
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z", s)
    # Round-trip via fromisoformat (Python 3.11+ handles 'Z' as +00:00 only since 3.12;
    # we use the explicit Z stripper to keep 3.11 compat).
    parsed = dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
    assert parsed.tzinfo is not None


def test_event_payload_supports_arbitrary_json_compatible_dict() -> None:
    e = Event(
        id="01HX",
        ts="2026-04-26T00:00:00.000Z",
        kind="x.y.z",
        source="test",
        payload={"a": 1, "b": "two", "c": [3, 4], "d": {"e": True}},
    )
    assert e.payload["d"]["e"] is True
