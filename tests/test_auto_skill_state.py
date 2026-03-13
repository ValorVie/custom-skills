import json
from pathlib import Path

from script.utils.auto_skill_state import refresh_auto_skill_state


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def test_refresh_auto_skill_state_preserves_existing_user_content(tmp_path: Path):
    template = tmp_path / "template"
    upstream = tmp_path / "upstream"
    state = tmp_path / "state"

    _write_json(
        template / ".clonepolicy.json",
        {
            "rules": [
                {"pattern": "*/_index.json", "strategy": "key-merge"},
                {"pattern": "knowledge-base/*.md", "strategy": "skip-if-exists"},
                {"pattern": "experience/*.md", "strategy": "skip-if-exists"},
            ]
        },
    )
    _write(template / "SKILL.md", "template skill\n")
    _write_json(template / "knowledge-base" / "_index.json", {"categories": [{"id": "workflow", "count": 0}]})
    _write(template / "knowledge-base" / "workflow.md", "template workflow\n")
    _write(upstream / "SKILL.md", "upstream skill\n")
    _write_json(upstream / "experience" / "_index.json", {"skills": [{"skillId": "state-a", "count": 0}]})
    _write(upstream / "experience" / "skill-state-a.md", "upstream experience\n")
    _write(upstream / ".git" / "config", "should-not-copy\n")

    _write(state / "SKILL.md", "stale skill\n")
    _write(state / "knowledge-base" / "workflow.md", "user content\n")

    result = refresh_auto_skill_state(
        template_dir=template,
        upstream_dir=upstream,
        state_dir=state,
    )

    assert result == state
    assert (state / "SKILL.md").read_text(encoding="utf-8") == "template skill\n"
    assert (state / "knowledge-base" / "workflow.md").read_text(encoding="utf-8") == "user content\n"
    assert (state / "experience" / "skill-state-a.md").read_text(encoding="utf-8") == "upstream experience\n"
    assert json.loads((state / ".clonepolicy.json").read_text(encoding="utf-8")) == json.loads(
        (template / ".clonepolicy.json").read_text(encoding="utf-8")
    )
    assert not (state / ".git" / "config").exists()


def test_refresh_auto_skill_state_returns_none_without_sources(tmp_path: Path):
    result = refresh_auto_skill_state(
        template_dir=tmp_path / "missing-template",
        upstream_dir=tmp_path / "missing-upstream",
        state_dir=tmp_path / "state",
    )

    assert result is None


def test_refresh_auto_skill_state_falls_back_to_template_policy_for_upstream_indexes(
    tmp_path: Path,
):
    template = tmp_path / "template"
    upstream = tmp_path / "upstream"
    state = tmp_path / "state"

    _write_json(
        template / ".clonepolicy.json",
        {
            "rules": [
                {"pattern": "*/_index.json", "strategy": "key-merge"},
                {"pattern": "knowledge-base/*.md", "strategy": "skip-if-exists"},
                {"pattern": "experience/*.md", "strategy": "skip-if-exists"},
            ]
        },
    )
    _write(template / "SKILL.md", "template skill\n")
    _write_json(
        template / "knowledge-base" / "_index.json",
        {"categories": [{"id": "workflow", "count": 0}]},
    )
    _write_json(
        template / "experience" / "_index.json",
        {"skills": [{"skillId": "template-skill", "count": 0}]},
    )

    _write(upstream / "SKILL.md", "upstream skill\n")
    _write_json(
        upstream / "knowledge-base" / "_index.json",
        {"categories": [{"id": "upstream-cat", "count": 0}]},
    )
    _write_json(
        upstream / "experience" / "_index.json",
        {"skills": [{"skillId": "upstream-skill", "count": 0}]},
    )

    _write_json(
        state / "knowledge-base" / "_index.json",
        {"categories": [{"id": "user-cat", "count": 3}]},
    )
    _write_json(
        state / "experience" / "_index.json",
        {"skills": [{"skillId": "user-skill", "count": 2}]},
    )

    result = refresh_auto_skill_state(
        template_dir=template,
        upstream_dir=upstream,
        state_dir=state,
    )

    assert result == state
    knowledge_index = json.loads(
        (state / "knowledge-base" / "_index.json").read_text(encoding="utf-8")
    )
    experience_index = json.loads(
        (state / "experience" / "_index.json").read_text(encoding="utf-8")
    )
    assert {item["id"] for item in knowledge_index["categories"]} == {
        "user-cat",
        "workflow",
        "upstream-cat",
    }
    assert {item["skillId"] for item in experience_index["skills"]} == {
        "user-skill",
        "template-skill",
        "upstream-skill",
    }
