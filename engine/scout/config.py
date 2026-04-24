"""Layered configuration loader for Scout.

Precedence (low → high, later overrides earlier):
  1. Engine defaults (scout/defaults/scout-config.yaml, shipped with package)
  2. User overrides ($SCOUT_DATA_DIR/.scout-config.yaml)
  3. SCOUT_* environment variables (whitelisted keys)
"""

from __future__ import annotations

import os
from importlib.resources import as_file, files
from pathlib import Path
from typing import Any

import yaml

from scout import paths
from scout.errors import ConfigError


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        raise ConfigError(f"Invalid YAML in {path}: {e}") from e
    if not isinstance(data, dict):
        raise ConfigError(f"{path} must contain a YAML mapping at the top level")
    return data


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Recursive dict merge. `override` wins on conflicts."""
    result = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _env_overrides() -> dict[str, Any]:
    """Whitelisted SCOUT_* env vars → config overrides."""
    out: dict[str, Any] = {}
    if v := os.environ.get("SCOUT_USER_EMAIL"):
        out.setdefault("user", {})["email"] = v
    if v := os.environ.get("SCOUT_USER_TIMEZONE"):
        out.setdefault("user", {})["timezone"] = v
    return out


def _read_packaged_defaults() -> dict[str, Any]:
    """Read the shipped scout-config.yaml via importlib.resources.

    Resolving through importlib.resources keeps load_config() working
    when the package is installed from a wheel — Path(__file__).parent
    navigation breaks because the defaults sit under scout/defaults/
    in the installed tree, not relative to a sibling 'engine/' dir.
    """
    resource = files("scout") / "defaults" / "scout-config.yaml"
    with as_file(resource) as path:
        return _read_yaml(path)


def load_config(data_dir: Path | None = None) -> dict[str, Any]:
    """Load the three-layer merged config."""
    defaults = _read_packaged_defaults()
    user_path = paths.config_path(data_dir)
    user_overrides = _read_yaml(user_path)
    env_overrides = _env_overrides()

    merged = _deep_merge(defaults, user_overrides)
    merged = _deep_merge(merged, env_overrides)
    return merged
