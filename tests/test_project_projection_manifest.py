"""project_projection_manifest.py 的單元測試。"""

from pathlib import Path

import pytest

from script.utils import project_projection_manifest as ppm


def test_get_project_manifest_path_uses_projects_subdir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    manifest_dir = tmp_path / "manifests" / "projects"
    monkeypatch.setattr(ppm, "get_project_manifest_dir", lambda: manifest_dir)

    path = ppm.get_project_manifest_path("demo-project")

    assert path == manifest_dir / "demo-project.yaml"


def test_write_and_read_project_projection_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    manifest_dir = tmp_path / "manifests" / "projects"
    monkeypatch.setattr(ppm, "get_project_manifest_dir", lambda: manifest_dir)

    manifest = {
        "managed_by": "ai-dev",
        "schema_version": "1",
        "project_id": "demo-project",
        "files": {"AGENTS.md": {"kind": "managed_block", "hash": "sha256:test"}},
    }

    ppm.write_project_manifest("demo-project", manifest)
    loaded = ppm.read_project_manifest("demo-project")

    assert loaded is not None
    assert loaded["project_id"] == "demo-project"
    assert loaded["files"]["AGENTS.md"]["kind"] == "managed_block"


def test_read_project_manifest_returns_none_when_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    manifest_dir = tmp_path / "manifests" / "projects"
    monkeypatch.setattr(ppm, "get_project_manifest_dir", lambda: manifest_dir)

    assert ppm.read_project_manifest("missing-project") is None


def test_read_project_manifest_returns_none_for_invalid_yaml(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    manifest_dir = tmp_path / "manifests" / "projects"
    monkeypatch.setattr(ppm, "get_project_manifest_dir", lambda: manifest_dir)
    manifest_path = manifest_dir / "broken-project.yaml"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(":\n  - broken\n", encoding="utf-8")

    assert ppm.read_project_manifest("broken-project") is None
