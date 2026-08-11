import json
from pathlib import Path

import pytest

from script.utils import auto_skill_projection as projection
from script.utils.auto_skill_projection import project_auto_skill
from script.utils.system import get_os


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_json(path: Path, content: str) -> None:
    _write(path, content)


@pytest.mark.skipif(get_os() == "windows", reason="Windows 使用 junction，檢查方式不同")
def test_project_auto_skill_creates_symlink(tmp_path: Path):
    source = tmp_path / "state"
    target = tmp_path / "tool" / "skills" / "auto-skill"
    _write(source / "SKILL.md", "auto skill\n")

    result = project_auto_skill(source, target)

    assert result.mode == "symlink"
    assert result.changed is True
    assert target.is_symlink()
    assert target.resolve() == source.resolve()


def test_project_auto_skill_falls_back_to_copy(tmp_path: Path, monkeypatch):
    source = tmp_path / "state"
    target = tmp_path / "tool" / "skills" / "auto-skill"
    _write(source / "SKILL.md", "auto skill\n")

    monkeypatch.setattr(projection, "_create_directory_link", lambda *_args, **_kwargs: None)

    result = project_auto_skill(source, target)

    assert result.mode == "copy"
    assert result.changed is True
    assert (target / "SKILL.md").read_text(encoding="utf-8") == "auto skill\n"


@pytest.mark.skipif(get_os() == "windows", reason="Windows 使用 junction，檢查方式不同")
def test_project_auto_skill_is_idempotent_for_existing_symlink(tmp_path: Path):
    source = tmp_path / "state"
    target = tmp_path / "tool" / "skills" / "auto-skill"
    _write(source / "SKILL.md", "auto skill\n")

    first = project_auto_skill(source, target)
    second = project_auto_skill(source, target)

    assert first.mode == "symlink"
    assert second.mode == "symlink"
    assert second.changed is False


@pytest.mark.skipif(get_os() == "windows", reason="Windows 使用 junction，檢查方式不同")
def test_project_auto_skill_migrates_legacy_dir_to_shadow_projection(tmp_path: Path):
    source = tmp_path / "state"
    policy_source = tmp_path / "policy-source"
    target = tmp_path / "tool" / "skills" / "auto-skill"
    projection_root = tmp_path / "projections"
    backup_root = tmp_path / "backups"

    _write(source / "SKILL.md", "canonical skill v2\n")
    _write(source / "knowledge-base" / "workflow.md", "canonical workflow\n")
    _write_json(
        source / "knowledge-base" / "_index.json",
        '{\n  "categories": [\n    {"id": "workflow", "count": 0},\n    {"id": "new-cat", "count": 0}\n  ]\n}\n',
    )
    _write_json(
        policy_source / ".clonepolicy.json",
        '{\n  "rules": [\n    {"pattern": "*/_index.json", "strategy": "key-merge"},\n    {"pattern": "knowledge-base/*.md", "strategy": "skip-if-exists"},\n    {"pattern": "experience/*.md", "strategy": "skip-if-exists"}\n  ]\n}\n',
    )

    _write(target / "SKILL.md", "legacy skill\n")
    _write(target / "knowledge-base" / "workflow.md", "legacy workflow\n")
    _write_json(
        target / "knowledge-base" / "_index.json",
        '{\n  "categories": [\n    {"id": "workflow", "count": 2}\n  ]\n}\n',
    )
    _write_json(
        target / ".clonepolicy.json",
        '{\n  "rules": [\n    {"pattern": "*/_index.json", "strategy": "key-merge"},\n    {"pattern": "knowledge-base/*.md", "strategy": "skip-if-exists"}\n  ]\n}\n',
    )

    result = project_auto_skill(
        source,
        target,
        target_name="claude",
        policy_source_dir=policy_source,
        projection_root=projection_root,
        backups_root=backup_root,
    )

    shadow_dir = projection_root / "claude" / "auto-skill"

    assert result.mode == "symlink"
    assert result.changed is True
    assert result.migrated_from == "legacy_dir"
    assert result.shadow_dir == shadow_dir
    assert target.is_symlink()
    assert target.resolve() == shadow_dir.resolve()
    assert (shadow_dir / "SKILL.md").read_text(encoding="utf-8") == "canonical skill v2\n"
    assert json.loads((shadow_dir / ".clonepolicy.json").read_text(encoding="utf-8")) == json.loads(
        (policy_source / ".clonepolicy.json").read_text(encoding="utf-8")
    )
    assert (shadow_dir / "knowledge-base" / "workflow.md").read_text(encoding="utf-8") == "legacy workflow\n"
    assert any(backup_root.joinpath("claude").iterdir())
    merged_index = (shadow_dir / "knowledge-base" / "_index.json").read_text(
        encoding="utf-8"
    )
    assert '"id": "workflow"' in merged_index
    assert '"count": 2' in merged_index
    assert '"id": "new-cat"' in merged_index


@pytest.mark.skipif(get_os() == "windows", reason="Windows 使用 junction，檢查方式不同")
def test_project_auto_skill_updates_shadow_with_canonical_policy(tmp_path: Path):
    source = tmp_path / "state"
    policy_source = tmp_path / "policy-source"
    target = tmp_path / "tool" / "skills" / "auto-skill"
    projection_root = tmp_path / "projections"
    backup_root = tmp_path / "backups"

    _write_json(
        policy_source / ".clonepolicy.json",
        '{\n  "rules": [\n    {"pattern": "*/_index.json", "strategy": "key-merge"},\n    {"pattern": "knowledge-base/*.md", "strategy": "skip-if-exists"}\n  ]\n}\n',
    )
    _write(source / "SKILL.md", "canonical skill v1\n")
    _write(source / "knowledge-base" / "workflow.md", "canonical workflow v1\n")
    _write_json(
        source / "knowledge-base" / "_index.json",
        '{\n  "categories": [\n    {"id": "workflow", "count": 0}\n  ]\n}\n',
    )

    first = project_auto_skill(
        source,
        target,
        target_name="claude",
        policy_source_dir=policy_source,
        projection_root=projection_root,
        backups_root=backup_root,
    )
    shadow_dir = first.shadow_dir
    assert shadow_dir is not None

    _write(shadow_dir / "knowledge-base" / "workflow.md", "custom workflow\n")
    _write(source / "SKILL.md", "canonical skill v2\n")
    _write_json(
        source / "knowledge-base" / "_index.json",
        '{\n  "categories": [\n    {"id": "workflow", "count": 0},\n    {"id": "new-cat", "count": 0}\n  ]\n}\n',
    )

    second = project_auto_skill(
        source,
        target,
        target_name="claude",
        policy_source_dir=policy_source,
        projection_root=projection_root,
        backups_root=backup_root,
    )

    assert second.mode == "symlink"
    assert second.changed is True
    assert target.resolve() == shadow_dir.resolve()
    assert (shadow_dir / "SKILL.md").read_text(encoding="utf-8") == "canonical skill v2\n"
    assert json.loads((shadow_dir / ".clonepolicy.json").read_text(encoding="utf-8")) == json.loads(
        (policy_source / ".clonepolicy.json").read_text(encoding="utf-8")
    )
    assert (shadow_dir / "knowledge-base" / "workflow.md").read_text(encoding="utf-8") == "custom workflow\n"
    merged_index = (shadow_dir / "knowledge-base" / "_index.json").read_text(
        encoding="utf-8"
    )
    assert '"id": "new-cat"' in merged_index


@pytest.mark.skipif(get_os() == "windows", reason="Windows 使用 junction，檢查方式不同")
def test_project_auto_skill_shadow_projection_is_revision_idempotent(tmp_path: Path):
    source = tmp_path / "state"
    policy_source = tmp_path / "policy-source"
    target = tmp_path / "tool" / "skills" / "auto-skill"
    projection_root = tmp_path / "projections"
    backup_root = tmp_path / "backups"

    _write(source / "SKILL.md", "canonical skill\n")
    _write_json(policy_source / ".clonepolicy.json", '{\n  "rules": []\n}\n')

    first = project_auto_skill(
        source,
        target,
        target_name="claude",
        policy_source_dir=policy_source,
        projection_root=projection_root,
        backups_root=backup_root,
    )
    second = project_auto_skill(
        source,
        target,
        target_name="claude",
        policy_source_dir=policy_source,
        projection_root=projection_root,
        backups_root=backup_root,
    )

    assert first.changed is True
    assert second.mode == "symlink"
    assert second.changed is False


@pytest.mark.skipif(get_os() == "windows", reason="Windows 使用 junction，檢查方式不同")
def test_project_auto_skill_rebuilds_shadow_after_legacy_policy_migration(tmp_path: Path):
    source = tmp_path / "state"
    policy_source = tmp_path / "policy-source"
    target = tmp_path / "tool" / "skills" / "auto-skill"
    projection_root = tmp_path / "projections"
    backup_root = tmp_path / "backups"

    _write(source / "SKILL.md", "canonical skill\n")
    _write_json(
        policy_source / ".clonepolicy.json",
        '{\n  "rules": [\n    {"pattern": "knowledge-base/*.md", "strategy": "skip-if-exists"}\n  ]\n}\n',
    )

    _write(target / "SKILL.md", "legacy skill\n")
    _write_json(target / ".clonepolicy.json", '{\n  "rules": []\n}\n')

    first = project_auto_skill(
        source,
        target,
        target_name="claude",
        policy_source_dir=policy_source,
        projection_root=projection_root,
        backups_root=backup_root,
    )
    shadow_state_path = projection_root / "claude" / "auto-skill.state.json"
    first_state = json.loads(shadow_state_path.read_text(encoding="utf-8"))

    second = project_auto_skill(
        source,
        target,
        target_name="claude",
        policy_source_dir=policy_source,
        projection_root=projection_root,
        backups_root=backup_root,
    )
    second_state = json.loads(shadow_state_path.read_text(encoding="utf-8"))

    assert first.changed is True
    assert first_state["policy_source"] == "legacy"
    assert second.changed is True
    assert second_state["policy_source"] == "canonical"
