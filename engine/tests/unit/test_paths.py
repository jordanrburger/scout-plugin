"""Unit tests for scout.paths."""

from __future__ import annotations

from pathlib import Path

import pytest

from scout import paths
from scout.errors import DataDirError


def test_data_dir_explicit_argument(clean_env: None, tmp_path: Path) -> None:
    target = tmp_path / "custom-scout"
    result = paths.data_dir(target)
    assert result == target.resolve()


def test_data_dir_reads_env_var(
    clean_env: None, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SCOUT_DATA_DIR", str(tmp_path))
    assert paths.data_dir() == tmp_path.resolve()


def test_data_dir_falls_back_to_home(clean_env: None) -> None:
    result = paths.data_dir()
    assert result == (Path.home() / "Scout").resolve()


def test_data_dir_expands_tilde(
    clean_env: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SCOUT_DATA_DIR", "~/Scout")
    result = paths.data_dir()
    assert "~" not in str(result)
    assert result.is_absolute()


def test_resolve_path_resolves_symlinks(tmp_path: Path) -> None:
    real = tmp_path / "real"
    real.mkdir()
    link = tmp_path / "link"
    link.symlink_to(real)
    assert paths.resolve_path(link) == real.resolve()


def test_require_data_dir_missing_raises(tmp_path: Path) -> None:
    missing = tmp_path / "does-not-exist"
    with pytest.raises(DataDirError, match="does not exist"):
        paths.require_data_dir(missing)


def test_require_data_dir_file_not_dir(tmp_path: Path) -> None:
    not_dir = tmp_path / "file"
    not_dir.write_text("")
    with pytest.raises(DataDirError, match="not a directory"):
        paths.require_data_dir(not_dir)


def test_derived_paths_under_data_dir(tmp_path: Path) -> None:
    assert paths.logs_dir(tmp_path) == tmp_path / ".scout-logs"
    assert paths.cache_dir(tmp_path) == tmp_path / ".scout-cache"
    assert paths.state_dir(tmp_path) == tmp_path / ".scout-state"
    assert paths.config_path(tmp_path) == tmp_path / ".scout-config.yaml"
    assert paths.kb_dir(tmp_path) == tmp_path / "knowledge-base"
    assert paths.action_items_dir(tmp_path) == tmp_path / "action-items"
