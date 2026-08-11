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


def test_repository_manifest_excludes_project_local_agent_integrations():
    repo_root = Path(__file__).resolve().parents[1]
    data = load_project_template_manifest(repo_root / "project-template.manifest.yaml")

    assert ".agents/" in data["include"]
    assert ".codex/config.toml" in data["exclude"]
    assert ".codex/hooks.json" in data["exclude"]
    assert ".agents/skills/ask-matt" in data["exclude"]
    assert ".agents/skills/setup-matt-pocock-skills" in data["exclude"]
    assert ".agents/skills/work-log-codex/tests/__pycache__/" in data["exclude"]
    assert ".claude/skills/ask-matt" in data["exclude"]
    assert ".claude/skills/setup-matt-pocock-skills" in data["exclude"]


def test_repository_template_keeps_codex_skills_only_in_agents_directory():
    repo_root = Path(__file__).resolve().parents[1]
    template = repo_root / "project-template"

    for base in (repo_root, template):
        assert (base / ".agents" / "skills" / "code-simplifier" / "SKILL.md").exists()
        assert (base / ".agents" / "skills" / "work-log-codex" / "SKILL.md").exists()
        assert not (base / ".codex" / "skills").exists()
