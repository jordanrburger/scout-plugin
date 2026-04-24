# Scout Engine Package Scaffolding (Plan 1 of 7) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Scaffold the `scout-engine` Python package inside `~/scout-plugin/engine/` with a Typer-based `scoutctl` CLI, core modules (`errors`, `paths`, `config`, `manifest`), a launcher shim for LaunchAgent contexts, full unit + performance test coverage, and GitHub Actions CI. When Plan 1 merges, `scoutctl --help`, `scoutctl version`, and `scoutctl manifest show` work; CI is green on macOS + Linux × Python 3.11/3.12; the foundation is in place for Plans 2–7 to port existing scripts and features.

**Architecture:** The engine is a proper Python package (`hatchling` build backend, `pip install -e .` for editable dev installs), with strict separation between a minimal-import CLI surface (Typer, stdlib only at module top) and heavy subsystems (textual, rich, jinja2, kb, tui) that load lazily. All paths resolve via `scout.paths` with `expanduser().resolve()` applied at the boundary. Config layers engine defaults → user overrides → env vars. The manifest (`manifest.json`) is the future contract with scout-app — this plan wires the baseline version/features scaffold.

**Tech Stack:** Python 3.11+, Typer 0.12+, PyYAML, Jinja2, pytest, mypy, ruff, hatchling, uv (for dev install), GitHub Actions.

---

## Context for the implementer

**Working directory:** All file paths in this plan are relative to `/Users/jordanburger/scout-plugin/`, which is a **separate repository** from the one where this plan lives. Before starting, `cd` into `~/scout-plugin` and confirm you're on the right repo:

```bash
cd ~/scout-plugin
git status
git remote -v
# Should show origin: https://github.com/jordanrburger/scout-plugin.git
```

**This plan does NOT modify** `~/scout-plugin/plugin.json`, `~/scout-plugin/commands/`, `~/scout-plugin/skills/`, `~/scout-plugin/phases/`, or `~/scout-plugin/templates/`. Those stay as they are; they're touched in Plans 4 and 5.

**Reference spec:** `/Users/jordanburger/scout-app/docs/superpowers/specs/2026-04-24-scout-unification-design.md` — see especially §4 (Engine package design) and §9 (Testing strategy).

## File structure (what Plan 1 creates)

```
~/scout-plugin/
├── engine/
│   ├── pyproject.toml
│   ├── README.md
│   ├── bin/scoutctl                  (bash launcher shim)
│   ├── defaults/scout-config.yaml
│   ├── scout/
│   │   ├── __init__.py
│   │   ├── __main__.py
│   │   ├── cli.py                    (Typer app — minimal imports)
│   │   ├── errors.py                 (exception hierarchy → exit codes)
│   │   ├── paths.py                  (path resolution)
│   │   ├── config.py                 (three-layer merge)
│   │   └── manifest.py               (capability manifest)
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py               (shared fixtures)
│       ├── unit/
│       │   ├── __init__.py
│       │   ├── test_errors.py
│       │   ├── test_paths.py
│       │   ├── test_config.py
│       │   └── test_manifest.py
│       └── perf/
│           ├── __init__.py
│           ├── test_startup.py
│           └── test_no_heavy_imports.py
└── .github/
    └── workflows/
        ├── test.yml
        └── lint.yml
```

Every file in this tree has one clear responsibility. `cli.py` wires subcommands but defers to the other modules. `errors.py` has no dependencies on other scout modules. `paths.py` depends only on `errors`. `config.py` depends on `paths` + `errors`. `manifest.py` depends only on `scout.__version__`. This keeps the import graph acyclic and easy to test in isolation.

---

## Task 0: Branch + pyproject.toml + package skeleton

**Files:**
- Create: `~/scout-plugin/engine/pyproject.toml`
- Create: `~/scout-plugin/engine/README.md`
- Create: `~/scout-plugin/engine/scout/__init__.py`
- Create: `~/scout-plugin/engine/scout/__main__.py`
- Create: `~/scout-plugin/engine/tests/__init__.py`
- Create: `~/scout-plugin/engine/tests/unit/__init__.py`
- Create: `~/scout-plugin/engine/tests/perf/__init__.py`
- Create: `~/scout-plugin/engine/tests/conftest.py`

- [ ] **Step 1: Create the migration branch**

Run:
```bash
cd ~/scout-plugin
git checkout main
git pull
git checkout -b migrate/v0.4.0-engine-scaffolding
```

Expected: branch created, clean working tree.

- [ ] **Step 2: Create `engine/pyproject.toml`**

```toml
[project]
name = "scout-engine"
version = "0.4.0"
description = "Scout engine: CLI, hooks, runners, and Python library for the Scout productivity system."
readme = "README.md"
requires-python = ">=3.11"
authors = [{name = "Jordan Burger"}]
license = {text = "MIT"}

dependencies = [
    "typer>=0.12",
    "pyyaml>=6.0",
    "jinja2>=3.1",
]

[project.optional-dependencies]
full = [
    "textual>=0.63",
    "rich>=13.7",
    "watchdog>=4.0",
]
dev = [
    "pytest>=8.0",
    "pytest-cov>=5.0",
    "mypy>=1.10",
    "ruff>=0.5",
    "types-PyYAML",
]

[project.scripts]
scoutctl = "scout.cli:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["scout"]

[tool.ruff]
line-length = 120
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "W", "I", "B", "UP"]

[tool.mypy]
python_version = "3.11"
strict = false
warn_unused_ignores = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
addopts = "-ra --strict-markers"
markers = [
    "perf: performance tests (may be skipped in fast CI runs)",
    "concurrency: tests involving multiple processes/threads",
    "slow: tests taking > 1 second",
]
```

- [ ] **Step 3: Create `engine/README.md`**

````markdown
# Scout Engine

Python package providing the `scoutctl` CLI, hooks, runners, and
library code for the Scout productivity system.

## Install (dev)

From this directory:

```bash
uv venv
uv pip install -e ".[dev,full]"
```

Verify:

```bash
scoutctl --help
scoutctl version
scoutctl manifest show
```

## Tests

```bash
pytest tests/
```

## See also

- `../plugin.json` — Claude Code plugin manifest
- Scout unification design spec lives in the scout-app repo under
  `docs/superpowers/specs/`.
````

- [ ] **Step 4: Create the empty package skeleton files**

Create `engine/scout/__init__.py`:
```python
"""Scout engine package."""

__version__ = "0.4.0"
```

Create `engine/scout/__main__.py`:
```python
"""Enable `python -m scout` invocation."""

from scout.cli import main

if __name__ == "__main__":
    main()
```

Create `engine/tests/__init__.py` (empty file):
```python
```

Create `engine/tests/unit/__init__.py` (empty):
```python
```

Create `engine/tests/perf/__init__.py` (empty):
```python
```

- [ ] **Step 5: Create `engine/tests/conftest.py`**

```python
"""Shared pytest fixtures."""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

import pytest


@pytest.fixture
def fake_data_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """A writable tmp data dir wired up via SCOUT_DATA_DIR."""
    d = tmp_path / "Scout"
    d.mkdir()
    (d / ".scout-logs").mkdir()
    (d / ".scout-cache").mkdir()
    (d / ".scout-state").mkdir()
    (d / "knowledge-base").mkdir()
    (d / "action-items").mkdir()
    monkeypatch.setenv("SCOUT_DATA_DIR", str(d))
    yield d


@pytest.fixture
def clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Unset any SCOUT_* env vars that might leak between tests."""
    for key in list(os.environ):
        if key.startswith("SCOUT_"):
            monkeypatch.delenv(key, raising=False)
```

- [ ] **Step 6: Create the venv and verify editable install**

Run:
```bash
cd ~/scout-plugin/engine
uv venv
uv pip install -e ".[dev]"
```

Expected: "Built scout-engine @ ..." and no errors.

Verify the venv exists:
```bash
ls .venv/bin/scoutctl
```

Expected: the file exists (but currently fails because `scout/cli.py` does not exist yet — that's fine, it'll be created in Task 5).

- [ ] **Step 7: Commit**

```bash
cd ~/scout-plugin
git add engine/pyproject.toml engine/README.md engine/scout/__init__.py engine/scout/__main__.py engine/tests/
git commit -m "feat(engine): scaffold scout-engine package with pyproject + empty package"
```

---

## Task 1: `scout.errors` with exit-code contract

**Files:**
- Create: `~/scout-plugin/engine/tests/unit/test_errors.py`
- Create: `~/scout-plugin/engine/scout/errors.py`

- [ ] **Step 1: Write the failing tests**

Create `engine/tests/unit/test_errors.py`:
```python
"""Unit tests for scout.errors."""

from __future__ import annotations

from scout.errors import (
    ActionItemError,
    ConfigError,
    ContractViolation,
    DataDirError,
    ExternalProcessError,
    KBError,
    SchemaVersionMismatch,
    ScoutError,
)


def test_exit_codes_are_stable() -> None:
    assert ScoutError.exit_code == 1
    assert ConfigError.exit_code == 10
    assert DataDirError.exit_code == 11
    assert SchemaVersionMismatch.exit_code == 12
    assert KBError.exit_code == 20
    assert ActionItemError.exit_code == 21
    assert ExternalProcessError.exit_code == 30
    assert ContractViolation.exit_code == 40


def test_schema_version_mismatch_message_names_versions() -> None:
    err = SchemaVersionMismatch(have=1, want=2)
    assert "v1" in str(err)
    assert "v2" in str(err)
    assert "scoutctl migrate" in str(err)


def test_all_subclasses_inherit_from_scout_error() -> None:
    for cls in (
        ConfigError,
        DataDirError,
        SchemaVersionMismatch,
        KBError,
        ActionItemError,
        ExternalProcessError,
        ContractViolation,
    ):
        assert issubclass(cls, ScoutError)
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
cd ~/scout-plugin/engine
.venv/bin/pytest tests/unit/test_errors.py -v
```

Expected: `ModuleNotFoundError: No module named 'scout.errors'` — tests fail to import.

- [ ] **Step 3: Implement `scout/errors.py`**

Create `engine/scout/errors.py`:
```python
"""Scout engine exception hierarchy and exit code contract.

Each ScoutError subclass maps to a specific exit code. The CLI
layer converts exceptions to exit codes + stderr messages.
Scout-app decodes exit codes back into specific Swift error cases.
"""

from __future__ import annotations


class ScoutError(Exception):
    """Base for all scout-specific errors."""

    exit_code = 1


class ConfigError(ScoutError):
    """Invalid or missing configuration."""

    exit_code = 10


class DataDirError(ScoutError):
    """SCOUT_DATA_DIR unset, invalid, or inaccessible."""

    exit_code = 11


class SchemaVersionMismatch(ScoutError):
    """Data dir schema version does not match engine expectation."""

    exit_code = 12

    def __init__(self, have: int, want: int) -> None:
        super().__init__(
            f"Data dir at schema v{have}; engine expects v{want}. "
            f"Run: scoutctl migrate data-dir --from {have} --to {want}"
        )
        self.have = have
        self.want = want


class KBError(ScoutError):
    """Knowledge-base query failure."""

    exit_code = 20


class ActionItemError(ScoutError):
    """Action-item operation failure (no-match, ambiguous, write error)."""

    exit_code = 21


class ExternalProcessError(ScoutError):
    """Subprocess (git, claude, launchctl) failed."""

    exit_code = 30


class ContractViolation(ScoutError):
    """Manifest missing a required feature flag."""

    exit_code = 40
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```bash
cd ~/scout-plugin/engine
.venv/bin/pytest tests/unit/test_errors.py -v
```

Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
cd ~/scout-plugin
git add engine/scout/errors.py engine/tests/unit/test_errors.py
git commit -m "feat(engine): add errors module with stable exit-code contract"
```

---

## Task 2: `scout.paths` with tilde/symlink expansion

**Files:**
- Create: `~/scout-plugin/engine/tests/unit/test_paths.py`
- Create: `~/scout-plugin/engine/scout/paths.py`

- [ ] **Step 1: Write the failing tests**

Create `engine/tests/unit/test_paths.py`:
```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
cd ~/scout-plugin/engine
.venv/bin/pytest tests/unit/test_paths.py -v
```

Expected: ImportError — `scout.paths` does not exist.

- [ ] **Step 3: Implement `scout/paths.py`**

Create `engine/scout/paths.py`:
```python
"""Path resolution for Scout engine and data dirs.

All paths are expanded (~) and resolved (symlinks, relative segments).
"""

from __future__ import annotations

import os
from pathlib import Path

from scout.errors import DataDirError

DEFAULT_DATA_DIR_NAME = "Scout"


def resolve_path(p: str | Path) -> Path:
    """Expand ~ and resolve symlinks/relative segments to an absolute Path."""
    return Path(p).expanduser().resolve()


def data_dir(explicit: str | Path | None = None) -> Path:
    """Resolve the Scout data directory.

    Precedence:
      1. Explicit argument
      2. $SCOUT_DATA_DIR env var
      3. ~/Scout

    Does NOT validate that the dir exists — callers use require_data_dir().
    """
    if explicit is not None:
        return resolve_path(explicit)

    env = os.environ.get("SCOUT_DATA_DIR")
    if env:
        return resolve_path(env)

    return resolve_path(Path.home() / DEFAULT_DATA_DIR_NAME)


def logs_dir(data: Path | None = None) -> Path:
    return (data or data_dir()) / ".scout-logs"


def cache_dir(data: Path | None = None) -> Path:
    return (data or data_dir()) / ".scout-cache"


def state_dir(data: Path | None = None) -> Path:
    return (data or data_dir()) / ".scout-state"


def config_path(data: Path | None = None) -> Path:
    return (data or data_dir()) / ".scout-config.yaml"


def kb_dir(data: Path | None = None) -> Path:
    return (data or data_dir()) / "knowledge-base"


def action_items_dir(data: Path | None = None) -> Path:
    return (data or data_dir()) / "action-items"


def require_data_dir(data: Path | None = None) -> Path:
    """Return the data dir, raising DataDirError if it does not exist."""
    d = data or data_dir()
    if not d.exists():
        raise DataDirError(
            f"Scout data dir does not exist: {d}\n"
            f"Run: scoutctl setup data-dir"
        )
    if not d.is_dir():
        raise DataDirError(f"Scout data dir is not a directory: {d}")
    return d
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```bash
cd ~/scout-plugin/engine
.venv/bin/pytest tests/unit/test_paths.py -v
```

Expected: 8 passed.

- [ ] **Step 5: Commit**

```bash
cd ~/scout-plugin
git add engine/scout/paths.py engine/tests/unit/test_paths.py
git commit -m "feat(engine): add paths module with tilde/symlink resolution"
```

---

## Task 3: `defaults/scout-config.yaml` (prerequisite for config module)

**Files:**
- Create: `~/scout-plugin/engine/defaults/scout-config.yaml`

- [ ] **Step 1: Create the defaults file**

Create `engine/defaults/scout-config.yaml`:
```yaml
schema_version: 1

user:
  email: ""
  github_username: ""
  slack_user_id: ""
  timezone: America/New_York
  company: ""
  display_name: ""

budgets:
  daily_budget_estimate_usd: 150
  max_per_session_usd: 20

thresholds:
  rate_limit_warn_pct: 80
  rate_limit_block_pct: 95
  connector_staleness_hours: 24

features:
  tui: true
  connector_health: true
  dreaming: true
```

- [ ] **Step 2: Verify the YAML parses**

Run:
```bash
cd ~/scout-plugin/engine
.venv/bin/python -c "import yaml; print(yaml.safe_load(open('defaults/scout-config.yaml')))"
```

Expected: a dict with keys `schema_version`, `user`, `budgets`, `thresholds`, `features` printed.

- [ ] **Step 3: Commit**

```bash
cd ~/scout-plugin
git add engine/defaults/scout-config.yaml
git commit -m "feat(engine): add engine defaults scout-config.yaml"
```

---

## Task 4: `scout.config` with three-layer merge

**Files:**
- Create: `~/scout-plugin/engine/tests/unit/test_config.py`
- Create: `~/scout-plugin/engine/scout/config.py`

- [ ] **Step 1: Write the failing tests**

Create `engine/tests/unit/test_config.py`:
```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
cd ~/scout-plugin/engine
.venv/bin/pytest tests/unit/test_config.py -v
```

Expected: `ModuleNotFoundError: No module named 'scout.config'`.

- [ ] **Step 3: Implement `scout/config.py`**

Create `engine/scout/config.py`:
```python
"""Layered configuration loader for Scout.

Precedence (low → high, later overrides earlier):
  1. Engine defaults (engine/defaults/scout-config.yaml, shipped with package)
  2. User overrides ($SCOUT_DATA_DIR/.scout-config.yaml)
  3. SCOUT_* environment variables (whitelisted keys)
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

from scout import paths
from scout.errors import ConfigError

PACKAGE_DEFAULTS_PATH = (
    Path(__file__).parent.parent / "defaults" / "scout-config.yaml"
)


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
        if (
            key in result
            and isinstance(result[key], dict)
            and isinstance(value, dict)
        ):
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


def load_config(data_dir: Path | None = None) -> dict[str, Any]:
    """Load the three-layer merged config."""
    defaults = _read_yaml(PACKAGE_DEFAULTS_PATH)
    user_path = paths.config_path(data_dir)
    user_overrides = _read_yaml(user_path)
    env_overrides = _env_overrides()

    merged = _deep_merge(defaults, user_overrides)
    merged = _deep_merge(merged, env_overrides)
    return merged
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```bash
cd ~/scout-plugin/engine
.venv/bin/pytest tests/unit/test_config.py -v
```

Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
cd ~/scout-plugin
git add engine/scout/config.py engine/tests/unit/test_config.py
git commit -m "feat(engine): add config module with three-layer merge"
```

---

## Task 5: `scout.manifest` with capability declaration

**Files:**
- Create: `~/scout-plugin/engine/tests/unit/test_manifest.py`
- Create: `~/scout-plugin/engine/scout/manifest.py`

- [ ] **Step 1: Write the failing tests**

Create `engine/tests/unit/test_manifest.py`:
```python
"""Unit tests for scout.manifest."""

from __future__ import annotations

import json
from pathlib import Path

from scout import __version__
from scout.manifest import build_manifest, write_manifest


def test_build_manifest_has_version() -> None:
    m = build_manifest()
    assert m.version == __version__


def test_build_manifest_has_schema_version() -> None:
    assert build_manifest().schema_version == 1


def test_build_manifest_exposes_known_features() -> None:
    m = build_manifest()
    expected = {
        "session_tokens_v1",
        "connector_health_v1",
        "action_items_cli_v1",
        "kb_ontology_v1",
        "tui_v1",
    }
    assert expected.issubset(m.features.keys())


def test_build_manifest_exposes_baseline_subcommands() -> None:
    m = build_manifest()
    assert "version" in m.subcommands
    assert "manifest" in m.subcommands


def test_manifest_json_is_stable_and_decodable() -> None:
    js = build_manifest().to_json()
    decoded = json.loads(js)
    assert decoded["version"] == __version__
    assert "features" in decoded
    assert "subcommands" in decoded


def test_write_manifest_round_trip(tmp_path: Path) -> None:
    target = tmp_path / "manifest.json"
    written = write_manifest(target)
    assert written == target
    decoded = json.loads(target.read_text())
    assert decoded["version"] == __version__
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
cd ~/scout-plugin/engine
.venv/bin/pytest tests/unit/test_manifest.py -v
```

Expected: `ModuleNotFoundError: No module named 'scout.manifest'`.

- [ ] **Step 3: Implement `scout/manifest.py`**

Create `engine/scout/manifest.py`:
```python
"""Engine capability manifest.

The manifest is the contract between scout-plugin (engine) and scout-app.
It declares which features and CLI subcommands this engine version
supports. Scout-app reads it at launch and refuses (with a helpful
banner) to use features the engine cannot provide.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from scout import __version__

ENGINE_DIR = Path(__file__).parent.parent


@dataclass
class EngineManifest:
    """Serializable capability manifest."""

    version: str
    schema_version: int
    features: dict[str, bool] = field(default_factory=dict)
    subcommands: list[str] = field(default_factory=list)

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, sort_keys=True)


def build_manifest() -> EngineManifest:
    """Construct the manifest from package state.

    Feature flags reflect what this version of the engine promises.
    Plans 2 and 3 flip individual flags to True as subsystems land.
    """
    return EngineManifest(
        version=__version__,
        schema_version=1,
        features={
            "session_tokens_v1": False,
            "connector_health_v1": False,
            "action_items_cli_v1": False,
            "kb_ontology_v1": False,
            "tui_v1": False,
        },
        subcommands=[
            "version",
            "manifest",
        ],
    )


def write_manifest(path: Path | None = None) -> Path:
    """Write the manifest to disk. Returns the path written."""
    target = path or (ENGINE_DIR / "manifest.json")
    target.write_text(build_manifest().to_json() + "\n")
    return target
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```bash
cd ~/scout-plugin/engine
.venv/bin/pytest tests/unit/test_manifest.py -v
```

Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
cd ~/scout-plugin
git add engine/scout/manifest.py engine/tests/unit/test_manifest.py
git commit -m "feat(engine): add manifest module with capability declaration"
```

---

## Task 6: `scout.cli` — Typer app with minimal imports

**Files:**
- Create: `~/scout-plugin/engine/scout/cli.py`

This task does not have a dedicated test file — `cli.py`'s correctness is covered by the perf test in Task 8 (no heavy imports) and by running the CLI manually. The Typer framework is well-tested upstream.

- [ ] **Step 1: Create `scout/cli.py`**

Create `engine/scout/cli.py`:
```python
"""scoutctl CLI entry point.

Top-level imports are intentionally minimal — Typer + stdlib only —
to keep `scoutctl --help` under 100ms. Heavy libraries (textual, rich,
jinja2, watchdog, scout.kb.*, scout.tui.*) must be imported inside
the subcommand functions, not at module level.
"""

from __future__ import annotations

import sys

import typer

from scout import __version__
from scout.errors import ScoutError

app = typer.Typer(
    name="scoutctl",
    help="Scout engine control CLI.",
    no_args_is_help=True,
    add_completion=False,
    rich_markup_mode=None,  # avoid importing rich at startup
)


@app.command()
def version() -> None:
    """Print the engine version."""
    print(__version__)


manifest_app = typer.Typer(help="Engine capability manifest operations.")
app.add_typer(manifest_app, name="manifest")


@manifest_app.command("build")
def manifest_build() -> None:
    """Write manifest.json to the engine dir."""
    from scout.manifest import write_manifest

    path = write_manifest()
    print(f"Wrote: {path}")


@manifest_app.command("show")
def manifest_show() -> None:
    """Print the current manifest to stdout."""
    from scout.manifest import build_manifest

    print(build_manifest().to_json())


def main() -> None:
    try:
        app()
    except ScoutError as e:
        print(str(e), file=sys.stderr)
        sys.exit(e.exit_code)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Reinstall the package (so the scoutctl script binding updates)**

Run:
```bash
cd ~/scout-plugin/engine
uv pip install -e ".[dev]"
```

Expected: "Successfully installed scout-engine..."

- [ ] **Step 3: Verify the CLI works end-to-end**

Run each command and confirm expected output:

```bash
.venv/bin/scoutctl --help
```
Expected: Typer help listing `version` and `manifest` commands, no errors.

```bash
.venv/bin/scoutctl version
```
Expected: `0.4.0`

```bash
.venv/bin/scoutctl manifest show
```
Expected: JSON matching the manifest structure (version, schema_version, features, subcommands).

- [ ] **Step 4: Commit**

```bash
cd ~/scout-plugin
git add engine/scout/cli.py
git commit -m "feat(engine): add scoutctl Typer CLI with version + manifest subcommands"
```

---

## Task 7: `bin/scoutctl` launcher shim

**Files:**
- Create: `~/scout-plugin/engine/bin/scoutctl`

The shim exists so LaunchAgents (which don't inherit user PATH) can still find the right Python interpreter.

- [ ] **Step 1: Create `engine/bin/scoutctl`**

Create `engine/bin/scoutctl`:
```bash
#!/usr/bin/env bash
# scoutctl launcher — resolves the venv Python deterministically so
# hooks invoked from LaunchAgents (which don't inherit user PATH)
# still find the right interpreter.
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ENGINE_DIR="${DIR%/bin}"
VENV_PY="${ENGINE_DIR}/.venv/bin/python"

if [ -x "$VENV_PY" ]; then
    exec "$VENV_PY" -m scout.cli "$@"
else
    exec python3 -m scout.cli "$@"
fi
```

- [ ] **Step 2: Make it executable**

Run:
```bash
chmod +x ~/scout-plugin/engine/bin/scoutctl
```

- [ ] **Step 3: Verify the shim runs without the venv on PATH**

Run (explicitly clearing PATH to simulate a LaunchAgent):
```bash
cd ~/scout-plugin
env -i PATH=/usr/bin:/bin HOME="$HOME" engine/bin/scoutctl version
```

Expected: `0.4.0` on stdout.

- [ ] **Step 4: Verify shellcheck is clean**

Run:
```bash
shellcheck ~/scout-plugin/engine/bin/scoutctl
```

Expected: no output (clean). If `shellcheck` is not installed, run `brew install shellcheck` first.

- [ ] **Step 5: Commit**

```bash
cd ~/scout-plugin
git add engine/bin/scoutctl
git commit -m "feat(engine): add scoutctl bash launcher shim for LaunchAgent contexts"
```

---

## Task 8: Performance tests — startup + no-heavy-imports

**Files:**
- Create: `~/scout-plugin/engine/tests/perf/test_startup.py`
- Create: `~/scout-plugin/engine/tests/perf/test_no_heavy_imports.py`

- [ ] **Step 1: Create `tests/perf/test_startup.py`**

```python
"""Startup-latency tests for scoutctl.

These assert that import + help + version paths stay fast so the
scout-app UI doesn't feel laggy when invoking scoutctl on user actions.

Budgets have CI headroom; local Macs hit them in half the listed time.
"""

from __future__ import annotations

import subprocess
import sys
import time

import pytest

HELP_BUDGET_MS = 250
VERSION_BUDGET_MS = 150


@pytest.mark.perf
def test_scoutctl_help_latency() -> None:
    start = time.perf_counter()
    result = subprocess.run(
        [sys.executable, "-m", "scout.cli", "--help"],
        capture_output=True,
        text=True,
        timeout=5,
    )
    elapsed_ms = (time.perf_counter() - start) * 1000
    assert result.returncode == 0
    assert elapsed_ms < HELP_BUDGET_MS, (
        f"scoutctl --help took {elapsed_ms:.0f}ms "
        f"(budget: {HELP_BUDGET_MS}ms). Check for heavy top-level imports."
    )


@pytest.mark.perf
def test_scoutctl_version_latency() -> None:
    start = time.perf_counter()
    result = subprocess.run(
        [sys.executable, "-m", "scout.cli", "version"],
        capture_output=True,
        text=True,
        timeout=5,
    )
    elapsed_ms = (time.perf_counter() - start) * 1000
    assert result.returncode == 0
    assert result.stdout.strip(), "version should emit to stdout"
    assert elapsed_ms < VERSION_BUDGET_MS, (
        f"scoutctl version took {elapsed_ms:.0f}ms "
        f"(budget: {VERSION_BUDGET_MS}ms)."
    )
```

- [ ] **Step 2: Create `tests/perf/test_no_heavy_imports.py`**

```python
"""Static import-graph test: forbids heavy imports at scoutctl startup.

Scout-app invokes scoutctl on every user action. If scout.cli imports
textual / rich / jinja2 / watchdog / scout.kb.*, startup balloons past
the latency budget. This test parses scout/cli.py's AST and fails on
top-level imports of the banned modules.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

BANNED_TOP_LEVEL = {
    "textual",
    "rich",
    "jinja2",
    "watchdog",
    "scout.kb",
    "scout.tui",
    "scout.action_items",
    "scout.runners",
    "scout.hooks",
    "scout.scripts",
}


def _top_level_imports(source: str) -> set[str]:
    tree = ast.parse(source)
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name.split(".")[0])
                names.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                names.add(node.module)
                names.add(node.module.split(".")[0])
    return names


CLI_PATH = Path(__file__).parent.parent.parent / "scout" / "cli.py"


@pytest.mark.perf
def test_cli_has_no_banned_top_level_imports() -> None:
    source = CLI_PATH.read_text()
    imports = _top_level_imports(source)
    offenders = imports & BANNED_TOP_LEVEL
    assert not offenders, (
        f"scout/cli.py has banned top-level imports: {offenders}. "
        f"Move them inside subcommand functions to preserve startup latency."
    )
```

- [ ] **Step 3: Run perf tests to verify they pass**

Run:
```bash
cd ~/scout-plugin/engine
.venv/bin/pytest tests/perf/ -v -m perf
```

Expected: 3 passed. If latency tests fail on a slow machine, examine the actual ms and confirm it's a machine issue, not a regression.

- [ ] **Step 4: Commit**

```bash
cd ~/scout-plugin
git add engine/tests/perf/test_startup.py engine/tests/perf/test_no_heavy_imports.py
git commit -m "test(engine): add perf tests for startup latency + import discipline"
```

---

## Task 9: GitHub Actions — `test.yml`

**Files:**
- Create: `~/scout-plugin/.github/workflows/test.yml`

- [ ] **Step 1: Create the workflow file**

Create `.github/workflows/test.yml`:
```yaml
name: test

on:
  push:
    branches: [main, "migrate/**"]
  pull_request:

jobs:
  test:
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, macos-latest]
        python: ["3.11", "3.12"]
    runs-on: ${{ matrix.os }}
    defaults:
      run:
        working-directory: engine
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - name: Setup Python
        run: uv python install ${{ matrix.python }}
      - name: Install
        run: uv pip install --system -e ".[dev]"
      - name: Pytest
        run: pytest tests/ -v
```

- [ ] **Step 2: Validate the YAML locally**

Run:
```bash
cd ~/scout-plugin
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/test.yml'))"
```

Expected: no output (valid YAML).

- [ ] **Step 3: Commit**

```bash
cd ~/scout-plugin
git add .github/workflows/test.yml
git commit -m "ci(engine): add GitHub Actions test workflow for macOS + Linux x py3.11/3.12"
```

---

## Task 10: GitHub Actions — `lint.yml`

**Files:**
- Create: `~/scout-plugin/.github/workflows/lint.yml`

- [ ] **Step 1: Create the lint workflow**

Create `.github/workflows/lint.yml`:
```yaml
name: lint

on:
  pull_request:
  push:
    branches: [main, "migrate/**"]

jobs:
  lint:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: engine
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - name: Setup Python
        run: uv python install 3.12
      - name: Install
        run: uv pip install --system -e ".[dev]"
      - name: Ruff check
        run: ruff check scout tests
      - name: Ruff format check
        run: ruff format --check scout tests
      - name: Mypy
        run: mypy scout
      - name: Shellcheck scoutctl
        run: |
          sudo apt-get update && sudo apt-get install -y shellcheck
          shellcheck bin/scoutctl
```

- [ ] **Step 2: Run ruff and mypy locally to confirm they're green**

Run:
```bash
cd ~/scout-plugin/engine
.venv/bin/ruff check scout tests
.venv/bin/ruff format --check scout tests
.venv/bin/mypy scout
```

Expected: each command exits 0 with no errors. If `ruff format --check` reports formatting issues, run `.venv/bin/ruff format scout tests` and commit the result before continuing.

- [ ] **Step 3: Validate the YAML**

```bash
cd ~/scout-plugin
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/lint.yml'))"
```

Expected: no output.

- [ ] **Step 4: Commit**

```bash
cd ~/scout-plugin
git add .github/workflows/lint.yml
git commit -m "ci(engine): add GitHub Actions lint workflow (ruff + mypy + shellcheck)"
```

---

## Task 11: Full verification + push

**Files:** none created in this task.

- [ ] **Step 1: Run the full test suite**

Run:
```bash
cd ~/scout-plugin/engine
.venv/bin/pytest tests/ -v
```

Expected: all unit + perf tests pass. Note the count — should be approximately 23 tests (3 errors + 8 paths + 6 config + 6 manifest + 3 perf).

- [ ] **Step 2: Run ruff and mypy one more time**

Run:
```bash
cd ~/scout-plugin/engine
.venv/bin/ruff check scout tests
.venv/bin/ruff format --check scout tests
.venv/bin/mypy scout
```

Expected: all green.

- [ ] **Step 3: Confirm `scoutctl` end-to-end from shim**

Run:
```bash
cd ~/scout-plugin
engine/bin/scoutctl version
engine/bin/scoutctl manifest show
```

Expected: version prints `0.4.0`; manifest show prints JSON with the expected keys.

- [ ] **Step 4: Review the commits and push**

Run:
```bash
cd ~/scout-plugin
git log --oneline main..HEAD
```

Expected: ~11 commits corresponding to the tasks above.

Push the branch:
```bash
git push -u origin migrate/v0.4.0-engine-scaffolding
```

- [ ] **Step 5: Open a draft PR on GitHub (optional but recommended)**

Use `gh` CLI:
```bash
cd ~/scout-plugin
gh pr create --draft --title "v0.4.0 Plan 1: engine package scaffolding" --body "$(cat <<'EOF'
## Summary

Plan 1 of 7 for Scout unification. Scaffolds the scout-engine Python package with:

- pyproject.toml + hatchling build backend
- `scout.errors` exit-code contract
- `scout.paths` tilde/symlink resolution
- `scout.config` three-layer merge (defaults → user → env)
- `scout.manifest` capability declaration
- `scout.cli` Typer app (minimal imports; `scoutctl --help` < 250ms)
- `bin/scoutctl` bash launcher shim for LaunchAgent contexts
- Unit tests + perf tests (startup latency + no-heavy-imports static check)
- CI: test (macOS + Linux × py3.11/3.12) and lint (ruff + mypy + shellcheck)

Plans 2–7 follow.

## Test plan

- [ ] CI test workflow green on both matrix rows
- [ ] CI lint workflow green
- [ ] Manual: `scoutctl --help`, `scoutctl version`, `scoutctl manifest show` all work locally
- [ ] Manual: `env -i PATH=/usr/bin:/bin HOME=$HOME engine/bin/scoutctl version` succeeds (LaunchAgent simulation)

Ref: `docs/superpowers/specs/2026-04-24-scout-unification-design.md` (in the scout-app repo).
EOF
)"
```

- [ ] **Step 6: Update the task tracker**

Plan 1 is complete when this PR merges. Plans 2–7 in the spec section 8 Migration Journey 1 are ready to begin.

---

## What Plans 2–7 will build on

Each subsequent plan operates on the same `migrate/v0.4.0-*` branch pattern in `~/scout-plugin` (or a successor branch), with the scaffolding from Plan 1 in place. Rough outlines:

- **Plan 2 — Port existing Python into the package.** Create `scout/action_items/`, `scout/kb/`, `scout/tui/` from `~/Scout/action-items/*.py`, `~/Scout/knowledge-base/ontology/*`, and `~/Scout/tui/*`. Flip `action_items_cli_v1`, `kb_ontology_v1`, `tui_v1` to True in the manifest.
- **Plan 3 — Port 11 shell scripts to Python.** `scout/runners/`, `scout/hooks/`, `scout/scripts/`. Each port paired with a parity test (bats diff of old shell vs new Python). Flip `session_tokens_v1`, `connector_health_v1` to True.
- **Plan 4 — `scoutctl setup` + plugin-level hooks.** Add `setup` subcommands; update `plugin.json` hooks array; render `~/Scout/.mcp.json` from template; render `~/Library/LaunchAgents/*.plist` from `engine/launchd_templates/`. Add `--with-examples` seed KB.
- **Plan 5 — Personal-data scrub + skill rewrites + kb_summary cache.** Build `kb_summary.json` cache; scrub SKILL.md / DREAMING.md / RESEARCH.md to generic templates; populate user KB entries for all cited people/projects/channels.
- **Plan 6 — scout-app refactor.** `ScoutEnvironment`, `EngineClient`, capability check, first-run wizard, path normalization, contract tests. Lives in the scout-app repo.
- **Plan 7 — Jordan's migration + v0.4.0 publish.** Unload old LaunchAgents, reload from new templates; remove dead files from `~/Scout`; tag v0.4.0; colleague updates.

---

## Self-review (inline; already applied)

**Spec coverage for Plan 1's scope:** §4 (Engine package design, layout, pyproject) → Tasks 0–6. §4 "Startup latency budget" → Tasks 6 + 8. §7 "Path normalization" (engine side; Python defense-in-depth) → Task 2. §9 (Testing strategy — unit + perf) → Tasks 1–8. §9 "CI" → Tasks 9–10. §10 (Error handling / exit codes) → Task 1. All §4 items for this plan are covered; wider items (hooks, runners, scripts, action_items, kb, tui, launchd) are explicitly deferred to Plans 2–4.

**Placeholder scan:** No "TBD" / "TODO" / "implement later" in tasks. Every code block is complete. Every test asserts concrete behavior.

**Type consistency:** `EngineManifest` fields `version: str`, `schema_version: int`, `features: dict[str, bool]`, `subcommands: list[str]` used consistently across `manifest.py`, `test_manifest.py`. `ScoutError.exit_code` is a class attribute (int) inherited by every subclass — consistent across `errors.py` and `test_errors.py`. `paths.data_dir()`, `paths.logs_dir()`, etc. all return `Path` and take `Path | None`. `config.load_config()` returns `dict[str, Any]` — consistent with test expectations.
