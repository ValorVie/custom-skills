from pathlib import Path

from script.utils.project_template_sync import sync_project_template


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_sync_project_template_only_copies_manifest_included_items(tmp_path: Path):
    repo_root = tmp_path / "repo"
    template_dir = repo_root / "project-template"
    repo_root.mkdir()
    template_dir.mkdir()

    _write(repo_root / "AGENTS.md", "root agents\n")
    _write(repo_root / ".standards" / "testing.ai.yaml", "x: 1\n")
    _write(repo_root / "README.md", "ignore me\n")

    manifest = {
        "version": 1,
        "include": ["AGENTS.md", ".standards/"],
        "exclude": [],
    }

    result = sync_project_template(
        repo_root=repo_root,
        template_dir=template_dir,
        manifest=manifest,
        check=False,
    )

    assert (template_dir / "AGENTS.md").exists()
    assert (template_dir / ".standards" / "testing.ai.yaml").exists()
    assert not (template_dir / "README.md").exists()
    assert result.copied == 2
    assert result.updated == 0


def test_sync_project_template_check_reports_clean_after_sync(tmp_path: Path):
    repo_root = tmp_path / "repo"
    template_dir = repo_root / "project-template"
    repo_root.mkdir()
    template_dir.mkdir()

    _write(repo_root / "AGENTS.md", "root agents\n")
    _write(repo_root / ".standards" / "testing.ai.yaml", "x: 1\n")

    manifest = {
        "version": 1,
        "include": ["AGENTS.md", ".standards/"],
        "exclude": [],
    }

    sync_project_template(
        repo_root=repo_root,
        template_dir=template_dir,
        manifest=manifest,
        check=False,
    )
    result = sync_project_template(
        repo_root=repo_root,
        template_dir=template_dir,
        manifest=manifest,
        check=True,
    )

    assert result.copied == 0
    assert result.updated == 0
    assert result.skipped == 0
    assert result.missing == []
