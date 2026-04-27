"""ULID generation and Crockford base32 short prefixes.

Short prefixes are the human-friendly surface form for action-item IDs in
markdown; the full ULID is the canonical storage form. See v0.4 spec §13.1.

The Crockford alphabet excludes 0/O and 1/I/L visual confusables (and
also U) so that hand-typed prefixes are unambiguous.
"""

from __future__ import annotations

import re
import secrets

from ulid import ULID

# Crockford base32 alphabet: 0-9 + uppercase A-Z minus I, L, O, U.
CROCKFORD_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
SHORT_PREFIX_LEN = 4

_DEFAULT_MAX_ATTEMPTS = 64  # plenty for any realistic in-use set

_PREFIX_REGEX = re.compile(r"\[#(" + f"[{re.escape(CROCKFORD_ALPHABET)}]" + r"{" + str(SHORT_PREFIX_LEN) + r"})\]")


def new_ulid() -> str:
    """Mint a fresh 26-character ULID (sortable, time-ordered)."""
    return str(ULID())


def new_short_prefix(
    exclude: set[str] | None = None,
    max_attempts: int = _DEFAULT_MAX_ATTEMPTS,
) -> str:
    """Generate a fresh 4-char Crockford base32 prefix not in `exclude`.

    `exclude` is the set of currently-in-use short prefixes (typically
    sourced from `scout.id_map.IdMap.in_use_prefixes()`). Raises
    `RuntimeError` if `max_attempts` retries all hit the exclude set —
    indicates the prefix space is approaching saturation, which would
    require widening to 5 chars (out of scope for v0.4).
    """
    exclude = exclude or set()
    for _ in range(max_attempts):
        candidate = "".join(secrets.choice(CROCKFORD_ALPHABET) for _ in range(SHORT_PREFIX_LEN))
        if candidate not in exclude:
            return candidate
    raise RuntimeError(f"prefix space exhausted after {max_attempts} attempts (exclude size {len(exclude)})")


def short_prefix_pattern() -> re.Pattern[str]:
    """Regex matching `[#XXXX]` where XXXX is 4 Crockford chars.

    `match.group(0)` returns the full bracketed prefix; `match.group(1)`
    returns the bare 4-char prefix.
    """
    return _PREFIX_REGEX
