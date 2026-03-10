"""project_projection.py 的單元測試。"""

from pathlib import Path

import pytest

from script.utils import project_projection_manifest as ppm
from script.utils.project_blocks import read_managed_block
from script.utils.project_projection import hydrate_project, reconcile_project
from script.utils.project_tracking import load_tracking_file, save_tracking_file


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _make_template(base: Path) -> Path:
    template_dir = base / "template"
    _write(template_dir / "AGENTS.md", "# Project instructions\n")
    _write(template_dir / ".claude" / "commands" / "review.md", "review command\n")
    _write(template_dir / ".github" / "skills" / "demo" / "SKILL.md", "demo skill\n")
    _write(template_dir / ".github" / "copilot-instructions.md", "copilot\n")
    return template_dir


def _make_project(base: Path, project_id: str = "demo-project") -> Path:
    project_root = base / "project"
    (project_root / ".git" / "info").mkdir(parents=True)
    save_tracking_file(
        {
            "managed_by": "ai-dev",
            "schema_version": "2",
            "project_id": project_id,
            "template": {
                "name": "project-template",
                "url": "local://project-template",
                "branch": "main",
            },
            "projection": {
                "targets": ["claude", "codex", "gemini"],
                "profile": "default",
                "allow_local_generation": True,
            },
            "managed_files": [],
        },
        project_root,
    )
    return project_root


def test_hydrate_project_generates_files_and_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    template_dir = _make_template(tmp_path)
    project_root = _make_project(tmp_path)
    manifest_dir = tmp_path / "manifests" / "projects"
    monkeypatch.setattr(ppm, "get_project_manifest_dir", lambda: manifest_dir)

    result = hydrate_project(project_root, template_dir=template_dir)

    assert result.generated
    assert (project_root / "AGENTS.md").exists()
    assert (project_root / ".claude" / "commands" / "review.md").exists()
    assert (project_root / ".github" / "skills" / "demo" / "SKILL.md").exists()
    assert (project_root / ".git" / "info" / "exclude").exists()

    manifest = ppm.read_project_manifest("demo-project")
    assert manifest is not None
    assert manifest["files"]["AGENTS.md"]["kind"] == "managed_block"
    assert manifest["files"][".claude"]["kind"] == "dir"
    assert manifest["files"][".github/copilot-instructions.md"]["kind"] == "file"

    tracking = load_tracking_file(project_root)
    assert tracking is not None
    assert "AGENTS.md" in tracking["managed_files"]
    assert ".claude" in tracking["managed_files"]


def test_reconcile_project_skips_conflicting_managed_block_by_default(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    template_dir = _make_template(tmp_path)
    project_root = _make_project(tmp_path)
    manifest_dir = tmp_path / "manifests" / "projects"
    monkeypatch.setattr(ppm, "get_project_manifest_dir", lambda: manifest_dir)

    hydrate_project(project_root, template_dir=template_dir)
    manual_content = "# manually edited block\n"
    _write(template_dir / "AGENTS.md", "# Updated instructions\n")
    from script.utils.project_blocks import upsert_managed_block

    upsert_managed_block(project_root / "AGENTS.md", "ai-dev-project", manual_content)

    result = reconcile_project(project_root, template_dir=template_dir)

    assert "AGENTS.md" in result.conflicts
    assert "AGENTS.md" in result.skipped
    assert read_managed_block(project_root / "AGENTS.md", "ai-dev-project") == manual_content.strip()


def test_reconcile_project_force_overwrites_conflicting_managed_block(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    template_dir = _make_template(tmp_path)
    project_root = _make_project(tmp_path)
    manifest_dir = tmp_path / "manifests" / "projects"
    monkeypatch.setattr(ppm, "get_project_manifest_dir", lambda: manifest_dir)

    hydrate_project(project_root, template_dir=template_dir)
    from script.utils.project_blocks import upsert_managed_block

    upsert_managed_block(project_root / "AGENTS.md", "ai-dev-project", "# manual\n")
    _write(template_dir / "AGENTS.md", "# Updated instructions\n")

    result = reconcile_project(project_root, template_dir=template_dir, on_conflict="force")

    assert "AGENTS.md" not in result.conflicts
    assert "AGENTS.md" in result.generated
    assert read_managed_block(project_root / "AGENTS.md", "ai-dev-project") == "# Updated instructions"


def test_reconcile_project_backup_preserves_conflicting_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    template_dir = _make_template(tmp_path)
    project_root = _make_project(tmp_path)
    manifest_dir = tmp_path / "manifests" / "projects"
    monkeypatch.setattr(ppm, "get_project_manifest_dir", lambda: manifest_dir)

    hydrate_project(project_root, template_dir=template_dir)
    from script.utils.project_blocks import upsert_managed_block

    upsert_managed_block(project_root / "AGENTS.md", "ai-dev-project", "# manual\n")
    _write(template_dir / "AGENTS.md", "# Updated instructions\n")

    result = reconcile_project(project_root, template_dir=template_dir, on_conflict="backup")

    backup_root = project_root / "_backup_project_projection"

    assert "AGENTS.md" in result.generated
    assert read_managed_block(project_root / "AGENTS.md", "ai-dev-project") == "# Updated instructions"
    assert backup_root.exists()
    assert any(path.name == "AGENTS.md" for path in backup_root.rglob("AGENTS.md"))
