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


def test_mp_skill_projections_match_canonical_source():
    for skill in MP_SKILLS:
        canonical = _read_text(ROOT / "skills" / skill / "SKILL.md")

        assert _read_text(ROOT / ".claude" / "skills" / skill / "SKILL.md") == canonical
        assert _read_text(ROOT / ".codex" / "skills" / skill / "SKILL.md") == canonical


def test_entrypoints_reference_shared_agent_docs():
    for entrypoint in ["CLAUDE.md", "AGENTS.md"]:
        text = _read_text(ROOT / entrypoint)

        assert "docs/agents/mp-workflow.md" in text
        assert "docs/agents/issue-tracker.md" in text
        assert "docs/agents/triage-states.md" in text
        assert "docs/agents/domain.md" in text


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

    workflow = _read_text(ROOT / "docs" / "agents" / "mp-workflow.md")
    setup = _read_text(ROOT / "skills" / "mp-setup-matt-pocock-skills" / "SKILL.md")
    to_issues = _read_text(ROOT / "skills" / "mp-to-issues" / "SKILL.md")

    assert "proposal、design、tasks、spec、verify、archive" in workflow
    assert "使用 `openspec-*`" in workflow
    assert "TDD、除錯、review" in workflow
    assert "使用 `superpowers:*`" in workflow
    assert "沒有覆寫 `openspec-*` 或 `superpowers:*`" in setup
    assert "不適用於直接 TDD 實作" in to_issues
