from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]

MP_SKILLS = [
    "mp-setup-matt-pocock-skills",
    "mp-grill-with-docs",
    "mp-to-issues",
    "mp-triage",
    "mp-improve-codebase-architecture",
    "mp-to-prd",
]

RUNTIME_MP_SKILLS = [skill for skill in MP_SKILLS if skill != "mp-setup-matt-pocock-skills"]


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _frontmatter(path: Path) -> dict:
    text = _read_text(path)
    assert text.startswith("---\n")
    raw = text.split("---\n", 2)[1]
    data = yaml.safe_load(raw)
    assert isinstance(data, dict)
    return data


def test_mp_skills_have_valid_frontmatter():
    for skill in MP_SKILLS:
        skill_path = ROOT / "skills" / skill / "SKILL.md"
        data = _frontmatter(skill_path)

        assert data["name"] == skill
        assert "description" in data
        assert "Use when:" in data["description"]


def test_mp_is_not_project_template_or_project_projection():
    assert not (ROOT / "project-template" / "docs" / "agents").exists()
    assert not (ROOT / ".claude" / "skills" / "mp-grill-with-docs").exists()
    assert not (ROOT / ".codex" / "skills" / "mp-grill-with-docs").exists()

    for entrypoint in ["CLAUDE.md", "AGENTS.md"]:
        text = _read_text(ROOT / entrypoint)

        assert "docs/agents/mp-workflow.md" not in text
        assert "mp-setup-matt-pocock-skills" not in text


def test_workflow_docs_include_mp_usage_guide():
    usage_guide = _read_text(
        ROOT / "docs" / "dev-guide" / "workflow" / "MP-USAGE-GUIDE.md"
    )
    dev_workflow = _read_text(
        ROOT / "docs" / "dev-guide" / "workflow" / "DEVELOPMENT-WORKFLOW.md"
    )
    integration_guide = _read_text(
        ROOT / "docs" / "dev-guide" / "workflow" / "mp-workflow-entry-layer.md"
    )

    assert "[MP 使用指南](MP-USAGE-GUIDE.md)" in dev_workflow
    assert "[MP 使用指南](MP-USAGE-GUIDE.md)" in integration_guide
    assert "### Phase 0.5: MP 工作入口" in dev_workflow
    assert "project-template" in usage_guide
    assert "不代表 `project-template` 應該預載 MP 共同文件" in usage_guide

    for skill in RUNTIME_MP_SKILLS:
        assert skill in usage_guide
        assert skill in dev_workflow

    assert "mp-setup-matt-pocock-skills" in usage_guide


def test_upstream_mapping_tracks_selected_and_excluded_skills():
    mapping = yaml.safe_load(
        _read_text(ROOT / "upstream" / "mattpocock-skills" / "mapping.yaml")
    )
    sources = yaml.safe_load(_read_text(ROOT / "upstream" / "sources.yaml"))

    assert sources["sources"]["mattpocock-skills"]["repo"] == "mattpocock/skills"
    assert sources["sources"]["mattpocock-skills"]["install_method"] == "manual"

    for source_name, skill in {
        "setup-matt-pocock-skills": "mp-setup-matt-pocock-skills",
        "grill-with-docs": "mp-grill-with-docs",
        "to-issues": "mp-to-issues",
        "triage": "mp-triage",
        "improve-codebase-architecture": "mp-improve-codebase-architecture",
        "to-prd": "mp-to-prd",
    }.items():
        entry = mapping["skills"][source_name]
        assert entry["local_skill"] == f"skills/{skill}/"
        assert entry["adaptation"] == "rewritten"

    assert mapping["excluded"]["tdd"]["reason"] == "covered-by-superpowers"
    assert mapping["excluded"]["diagnose"]["reason"] == "covered-by-superpowers"


def test_mp_trigger_boundaries_do_not_replace_openspec_or_superpowers():
    assert not (ROOT / "skills" / "mp-tdd").exists()
    assert not (ROOT / "skills" / "mp-diagnose").exists()

    setup = _read_text(ROOT / "skills" / "mp-setup-matt-pocock-skills" / "SKILL.md")
    to_issues = _read_text(ROOT / "skills" / "mp-to-issues" / "SKILL.md")
    usage_guide = _read_text(
        ROOT / "docs" / "dev-guide" / "workflow" / "MP-USAGE-GUIDE.md"
    )

    assert "proposal、design、spec、tasks、verify、archive" in usage_guide
    assert "OpenSpec 負責正式變更生命週期" in usage_guide
    assert "TDD、除錯、review" in usage_guide
    assert "Superpowers 負責任務內執行紀律" in usage_guide
    assert "沒有覆寫 `openspec-*` 或 `superpowers:*`" in setup
    assert "不適用於直接 TDD 實作" in to_issues
