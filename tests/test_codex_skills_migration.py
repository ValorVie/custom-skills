from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from script.utils import codex_skills_migration as migration


def _skill(root: Path, name: str, content: str = "body") -> Path:
    skill = root / name
    (skill / "agents").mkdir(parents=True)
    (skill / "references").mkdir()
    (skill / "scripts").mkdir()
    (skill / "assets").mkdir()
    (skill / "SKILL.md").write_text(content, encoding="utf-8")
    (skill / "agents" / "openai.yaml").write_text("interface: {}\n", encoding="utf-8")
    (skill / "references" / "guide.md").write_text("guide\n", encoding="utf-8")
    (skill / "scripts" / "run.py").write_text("print('ok')\n", encoding="utf-8")
    (skill / "assets" / "template.txt").write_text("template\n", encoding="utf-8")
    return skill


def test_fresh_install_without_legacy_directory_is_noop(tmp_path: Path) -> None:
    legacy = tmp_path / ".codex" / "skills"
    target = tmp_path / ".agents" / "skills"
    backups = tmp_path / "backups"

    result = migration.migrate_legacy_codex_skills(
        legacy_dir=legacy,
        target_dir=target,
        backup_root=backups,
    )

    assert result.changed is False
    assert result.migrated == ()
    assert not target.exists()
    assert not backups.exists()


def test_migrates_whole_skill_directory_and_writes_audit(tmp_path: Path) -> None:
    legacy = tmp_path / ".codex" / "skills"
    target = tmp_path / ".agents" / "skills"
    backups = tmp_path / "backups"
    _skill(legacy, "demo")

    result = migration.migrate_legacy_codex_skills(
        legacy_dir=legacy,
        target_dir=target,
        backup_root=backups,
    )

    assert result.changed is True
    assert result.migrated == ("demo",)
    assert not (legacy / "demo").exists()
    assert (target / "demo" / "SKILL.md").read_text(encoding="utf-8") == "body"
    assert (target / "demo" / "agents" / "openai.yaml").exists()
    assert (target / "demo" / "references" / "guide.md").exists()
    assert (target / "demo" / "scripts" / "run.py").exists()
    assert (target / "demo" / "assets" / "template.txt").exists()
    assert result.backup_dir is not None
    assert (result.backup_dir / "demo" / "SKILL.md").exists()
    audit = json.loads((result.backup_dir / "audit.json").read_text(encoding="utf-8"))
    assert audit["status"] == "complete"
    assert audit["actions"] == [{"action": "migrate", "name": "demo"}]


def test_identical_target_is_deduplicated_after_backup(tmp_path: Path) -> None:
    legacy = tmp_path / ".codex" / "skills"
    target = tmp_path / ".agents" / "skills"
    backups = tmp_path / "backups"
    _skill(legacy, "same")
    _skill(target, "same")

    result = migration.migrate_legacy_codex_skills(
        legacy_dir=legacy,
        target_dir=target,
        backup_root=backups,
    )

    assert result.deduplicated == ("same",)
    assert not (legacy / "same").exists()
    assert (target / "same" / "SKILL.md").exists()
    assert result.backup_dir is not None
    assert (result.backup_dir / "same" / "SKILL.md").exists()


def test_conflict_keeps_both_versions_and_writes_audit(
    tmp_path: Path,
) -> None:
    legacy = tmp_path / ".codex" / "skills"
    target = tmp_path / ".agents" / "skills"
    backups = tmp_path / "backups"
    _skill(legacy, "conflict", "legacy")
    _skill(target, "conflict", "target")

    result = migration.migrate_legacy_codex_skills(
        legacy_dir=legacy,
        target_dir=target,
        backup_root=backups,
    )

    assert result.conflicts == ("conflict",)
    assert result.changed is False
    assert (legacy / "conflict" / "SKILL.md").read_text(encoding="utf-8") == "legacy"
    assert (target / "conflict" / "SKILL.md").read_text(encoding="utf-8") == "target"
    audit_dir = next(backups.iterdir())
    audit = json.loads((audit_dir / "audit.json").read_text(encoding="utf-8"))
    assert audit["status"] == "conflict"
    assert audit["conflicts"] == [
        {
            "name": "conflict",
            "legacy_only": [],
            "target_only": [],
            "content_differs": ["SKILL.md"],
        }
    ]
    assert not (audit_dir / "conflict").exists()


def test_one_conflict_skips_only_that_skill(tmp_path: Path) -> None:
    legacy = tmp_path / ".codex" / "skills"
    target = tmp_path / ".agents" / "skills"
    backups = tmp_path / "backups"
    _skill(legacy, "safe")
    _skill(legacy, "conflict", "legacy")
    _skill(target, "conflict", "target")

    result = migration.migrate_legacy_codex_skills(
        legacy_dir=legacy,
        target_dir=target,
        backup_root=backups,
    )

    assert result.migrated == ("safe",)
    assert result.conflicts == ("conflict",)
    assert not (legacy / "safe").exists()
    assert (target / "safe" / "SKILL.md").exists()
    assert (legacy / "conflict" / "SKILL.md").read_text(encoding="utf-8") == "legacy"
    assert (target / "conflict" / "SKILL.md").read_text(encoding="utf-8") == "target"
    audit = json.loads(
        (next(backups.iterdir()) / "audit.json").read_text(encoding="utf-8")
    )
    assert audit["status"] == "partial"
    assert audit["actions"] == [{"action": "migrate", "name": "safe"}]
    assert [entry["name"] for entry in audit["conflicts"]] == ["conflict"]


def test_conflict_audit_lists_extra_files_on_each_side(tmp_path: Path) -> None:
    legacy = tmp_path / ".codex" / "skills"
    target = tmp_path / ".agents" / "skills"
    backups = tmp_path / "backups"
    _skill(legacy, "partial-diff")
    _skill(target, "partial-diff")
    (legacy / "partial-diff" / "references" / "notes.md").write_text(
        "notes\n", encoding="utf-8"
    )
    (target / "partial-diff" / "assets" / "extra.txt").write_text(
        "extra\n", encoding="utf-8"
    )

    result = migration.migrate_legacy_codex_skills(
        legacy_dir=legacy,
        target_dir=target,
        backup_root=backups,
    )

    assert result.conflicts == ("partial-diff",)
    audit = json.loads(
        (next(backups.iterdir()) / "audit.json").read_text(encoding="utf-8")
    )
    detail = audit["conflicts"][0]
    assert detail["legacy_only"] == ["references/notes.md"]
    assert detail["target_only"] == ["assets/extra.txt"]
    assert detail["content_differs"] == []


def test_conflict_dry_run_does_not_write_audit_or_move_skills(tmp_path: Path) -> None:
    legacy = tmp_path / ".codex" / "skills"
    target = tmp_path / ".agents" / "skills"
    backups = tmp_path / "backups"
    _skill(legacy, "conflict", "legacy")
    _skill(target, "conflict", "target")

    result = migration.migrate_legacy_codex_skills(
        legacy_dir=legacy,
        target_dir=target,
        backup_root=backups,
        dry_run=True,
    )

    assert result.conflicts == ("conflict",)
    assert (legacy / "conflict" / "SKILL.md").exists()
    assert (target / "conflict" / "SKILL.md").exists()
    assert not backups.exists()


def test_dry_run_reports_plan_without_writing(tmp_path: Path) -> None:
    legacy = tmp_path / ".codex" / "skills"
    target = tmp_path / ".agents" / "skills"
    backups = tmp_path / "backups"
    _skill(legacy, "demo")

    result = migration.migrate_legacy_codex_skills(
        legacy_dir=legacy,
        target_dir=target,
        backup_root=backups,
        dry_run=True,
    )

    assert result.changed is False
    assert result.migrated == ("demo",)
    assert (legacy / "demo").exists()
    assert not target.exists()
    assert not backups.exists()


def test_rerun_is_idempotent_and_hidden_system_skill_stays_legacy(
    tmp_path: Path,
) -> None:
    legacy = tmp_path / ".codex" / "skills"
    target = tmp_path / ".agents" / "skills"
    backups = tmp_path / "backups"
    _skill(legacy, "demo")
    _skill(legacy, ".system")

    first = migration.migrate_legacy_codex_skills(
        legacy_dir=legacy,
        target_dir=target,
        backup_root=backups,
    )
    second = migration.migrate_legacy_codex_skills(
        legacy_dir=legacy,
        target_dir=target,
        backup_root=backups,
    )

    assert first.migrated == ("demo",)
    assert first.skipped == (".system",)
    assert second.changed is False
    assert second.migrated == ()
    assert second.skipped == (".system",)
    assert (legacy / ".system" / "SKILL.md").exists()
    assert len(list(backups.iterdir())) == 1


def test_leaves_retired_auto_skill_for_confirmed_cleanup(
    tmp_path: Path,
) -> None:
    legacy = tmp_path / ".codex" / "skills"
    target = tmp_path / ".agents" / "skills"
    backups = tmp_path / "backups"
    state = tmp_path / ".config" / "ai-dev" / "projections" / "codex" / "auto-skill"
    _skill(state.parent, "auto-skill")
    legacy.mkdir(parents=True)
    legacy_link = legacy / "auto-skill"
    legacy_link.symlink_to("../../.config/ai-dev/projections/codex/auto-skill")

    result = migration.migrate_legacy_codex_skills(
        legacy_dir=legacy,
        target_dir=target,
        backup_root=backups,
    )

    assert result.migrated == ()
    assert result.skipped == ("auto-skill",)
    assert legacy_link.is_symlink()
    assert not (target / "auto-skill").exists()
    assert result.backup_dir is None


def test_migrates_broken_skill_symlink_without_following_it(tmp_path: Path) -> None:
    legacy = tmp_path / ".codex" / "skills"
    target = tmp_path / ".agents" / "skills"
    backups = tmp_path / "backups"
    legacy.mkdir(parents=True)
    (legacy / "broken-skill").symlink_to("../../missing/skill")

    result = migration.migrate_legacy_codex_skills(
        legacy_dir=legacy,
        target_dir=target,
        backup_root=backups,
    )

    migrated_link = target / "broken-skill"
    assert result.migrated == ("broken-skill",)
    assert migrated_link.is_symlink()
    assert os.readlink(migrated_link) == "../../missing/skill"
    assert result.backup_dir is not None
    assert (result.backup_dir / "broken-skill").is_symlink()


def test_failure_rolls_back_all_completed_actions(tmp_path: Path, monkeypatch) -> None:
    legacy = tmp_path / ".codex" / "skills"
    target = tmp_path / ".agents" / "skills"
    backups = tmp_path / "backups"
    _skill(legacy, "alpha")
    _skill(legacy, "beta")
    real_move = migration._move_entry

    def fail_on_beta(source: Path, destination: Path) -> None:
        if source.name == "beta":
            raise OSError("injected failure")
        real_move(source, destination)

    monkeypatch.setattr(migration, "_move_entry", fail_on_beta)

    with pytest.raises(RuntimeError, match="已回復"):
        migration.migrate_legacy_codex_skills(
            legacy_dir=legacy,
            target_dir=target,
            backup_root=backups,
        )

    assert (legacy / "alpha" / "SKILL.md").exists()
    assert (legacy / "beta" / "SKILL.md").exists()
    assert not (target / "alpha").exists()
    assert not (target / "beta").exists()
    backup_dir = next(backups.iterdir())
    audit = json.loads((backup_dir / "audit.json").read_text(encoding="utf-8"))
    assert audit["status"] == "rolled_back"


def test_partial_dedup_failure_restores_source_from_backup(
    tmp_path: Path, monkeypatch
) -> None:
    legacy = tmp_path / ".codex" / "skills"
    target = tmp_path / ".agents" / "skills"
    backups = tmp_path / "backups"
    _skill(legacy, "same", "same")
    _skill(target, "same", "same")
    original_remove = migration._remove_entry
    failed = False

    def partial_remove(path: Path) -> None:
        nonlocal failed
        if path == legacy / "same" and not failed:
            failed = True
            (path / "SKILL.md").unlink()
            raise OSError("simulated partial removal")
        original_remove(path)

    monkeypatch.setattr(migration, "_remove_entry", partial_remove)

    with pytest.raises(RuntimeError, match="已回復原狀"):
        migration.migrate_legacy_codex_skills(
            legacy_dir=legacy,
            target_dir=target,
            backup_root=backups,
        )

    assert (legacy / "same" / "SKILL.md").read_text(encoding="utf-8") == "same"
    assert (target / "same" / "SKILL.md").read_text(encoding="utf-8") == "same"
    audit_path = next(backups.iterdir()) / "audit.json"
    assert json.loads(audit_path.read_text(encoding="utf-8"))["status"] == "rolled_back"
