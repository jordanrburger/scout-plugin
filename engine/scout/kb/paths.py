"""Resolve the KB schema and entity paths.

Engine ships scout/kb/schema.yaml as a default; users may override
by placing their own schema at $SCOUT_DATA_DIR/knowledge-base/ontology/schema.yaml.
"""

from __future__ import annotations

from importlib.resources import as_file, files
from pathlib import Path

from scout import paths


def resolve_schema_path(data: Path | None = None) -> Path:
    """Return the path to the active KB schema.

    Precedence: user override at
    $SCOUT_DATA_DIR/knowledge-base/ontology/schema.yaml, else the
    packaged default in scout/kb/schema.yaml extracted via
    importlib.resources.

    Caller is responsible for not mutating the returned path; under a
    wheel install the packaged copy may sit inside an importlib.resources
    extraction directory, but with a filesystem-installed wheel it is a
    real on-disk path.
    """
    user = paths.kb_dir(data) / "ontology" / "schema.yaml"
    if user.exists():
        return user
    resource = files("scout") / "kb" / "schema.yaml"
    with as_file(resource) as p:
        return Path(p)
