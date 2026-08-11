"""auto-skill 退役封存與有效路徑隔離測試。"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_auto_skill_is_archived_by_category_and_not_active() -> None:
    archive = ROOT / "archive" / "auto-skill"
    required = (
        archive / "README.md",
        archive / "skill" / "SKILL.md",
        archive / "project-knowledge" / "knowledge-base" / "_index.json",
        archive / "claude-plugin" / "hooks" / "hooks.json",
        archive / "implementation" / "script" / "utils" / "auto_skill_state.py",
        archive / "specs" / "openspec" / "knowledge-injection" / "spec.md",
    )

    assert all(path.exists() for path in required)
    assert not (ROOT / "skills" / "auto-skill").exists()
    assert not (ROOT / ".claude" / "skills" / "auto-skill").exists()
    assert not (ROOT / "plugins" / "auto-skill-hooks").exists()

    marketplace = json.loads(
        (ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8")
    )
    assert "auto-skill-hooks" not in {
        plugin["name"] for plugin in marketplace["plugins"]
    }


def test_archive_explains_harness_replacement_and_shared_agent_skills() -> None:
    readme = (ROOT / "archive" / "auto-skill" / "README.md").read_text(encoding="utf-8")

    assert "harness agent tool" in readme
    assert "Prime Agent" in readme
    assert ".agents/skills" in readme
    assert "不再安裝、分發或觸發" in readme
