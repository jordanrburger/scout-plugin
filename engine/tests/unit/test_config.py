"""Unit tests for scout.config."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from scout import config
from scout.errors import ConfigError


def _write(path: Path, data: dict) -> None:
    path.write_text(yaml.safe_dump(data))


def test_load_config_returns_defaults_when_no_user_override(
    clean_env: None, fake_data_dir: Path
) -> None:
    cfg = config.load_config(fake_data_dir)
    assert "budgets" in cfg
    assert "thresholds" in cfg
    assert cfg["schema_version"] == 1


def test_user_config_overrides_defaults(clean_env: None, fake_data_dir: Path) -> None:
    _write(
        fake_data_dir / ".scout-config.yaml",
        {"budgets": {"daily_budget_estimate_usd": 999}},
    )
    cfg = config.load_config(fake_data_dir)
    assert cfg["budgets"]["daily_budget_estimate_usd"] == 999
    # Other default keys preserved
    assert "max_per_session_usd" in cfg["budgets"]


def test_deep_merge_preserves_sibling_keys(clean_env: None, fake_data_dir: Path) -> None:
    _write(
        fake_data_dir / ".scout-config.yaml",
        {"user": {"email": "test@example.com"}},
    )
    cfg = config.load_config(fake_data_dir)
    assert cfg["user"]["email"] == "test@example.com"
    # Defaults for other user keys preserved
    assert "timezone" in cfg["user"]


def test_env_var_overrides_user_config(
    clean_env: None, fake_data_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write(
        fake_data_dir / ".scout-config.yaml",
        {"user": {"email": "user@example.com"}},
    )
    monkeypatch.setenv("SCOUT_USER_EMAIL", "env@example.com")
    cfg = config.load_config(fake_data_dir)
    assert cfg["user"]["email"] == "env@example.com"


def test_invalid_yaml_raises_config_error(
    clean_env: None, fake_data_dir: Path
) -> None:
    (fake_data_dir / ".scout-config.yaml").write_text("key: [unclosed")
    with pytest.raises(ConfigError, match="Invalid YAML"):
        config.load_config(fake_data_dir)


def test_non_mapping_yaml_raises_config_error(
    clean_env: None, fake_data_dir: Path
) -> None:
    (fake_data_dir / ".scout-config.yaml").write_text("- a\n- b\n")
    with pytest.raises(ConfigError, match="YAML mapping"):
        config.load_config(fake_data_dir)
