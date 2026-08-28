from pathlib import Path

from script.services.npx_skills.config import SkillEntry
from script.services.npx_skills.first_party_reconcile import (
    GuardAction,
    get_first_party_local_roots,
    plan_first_party_reconcile,
    read_guard_entries,
    record_guard_success,
    verify_first_party_paths,
)
from script.services.npx_skills.migration import VerificationResult
from script.services.npx_skills.migration import MigrationRecord, MigrationState
from script.utils.manifest import FileEntry, compute_dir_hash

ENTRY = SkillEntry(
    repo="ValorVie/ai-dev-skills",
    skill="example-skill",
    source="ai-dev-first-party",
)


def _skill(root: Path, content: str) -> Path:
    path = root / ENTRY.skill
    path.mkdir(parents=True)
    (path / "SKILL.md").write_text(
        f"---\nname: {ENTRY.skill}\n---\n\n{content}\n",
        encoding="utf-8",
    )
    return path


def _guard_entry(path: Path) -> FileEntry:
    value = compute_dir_hash(path)
    return FileEntry(
        src_hash=value,
        src_commit="base-commit",
        src_source=ENTRY.repo,
        dst_hash_at_sync=value,
        decision="accepted",
        decided_at="2026-08-28T00:00:00+00:00",
    )


def _plan(
    tmp_path: Path,
    *,
    source_content: str,
    local_content: str | None,
    guard_entry: FileEntry | None = None,
    lock_source: str | None = None,
):
    source_root = tmp_path / "source"
    _skill(source_root, source_content)
    local_root = tmp_path / "local"
    if local_content is not None:
        _skill(local_root, local_content)
    guard_path = tmp_path / "npx-first-party.yaml"
    if guard_entry is not None:
        record_guard_success(
            guard_path,
            [(ENTRY, guard_entry.src_hash, guard_entry.src_commit)],
        )
    lock = {"skills": {}}
    if lock_source is not None or guard_entry is not None:
        lock["skills"][ENTRY.skill] = {"source": lock_source}
        if lock_source is None:
            lock["skills"][ENTRY.skill]["source"] = ENTRY.repo
    return plan_first_party_reconcile(
        (ENTRY,),
        source_skills_root=source_root,
        source_commit="source-commit",
        guard_path=guard_path,
        local_roots={"canonical": local_root},
        npx_lock=lock,
    )


def test_fresh_install_is_safe_apply(tmp_path: Path):
    plan = _plan(tmp_path, source_content="new", local_content=None)

    assert plan.records[0].classification == "no-base"
    assert plan.records[0].action is GuardAction.APPLY


def test_clean_unchanged_is_noop(tmp_path: Path):
    base_root = tmp_path / "base"
    base = _skill(base_root, "same")
    plan = _plan(
        tmp_path,
        source_content="same",
        local_content="same",
        guard_entry=_guard_entry(base),
    )

    assert plan.records[0].classification == "clean"
    assert plan.records[0].action is GuardAction.NOOP


def test_source_only_change_is_safe_apply(tmp_path: Path):
    base_root = tmp_path / "base"
    base = _skill(base_root, "old")
    plan = _plan(
        tmp_path,
        source_content="new",
        local_content="old",
        guard_entry=_guard_entry(base),
    )

    assert plan.records[0].classification == "clean"
    assert plan.records[0].action is GuardAction.APPLY


def test_local_only_change_is_blocked(tmp_path: Path):
    base_root = tmp_path / "base"
    base = _skill(base_root, "old")
    plan = _plan(
        tmp_path,
        source_content="old",
        local_content="custom",
        guard_entry=_guard_entry(base),
    )

    assert plan.records[0].classification == "local-only"
    assert plan.records[0].action is GuardAction.BLOCK


def test_both_changed_is_blocked(tmp_path: Path):
    base_root = tmp_path / "base"
    base = _skill(base_root, "old")
    plan = _plan(
        tmp_path,
        source_content="new",
        local_content="custom",
        guard_entry=_guard_entry(base),
    )

    assert plan.records[0].classification == "both-changed"
    assert plan.records[0].action is GuardAction.BLOCK


def test_existing_content_without_base_is_blocked(tmp_path: Path):
    plan = _plan(tmp_path, source_content="new", local_content="unknown")

    assert plan.records[0].classification == "no-base"
    assert plan.records[0].action is GuardAction.BLOCK


def test_existing_matching_npx_install_bootstraps_guard(tmp_path: Path):
    plan = _plan(
        tmp_path,
        source_content="same",
        local_content="same",
        lock_source=ENTRY.repo,
    )

    assert plan.records[0].classification == "no-base"
    assert plan.records[0].action is GuardAction.BOOTSTRAP


def test_guarded_skill_with_wrong_lock_source_is_no_base(tmp_path: Path):
    base_root = tmp_path / "base"
    base = _skill(base_root, "same")
    plan = _plan(
        tmp_path,
        source_content="same",
        local_content="same",
        guard_entry=_guard_entry(base),
        lock_source="other/repo",
    )

    assert plan.records[0].classification == "no-base"
    assert plan.records[0].action is GuardAction.BLOCK


def test_agent_roots_map_four_universal_agents_to_canonical(tmp_path: Path):
    roots = get_first_party_local_roots(
        ("claude-code", "codex", "gemini-cli", "opencode", "antigravity"),
        home=tmp_path,
    )

    canonical = tmp_path / ".agents" / "skills"
    assert roots["claude-code"] == tmp_path / ".claude" / "skills"
    assert roots["codex"] == canonical
    assert roots["gemini-cli"] == canonical
    assert roots["opencode"] == canonical
    assert roots["antigravity"] == canonical


def test_already_migrated_legacy_copy_is_not_an_active_guard_path(tmp_path: Path):
    source_root = tmp_path / "source"
    _skill(source_root, "same")
    canonical_root = tmp_path / "canonical"
    _skill(canonical_root, "same")
    stale = tmp_path / "legacy" / ENTRY.skill
    stale.mkdir(parents=True)
    (stale / "SKILL.md").write_text("stale legacy copy\n", encoding="utf-8")
    record = MigrationRecord(
        target="opencode",
        canonical_id=ENTRY.skill,
        legacy_name=ENTRY.skill,
        path=stale,
        state=MigrationState.ALREADY_MIGRATED,
    )

    plan = plan_first_party_reconcile(
        (ENTRY,),
        source_skills_root=source_root,
        source_commit="source-commit",
        guard_path=tmp_path / "guard.yaml",
        local_roots={"canonical": canonical_root},
        npx_lock={"skills": {ENTRY.skill: {"source": ENTRY.repo}}},
        legacy_records=(record,),
    )

    assert plan.records[0].classification == "no-base"
    assert plan.records[0].action is GuardAction.BOOTSTRAP


def test_unchanged_legacy_copy_can_migrate_when_new_roots_are_missing(tmp_path: Path):
    base_root = tmp_path / "legacy"
    legacy_path = _skill(base_root, "old")
    source_root = tmp_path / "source"
    _skill(source_root, "new")
    base_hash = compute_dir_hash(legacy_path)
    record = MigrationRecord(
        target="opencode",
        canonical_id=ENTRY.skill,
        legacy_name=ENTRY.skill,
        path=legacy_path,
        state=MigrationState.UNCHANGED,
        expected_hash=base_hash,
        actual_hash=base_hash,
    )

    plan = plan_first_party_reconcile(
        (ENTRY,),
        source_skills_root=source_root,
        source_commit="source-commit",
        guard_path=tmp_path / "guard.yaml",
        local_roots={"canonical": tmp_path / "missing-canonical"},
        npx_lock={"skills": {}},
        legacy_records=(record,),
    )

    assert plan.records[0].classification == "clean"
    assert plan.records[0].action is GuardAction.APPLY


def test_one_diverged_agent_path_blocks_skill(tmp_path: Path):
    source_root = tmp_path / "source"
    source = _skill(source_root, "same")
    canonical_root = tmp_path / "canonical"
    _skill(canonical_root, "same")
    claude_root = tmp_path / "claude"
    _skill(claude_root, "custom")
    guard_path = tmp_path / "npx-first-party.yaml"
    record_guard_success(
        guard_path,
        [(ENTRY, compute_dir_hash(source), "base-commit")],
    )

    plan = plan_first_party_reconcile(
        (ENTRY,),
        source_skills_root=source_root,
        source_commit="source-commit",
        guard_path=guard_path,
        local_roots={"canonical": canonical_root, "claude-code": claude_root},
        npx_lock={"skills": {ENTRY.skill: {"source": ENTRY.repo}}},
    )

    assert plan.records[0].classification == "local-only"
    assert plan.records[0].action is GuardAction.BLOCK


def test_record_guard_success_preserves_other_entries(tmp_path: Path):
    guard_path = tmp_path / "npx-first-party.yaml"
    other = SkillEntry(repo=ENTRY.repo, skill="other", source=ENTRY.source)
    record_guard_success(guard_path, [(other, "sha256:other", "commit-1")])
    record_guard_success(guard_path, [(ENTRY, "sha256:example", "commit-2")])

    entries = read_guard_entries(guard_path)

    assert set(entries) == {"other", ENTRY.skill}
    assert entries[ENTRY.skill].src_hash == "sha256:example"
    assert entries[ENTRY.skill].dst_hash_at_sync == "sha256:example"


def test_verify_first_party_paths_rejects_hash_mismatch(tmp_path: Path):
    source_root = tmp_path / "source"
    _skill(source_root, "upstream")
    canonical_root = tmp_path / "canonical"
    _skill(canonical_root, "upstream")
    claude_root = tmp_path / "claude"
    _skill(claude_root, "custom")
    lock_path = tmp_path / ".skill-lock.json"
    lock_path.write_text(
        '{"skills":{"example-skill":{"source":"ValorVie/ai-dev-skills"}}}',
        encoding="utf-8",
    )

    result = verify_first_party_paths(
        (ENTRY,),
        source_skills_root=source_root,
        local_roots={"canonical": canonical_root, "claude-code": claude_root},
        lock_path=lock_path,
    )

    assert isinstance(result, VerificationResult)
    assert result.verified_names == ()
    assert any("claude-code hash mismatch" in item for item in result.failures)
