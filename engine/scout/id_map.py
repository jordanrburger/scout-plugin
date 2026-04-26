"""Prefix↔ULID map persisted at $SCOUT_DATA_DIR/.scout-state/id-map.json.

Read-modify-write semantics use `flock(LOCK_EX)` per spec §6. The map
holds last-known position metadata so the diff engine can fuzzy-reattach
a markdown line whose `[#XXXX]` prefix was accidentally deleted.

See v0.4 spec §13.1.
"""

from __future__ import annotations

import fcntl
import json
import os
import tempfile
from collections.abc import Iterator
from dataclasses import asdict, dataclass
from pathlib import Path

from scout import paths


@dataclass(frozen=True)
class IdMapEntry:
    ulid: str
    short_prefix: str
    last_title: str
    last_file: str
    last_line: int


class IdMap:
    """Owns the prefix↔ULID JSON file. Construct via `IdMap.load(data_dir)`."""

    def __init__(self, data_dir: Path, entries: dict[str, IdMapEntry]) -> None:
        self._data_dir = data_dir
        self._entries: dict[str, IdMapEntry] = entries  # keyed by ULID

    @classmethod
    def load(cls, data_dir: Path) -> IdMap:
        path = paths.id_map_path(data_dir)
        if not path.exists():
            return cls(data_dir, entries={})
        with path.open("r", encoding="utf-8") as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_SH)
            try:
                raw = json.load(f)
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        entries = {ulid: IdMapEntry(**meta) for ulid, meta in raw.get("entries", {}).items()}
        return cls(data_dir, entries)

    def save(self) -> None:
        path = paths.id_map_path(self._data_dir)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": 1,
            "entries": {ulid: asdict(entry) for ulid, entry in self._entries.items()},
        }
        # Write under exclusive lock + atomic rename.
        fd, tmp = tempfile.mkstemp(prefix=".id-map.", suffix=".json.tmp", dir=str(path.parent))
        tmp_path = Path(tmp)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                try:
                    json.dump(payload, f, indent=2, sort_keys=True)
                    f.write("\n")
                    f.flush()
                    os.fsync(f.fileno())
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
            os.replace(tmp_path, path)
        except BaseException:
            if tmp_path.exists():
                tmp_path.unlink()
            raise

    def register(self, entry: IdMapEntry) -> None:
        """Insert or update an entry. Caller is responsible for `save()`."""
        self._entries[entry.ulid] = entry

    def lookup_by_prefix(self, prefix: str) -> IdMapEntry | None:
        for entry in self._entries.values():
            if entry.short_prefix == prefix:
                return entry
        return None

    def lookup_by_ulid(self, ulid: str) -> IdMapEntry | None:
        return self._entries.get(ulid)

    def in_use_prefixes(self) -> set[str]:
        return {entry.short_prefix for entry in self._entries.values()}

    def iter_entries(self) -> Iterator[IdMapEntry]:
        return iter(self._entries.values())

    def reattach(self, *, title: str, file: str) -> IdMapEntry | None:
        """Fuzzy-match an entry by title; prefer same-file matches.

        Used when a markdown line lost its `[#XXXX]` prefix. Title
        comparison is exact (case-sensitive); future enhancement could
        Levenshtein-fuzz this.
        """
        candidates = [e for e in self._entries.values() if e.last_title == title]
        if not candidates:
            return None
        same_file = [e for e in candidates if e.last_file == file]
        if same_file:
            return same_file[0]
        return candidates[0]
