"""Unit tests for scout.ids — ULID + short-prefix generation."""

from __future__ import annotations

import pytest

from scout.ids import (
    CROCKFORD_ALPHABET,
    SHORT_PREFIX_LEN,
    new_short_prefix,
    new_ulid,
    short_prefix_pattern,
)


def test_new_ulid_returns_26_char_string() -> None:
    val = new_ulid()
    assert isinstance(val, str)
    assert len(val) == 26


def test_new_ulid_is_unique_across_calls() -> None:
    seen: set[str] = set()
    for _ in range(100):
        seen.add(new_ulid())
    assert len(seen) == 100


def test_new_short_prefix_is_4_crockford_chars() -> None:
    p = new_short_prefix()
    assert len(p) == SHORT_PREFIX_LEN == 4
    assert all(c in CROCKFORD_ALPHABET for c in p)


def test_new_short_prefix_excludes_ambiguous_chars() -> None:
    # Crockford base32 excludes I, L, O, U to avoid 0/O and 1/I/L visual collisions.
    for c in "ILOU":
        assert c not in CROCKFORD_ALPHABET


def test_short_prefix_pattern_matches_well_formed_prefix() -> None:
    rx = short_prefix_pattern()
    assert rx.fullmatch("[#A3F7]")
    assert rx.fullmatch("[#0000]")
    # Hyphens and lowercase are not allowed.
    assert not rx.fullmatch("[#a3f7]")
    assert not rx.fullmatch("[#A-37]")
    # Wrong length.
    assert not rx.fullmatch("[#A3F]")
    assert not rx.fullmatch("[#A3F7E]")


def test_short_prefix_pattern_finds_prefix_in_line() -> None:
    rx = short_prefix_pattern()
    line = "- [ ] [#A3F7] Submit Lever feedback"
    m = rx.search(line)
    assert m is not None
    assert m.group(0) == "[#A3F7]"
    assert m.group(1) == "A3F7"


def test_new_short_prefix_excludes_set_member() -> None:
    """Caller passes an in-use set; generator retries until it lands outside."""
    in_use = {new_short_prefix() for _ in range(5)}
    # With ~1M space and 5 used prefixes, this lands in one try almost surely;
    # the test asserts the contract, not the retry count.
    p = new_short_prefix(exclude=in_use)
    assert p not in in_use


def test_new_short_prefix_raises_when_exhausted(monkeypatch: pytest.MonkeyPatch) -> None:
    """When all retries hit `exclude`, the generator raises instead of looping forever."""
    import secrets

    # Force every generated prefix to be "AAAA" so it deterministically hits the exclude set.
    monkeypatch.setattr(secrets, "choice", lambda _: "A")
    with pytest.raises(RuntimeError, match="prefix space exhausted"):
        new_short_prefix(exclude={"AAAA"}, max_attempts=3)
