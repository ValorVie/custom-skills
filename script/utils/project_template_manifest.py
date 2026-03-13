from __future__ import annotations

from pathlib import Path

import yaml

PROJECT_TEMPLATE_MANIFEST_NAME = "project-template.manifest.yaml"


def get_project_template_manifest_path(repo_root: Path) -> Path:
    return Path(repo_root) / PROJECT_TEMPLATE_MANIFEST_NAME


def load_project_template_manifest(path: Path) -> dict:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    return {
        "version": int(data.get("version", 1)),
        "include": list(data.get("include", [])),
        "exclude": list(data.get("exclude", [])),
    }
