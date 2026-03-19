"""project_projection.py 的單元測試。"""

from pathlib import Path

import pytest

from script.utils import project_projection_manifest as ppm
from script.utils.project_blocks import (
    get_block_markers,
    read_managed_block,
    render_managed_block,
)
from script.utils.project_projection import (
    MANAGED_BLOCK_CLOSE_LABEL,
    MANAGED_BLOCK_OPEN_LABEL,
    PROJECT_MANAGED_BLOCK_ID,
    PROJECT_TEMPLATE_NAME,
    PROJECT_TEMPLATE_URL,
    hydrate_project,
    reconcile_project,
)
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
            "project_id": project_id,
            "template": {
                "name": PROJECT_TEMPLATE_NAME,
                "url": PROJECT_TEMPLATE_URL,
                "branch": "main",
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


def test_hydrate_project_unwraps_managed_block_source_without_second_run_drift(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    template_dir = _make_template(tmp_path)
    project_root = _make_project(tmp_path)
    manifest_dir = tmp_path / "manifests" / "projects"
    monkeypatch.setattr(ppm, "get_project_manifest_dir", lambda: manifest_dir)

    _write(
        template_dir / "AGENTS.md",
        render_managed_block(PROJECT_MANAGED_BLOCK_ID, "# Project instructions\n"),
    )

    first_result = hydrate_project(project_root, template_dir=template_dir)
    second_result = hydrate_project(project_root, template_dir=template_dir)

    start_marker, end_marker = get_block_markers(
        PROJECT_MANAGED_BLOCK_ID,
        open_label=MANAGED_BLOCK_OPEN_LABEL,
        close_label=MANAGED_BLOCK_CLOSE_LABEL,
    )
    content = (project_root / "AGENTS.md").read_text(encoding="utf-8")

    assert content.count(start_marker) == 1
    assert content.count(end_marker) == 1
    assert read_managed_block(project_root / "AGENTS.md", PROJECT_MANAGED_BLOCK_ID) == "# Project instructions"
    assert first_result.generated
    assert second_result.generated == []
    assert second_result.conflicts == []
    assert second_result.skipped == []


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

    upsert_managed_block(project_root / "AGENTS.md", PROJECT_MANAGED_BLOCK_ID, manual_content)

    result = reconcile_project(project_root, template_dir=template_dir)

    assert "AGENTS.md" in result.conflicts
    assert "AGENTS.md" in result.skipped
    assert read_managed_block(project_root / "AGENTS.md", PROJECT_MANAGED_BLOCK_ID) == manual_content.strip()


def test_reconcile_project_force_overwrites_conflicting_managed_block(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    template_dir = _make_template(tmp_path)
    project_root = _make_project(tmp_path)
    manifest_dir = tmp_path / "manifests" / "projects"
    monkeypatch.setattr(ppm, "get_project_manifest_dir", lambda: manifest_dir)

    hydrate_project(project_root, template_dir=template_dir)
    from script.utils.project_blocks import upsert_managed_block

    upsert_managed_block(project_root / "AGENTS.md", PROJECT_MANAGED_BLOCK_ID, "# manual\n")
    _write(template_dir / "AGENTS.md", "# Updated instructions\n")

    result = reconcile_project(project_root, template_dir=template_dir, on_conflict="force")

    assert "AGENTS.md" not in result.conflicts
    assert "AGENTS.md" in result.generated
    assert read_managed_block(project_root / "AGENTS.md", PROJECT_MANAGED_BLOCK_ID) == "# Updated instructions"


def test_reconcile_project_backup_preserves_conflicting_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    template_dir = _make_template(tmp_path)
    project_root = _make_project(tmp_path)
    manifest_dir = tmp_path / "manifests" / "projects"
    monkeypatch.setattr(ppm, "get_project_manifest_dir", lambda: manifest_dir)

    hydrate_project(project_root, template_dir=template_dir)
    from script.utils.project_blocks import upsert_managed_block

    upsert_managed_block(project_root / "AGENTS.md", PROJECT_MANAGED_BLOCK_ID, "# manual\n")
    _write(template_dir / "AGENTS.md", "# Updated instructions\n")

    result = reconcile_project(project_root, template_dir=template_dir, on_conflict="backup")

    backup_root = project_root / "_backup_project_projection"

    assert "AGENTS.md" in result.generated
    assert read_managed_block(project_root / "AGENTS.md", PROJECT_MANAGED_BLOCK_ID) == "# Updated instructions"
    assert backup_root.exists()
    assert any(path.name == "AGENTS.md" for path in backup_root.rglob("AGENTS.md"))


def test_hydrate_project_skips_noop_entries_on_second_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    template_dir = _make_template(tmp_path)
    project_root = _make_project(tmp_path)
    manifest_dir = tmp_path / "manifests" / "projects"
    monkeypatch.setattr(ppm, "get_project_manifest_dir", lambda: manifest_dir)

    first_result = hydrate_project(project_root, template_dir=template_dir)
    second_result = hydrate_project(project_root, template_dir=template_dir)

    assert first_result.generated
    assert second_result.generated == []
    assert second_result.conflicts == []
    assert second_result.skipped == []


def test_hydrate_project_respects_disabled_git_exclude(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    template_dir = _make_template(tmp_path)
    project_root = _make_project(tmp_path)
    manifest_dir = tmp_path / "manifests" / "projects"
    monkeypatch.setattr(ppm, "get_project_manifest_dir", lambda: manifest_dir)

    save_tracking_file(
        {
            "project_id": "demo-project",
            "template": {
                "name": PROJECT_TEMPLATE_NAME,
                "url": PROJECT_TEMPLATE_URL,
                "branch": "main",
            },
            "managed_files": [],
            "git_exclude": {
                "enabled": False,
                "version": "1",
                "patterns": [".claude/", "AGENTS.md"],
                "keep_tracked": [".editorconfig", ".gitattributes", ".gitignore"],
            },
        },
        project_root,
    )

    result = hydrate_project(project_root, template_dir=template_dir)

    assert result.generated
    assert not (project_root / ".git" / "info" / "exclude").exists()
