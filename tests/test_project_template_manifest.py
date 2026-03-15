from pathlib import Path

from script.utils.project_template_manifest import load_project_template_manifest


def test_load_project_template_manifest_reads_include_and_exclude(tmp_path: Path):
    manifest_path = tmp_path / "project-template.manifest.yaml"
    manifest_path.write_text(
        "version: 1\n"
        "include:\n"
        "  - AGENTS.md\n"
        "  - .standards/\n"
        "exclude:\n"
        "  - .claude/settings.local.json\n",
        encoding="utf-8",
    )

    data = load_project_template_manifest(manifest_path)

    assert data["version"] == 1
    assert data["include"] == ["AGENTS.md", ".standards/"]
    assert data["exclude"] == [".claude/settings.local.json"]

