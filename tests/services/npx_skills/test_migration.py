from pathlib import Path

from script.services.npx_skills.config import SkillEntry
from script.services.npx_skills.migration import (
    LEGACY_PATH_BY_CANONICAL_ID,
    MigrationState,
    backup_and_remove_legacy_paths,
    classify_legacy_skill,
    manifest_names_for_detach,
    verify_npx_installations,
)
from script.utils.manifest import compute_dir_hash, compute_file_hash


def _write_skill(root: Path, name: str, body: str = "body\n") -> Path:
    skill = root / name
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: test skill\n---\n\n{body}",
        encoding="utf-8",
    )
    return skill


def test_classify_unchanged_legacy_copy(tmp_path: Path):
    skill = _write_skill(tmp_path, "alpha")
    manifest = {
        "files": {
            "skills": {
                "alpha": {
                    "hash": compute_dir_hash(skill),
                    "source": "custom-skills",
                }
            }
        }
    }

    record = classify_legacy_skill(
        target="claude",
        canonical_id="alpha",
        legacy_name="alpha",
        target_root=tmp_path,
        manifest=manifest,
        npx_lock={"skills": {}},
        expected_repo="ValorVie/ai-dev-skills",
    )

    assert record.state is MigrationState.UNCHANGED
    assert record.safe_to_install is True


def test_classify_modified_copy_reports_changed_files(tmp_path: Path):
    skill = _write_skill(tmp_path, "alpha")
    base_file_hash = compute_file_hash(skill / "SKILL.md")
    base_dir_hash = compute_dir_hash(skill)
    (skill / "SKILL.md").write_text("local edit\n", encoding="utf-8")
    manifest = {
        "files": {
            "skills": {
                "alpha": {
                    "hash": base_dir_hash,
                    "source": "custom-skills",
                    "files": {
                        "SKILL.md": {"dst_hash_at_sync": base_file_hash},
                    },
                }
            }
        }
    }

    record = classify_legacy_skill(
        target="claude",
        canonical_id="alpha",
        legacy_name="alpha",
        target_root=tmp_path,
        manifest=manifest,
        npx_lock={"skills": {}},
        expected_repo="ValorVie/ai-dev-skills",
    )

    assert record.state is MigrationState.MODIFIED
    assert record.changed_files == ("SKILL.md",)
    assert record.safe_to_install is False


def test_classify_unknown_ownership_stops(tmp_path: Path):
    _write_skill(tmp_path, "alpha")

    record = classify_legacy_skill(
        target="claude",
        canonical_id="alpha",
        legacy_name="alpha",
        target_root=tmp_path,
        manifest={"files": {"skills": {}}},
        npx_lock={"skills": {}},
        expected_repo="ValorVie/ai-dev-skills",
    )

    assert record.state is MigrationState.UNKNOWN
    assert record.safe_to_install is False


def test_classify_missing_copy_is_safe(tmp_path: Path):
    record = classify_legacy_skill(
        target="claude",
        canonical_id="alpha",
        legacy_name="alpha",
        target_root=tmp_path,
        manifest={"files": {"skills": {}}},
        npx_lock={"skills": {}},
        expected_repo="ValorVie/ai-dev-skills",
    )

    assert record.state is MigrationState.MISSING
    assert record.safe_to_install is True


def test_classify_existing_npx_install_is_idempotent(tmp_path: Path):
    _write_skill(tmp_path, "alpha")
    lock = {"skills": {"alpha": {"source": "ValorVie/ai-dev-skills"}}}

    record = classify_legacy_skill(
        target="codex",
        canonical_id="alpha",
        legacy_name="alpha",
        target_root=tmp_path,
        manifest={"files": {"skills": {}}},
        npx_lock=lock,
        expected_repo="ValorVie/ai-dev-skills",
    )

    assert record.state is MigrationState.ALREADY_MIGRATED
    assert record.safe_to_install is True


def test_verify_npx_installations_checks_lock_name_and_agent_paths(tmp_path: Path):
    canonical_root = tmp_path / "canonical"
    claude_root = tmp_path / "claude"
    _write_skill(canonical_root, "alpha")
    _write_skill(claude_root, "alpha")
    lock = tmp_path / "lock.json"
    lock.write_text(
        '{"version":3,"skills":{"alpha":{"source":"owner/repo"}}}',
        encoding="utf-8",
    )
    entries = (SkillEntry(repo="owner/repo", skill="alpha", source="first-party"),)

    result = verify_npx_installations(
        entries,
        canonical_root=canonical_root,
        lock_path=lock,
        agent_roots=(claude_root,),
    )

    assert result.verified_names == ("alpha",)
    assert result.failures == ()


def test_verify_npx_installations_reports_wrong_source_and_missing_path(tmp_path: Path):
    canonical_root = tmp_path / "canonical"
    lock = tmp_path / "lock.json"
    lock.write_text(
        '{"version":3,"skills":{"alpha":{"source":"other/repo"}}}',
        encoding="utf-8",
    )
    entries = (SkillEntry(repo="owner/repo", skill="alpha", source="first-party"),)

    result = verify_npx_installations(
        entries,
        canonical_root=canonical_root,
        lock_path=lock,
        agent_roots=(),
    )

    assert result.verified_names == ()
    assert any("canonical path" in failure for failure in result.failures)
    assert any("lock source" in failure for failure in result.failures)


def test_manifest_names_include_one_time_legacy_mapping():
    assert LEGACY_PATH_BY_CANONICAL_ID == {"simplify": "custom-simplify"}
    assert manifest_names_for_detach(["simplify", "wiki"]) == {
        "simplify",
        "custom-simplify",
        "wiki",
    }


def test_backup_and_remove_legacy_path_only_after_verification(tmp_path: Path):
    old_path = _write_skill(tmp_path, "custom-simplify")
    record = classify_legacy_skill(
        target="codex",
        canonical_id="simplify",
        legacy_name="custom-simplify",
        target_root=tmp_path,
        manifest={
            "files": {
                "skills": {
                    "custom-simplify": {
                        "hash": compute_dir_hash(old_path),
                        "source": "custom-skills",
                    }
                }
            }
        },
        npx_lock={"skills": {}},
        expected_repo="ValorVie/ai-dev-skills",
    )
    backups: list[tuple[str, str, str]] = []

    failures = backup_and_remove_legacy_paths(
        (record,),
        verified_names=("simplify",),
        backup_func=lambda target, resource_type, name: backups.append(
            (target, resource_type, name)
        )
        or tmp_path / "backup",
    )

    assert failures == ()
    assert backups == [("codex", "skills", "custom-simplify")]
    assert not old_path.exists()


def test_backup_and_remove_legacy_path_keeps_unverified_copy(tmp_path: Path):
    old_path = _write_skill(tmp_path, "custom-simplify")
    record = classify_legacy_skill(
        target="codex",
        canonical_id="simplify",
        legacy_name="custom-simplify",
        target_root=tmp_path,
        manifest={
            "files": {
                "skills": {
                    "custom-simplify": {
                        "hash": "sha256:not-current",
                        "source": "custom-skills",
                    }
                }
            }
        },
        npx_lock={"skills": {}},
        expected_repo="ValorVie/ai-dev-skills",
    )

    failures = backup_and_remove_legacy_paths(
        (record,),
        verified_names=("simplify",),
        backup_func=lambda *_args: tmp_path / "backup",
    )

    assert failures == ()
    assert old_path.exists()
