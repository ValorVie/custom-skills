from pathlib import Path

import pytest

from script.services.npx_skills.first_party_overlay import (
    MISSING_HASH,
    FilePlan,
    FileState,
    FirstPartyState,
    FirstPartyStateStore,
    OverlayEntry,
    SkillState,
    TransactionJournal,
    TransactionJournalStore,
    TransactionStatus,
    TreeFile,
    expand_v1_skill,
    plan_file,
    plan_skill,
    snapshot_tree,
)
from script.utils.manifest import FileEntry, compute_dir_hash, compute_file_hash


def test_schema_v2_round_trip_preserves_file_and_deleted_overlays(tmp_path: Path):
    store = FirstPartyStateStore(
        tmp_path / "npx-first-party.yaml",
        tmp_path / "overlays",
    )
    state = FirstPartyState(
        skills={
            "demo": SkillState(
                source="ValorVie/ai-dev-skills",
                source_commit="commit-2",
                files={
                    "SKILL.md": FileState(
                        src_hash="sha256:source",
                        src_commit="commit-2",
                        src_source="ValorVie/ai-dev-skills",
                        dst_hash_at_sync="sha256:local",
                        decision="keep-local",
                        decided_at="2026-08-28T00:00:00+00:00",
                        overlay=OverlayEntry(
                            kind="file",
                            hash="sha256:local",
                            path="demo/SKILL.md",
                        ),
                    ),
                    "removed.md": FileState(
                        src_hash="sha256:source-removed",
                        src_commit="commit-2",
                        src_source="ValorVie/ai-dev-skills",
                        dst_hash_at_sync=MISSING_HASH,
                        decision="keep-local",
                        decided_at="2026-08-28T00:00:00+00:00",
                        overlay=OverlayEntry(
                            kind="deleted",
                            hash=MISSING_HASH,
                            path=None,
                        ),
                    ),
                },
            )
        }
    )

    store.write(state)
    loaded = store.read()

    assert loaded == state
    assert store.manifest_path.stat().st_mode & 0o777 == 0o600


def test_overlay_store_writes_bytes_and_deletion_tombstone(tmp_path: Path):
    store = FirstPartyStateStore(
        tmp_path / "npx-first-party.yaml",
        tmp_path / "overlays",
    )

    file_overlay = store.write_overlay("demo", "refs/example.md", b"local\n")
    deleted_overlay = store.write_overlay("demo", "removed.md", None)

    assert file_overlay.kind == "file"
    assert file_overlay.path == "demo/refs/example.md"
    assert store.read_overlay(file_overlay) == b"local\n"
    assert deleted_overlay == OverlayEntry(kind="deleted", hash=MISSING_HASH, path=None)
    assert store.overlay_root.stat().st_mode & 0o777 == 0o700
    overlay_path = store.overlay_root / file_overlay.path
    assert overlay_path.stat().st_mode & 0o777 == 0o600


def test_invalid_or_traversing_overlay_state_fails_closed(tmp_path: Path):
    manifest = tmp_path / "npx-first-party.yaml"
    manifest.write_text(
        """schema_version: 2
managed_by: ai-dev-first-party-reconcile
skills:
  demo:
    source: ValorVie/ai-dev-skills
    source_commit: c
    files:
      SKILL.md:
        src_hash: s
        src_commit: c
        src_source: ValorVie/ai-dev-skills
        dst_hash_at_sync: d
        decision: keep-local
        decided_at: now
        overlay:
          kind: file
          hash: h
          path: ../outside
""",
        encoding="utf-8",
    )
    store = FirstPartyStateStore(manifest, tmp_path / "overlays")

    with pytest.raises(ValueError, match="overlay path"):
        store.read()


def test_corrupt_state_and_overlay_hash_mismatch_fail_closed(tmp_path: Path):
    manifest = tmp_path / "npx-first-party.yaml"
    manifest.write_text("skills: [", encoding="utf-8")
    store = FirstPartyStateStore(manifest, tmp_path / "overlays")

    with pytest.raises(ValueError, match="state unreadable"):
        store.read()

    entry = store.write_overlay("demo", "SKILL.md", b"local")
    assert entry.path is not None
    (store.overlay_root / entry.path).write_bytes(b"tampered")
    with pytest.raises(ValueError, match="overlay hash mismatch"):
        store.read_overlay(entry)


def test_overlay_store_rejects_symlink_escape(tmp_path: Path):
    store = FirstPartyStateStore(
        tmp_path / "npx-first-party.yaml", tmp_path / "overlays"
    )
    outside = tmp_path / "outside"
    outside.mkdir()
    store.overlay_root.mkdir()
    (store.overlay_root / "demo").symlink_to(outside, target_is_directory=True)
    entry = OverlayEntry(
        kind="file",
        hash="sha256:unused",
        path="demo/SKILL.md",
    )

    with pytest.raises(ValueError, match="overlay symlink"):
        store.write_overlay("demo", "SKILL.md", b"local")
    with pytest.raises(ValueError, match="overlay symlink"):
        store.read_overlay(entry)
    assert not (outside / "SKILL.md").exists()


def test_expand_v1_clean_guard_uses_base_commit_file_map(tmp_path: Path):
    base = tmp_path / "base"
    base.mkdir()
    (base / "SKILL.md").write_text("base\n", encoding="utf-8")
    (base / "refs").mkdir()
    (base / "refs" / "note.md").write_text("note\n", encoding="utf-8")
    legacy = FileEntry(
        src_hash=compute_dir_hash(base),
        src_commit="base-commit",
        src_source="ValorVie/ai-dev-skills",
        dst_hash_at_sync=compute_dir_hash(base),
        decision="accepted",
        decided_at="before",
    )

    expanded = expand_v1_skill("demo", legacy, base)

    assert expanded.source_commit == "base-commit"
    assert set(expanded.files) == {"SKILL.md", "refs/note.md"}
    assert expanded.files["SKILL.md"].src_hash == compute_file_hash(base / "SKILL.md")
    assert expanded.files["SKILL.md"].dst_hash_at_sync == compute_file_hash(
        base / "SKILL.md"
    )
    assert expanded.files["SKILL.md"].overlay is None


def test_expand_v1_requires_available_matching_base_tree(tmp_path: Path):
    legacy = FileEntry(
        src_hash="sha256:expected",
        src_commit="base-commit",
        src_source="ValorVie/ai-dev-skills",
        dst_hash_at_sync="sha256:expected",
        decision="accepted",
        decided_at="before",
    )

    with pytest.raises(ValueError, match="base commit unavailable"):
        expand_v1_skill("demo", legacy, None)

    wrong = tmp_path / "wrong"
    wrong.mkdir()
    (wrong / "SKILL.md").write_text("wrong", encoding="utf-8")
    with pytest.raises(ValueError, match="base hash mismatch"):
        expand_v1_skill("demo", legacy, wrong)


def test_expand_v1_uses_base_even_when_installed_tree_has_drifted(tmp_path: Path):
    base = tmp_path / "base"
    local = tmp_path / "local"
    base.mkdir()
    local.mkdir()
    (base / "SKILL.md").write_text("base\n", encoding="utf-8")
    (local / "SKILL.md").write_text("local\n", encoding="utf-8")
    legacy = FileEntry(
        src_hash=compute_dir_hash(base),
        src_commit="base-commit",
        src_source="ValorVie/ai-dev-skills",
        dst_hash_at_sync=compute_dir_hash(base),
        decision="accepted",
        decided_at="before",
    )

    expanded = expand_v1_skill("demo", legacy, base)

    assert expanded.files["SKILL.md"].src_hash == compute_file_hash(base / "SKILL.md")
    assert compute_file_hash(local / "SKILL.md") != expanded.files["SKILL.md"].src_hash


def test_transaction_journal_round_trip_and_status_update(tmp_path: Path):
    store = TransactionJournalStore(tmp_path / "transactions")
    journal = TransactionJournal(
        skill="demo",
        status=TransactionStatus.PLANNED,
        backup_dir="20260828/demo",
        roots={"canonical": "roots/canonical"},
        started_at="2026-08-28T00:00:00+00:00",
    )

    store.write(journal)
    updated = store.update(journal, TransactionStatus.BACKED_UP)

    assert store.read("demo") == updated
    assert updated.status is TransactionStatus.BACKED_UP
    assert store.root.stat().st_mode & 0o777 == 0o700
    assert store.path_for("demo").stat().st_mode & 0o777 == 0o600


def test_transaction_journal_rejects_traversal_and_invalid_status(tmp_path: Path):
    store = TransactionJournalStore(tmp_path / "transactions")
    store.root.mkdir(parents=True)
    store.path_for("demo").write_text(
        """schema_version: 1
skill: demo
status: UNKNOWN
backup_dir: ../outside
roots: {}
started_at: now
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="transaction journal"):
        store.read("demo")


@pytest.mark.parametrize(
    ("base", "source", "local", "overlay", "classification", "effective"),
    (
        ("b", "b", "b", None, "clean", "b"),
        ("b", "s", "b", None, "clean", "s"),
        ("b", "s", "s", None, "clean", "s"),
        ("b", "b", "l", None, "local-only", "l"),
        ("b", "s", "l", None, "both-changed", "l"),
        (None, "s", "s", None, "clean", "s"),
        (None, "s", MISSING_HASH, None, "clean", "s"),
        (None, MISSING_HASH, "l", None, "local-only", "l"),
        (None, "s", "l", None, "no-base", "l"),
        ("b", MISSING_HASH, "b", None, "clean", MISSING_HASH),
        ("b", MISSING_HASH, "l", None, "both-changed", "l"),
        ("b", "b", MISSING_HASH, None, "local-only", MISSING_HASH),
    ),
)
def test_plan_file_classification_matrix(
    base: str | None,
    source: str,
    local: str,
    overlay: str | None,
    classification: str,
    effective: str,
):
    plan = plan_file(
        "SKILL.md",
        base_hash=base,
        source_hash=source,
        local_hash=local,
        overlay_hash=overlay,
    )

    assert plan.classification == classification
    assert plan.effective_hash == effective


def test_plan_file_keeps_persistent_overlay_after_raw_npx_overwrite():
    plan = plan_file(
        "SKILL.md",
        base_hash="base",
        source_hash="source",
        local_hash="source",
        overlay_hash="local-intent",
    )

    assert plan == FilePlan(
        path="SKILL.md",
        classification="both-changed",
        base_hash="base",
        source_hash="source",
        local_hash="source",
        overlay_hash="local-intent",
        effective_hash="local-intent",
    )


def test_plan_file_prefers_new_local_edit_over_existing_overlay():
    plan = plan_file(
        "SKILL.md",
        base_hash="base",
        source_hash="base",
        local_hash="new-local",
        overlay_hash="old-overlay",
    )

    assert plan.classification == "local-only"
    assert plan.effective_hash == "new-local"


def test_plan_file_rejects_unsafe_relative_path():
    with pytest.raises(ValueError, match="file path"):
        plan_file(
            "../outside",
            base_hash="base",
            source_hash="source",
            local_hash="local",
            overlay_hash=None,
        )


def test_plan_skill_uses_union_for_new_and_deleted_files():
    base = {
        "deleted.md": TreeFile.from_content(b"old"),
        "local-delete.md": TreeFile.from_content(b"keep"),
    }
    source = {
        "new.md": TreeFile.from_content(b"new"),
        "local-delete.md": TreeFile.from_content(b"keep"),
    }
    local = {
        "deleted.md": TreeFile.from_content(b"old"),
        "new-local.md": TreeFile.from_content(b"mine"),
    }

    conflicts = plan_skill(base=base, source=source, local=local, overlays={})
    by_path = {item.plan.path: item.plan for item in conflicts}

    assert by_path["deleted.md"].classification == "clean"
    assert by_path["deleted.md"].effective_hash == MISSING_HASH
    assert by_path["new.md"].classification == "clean"
    assert by_path["new-local.md"].classification == "local-only"
    assert by_path["local-delete.md"].classification == "local-only"
    assert by_path["local-delete.md"].effective_hash == MISSING_HASH


def test_snapshot_tree_supports_binary_and_rejects_symlink(tmp_path: Path):
    root = tmp_path / "skill"
    root.mkdir()
    (root / "binary.dat").write_bytes(b"\x00\xff")

    snapshot = snapshot_tree(root)

    assert snapshot["binary.dat"].content == b"\x00\xff"
    assert snapshot["binary.dat"].hash.startswith("sha256:")

    (root / "link").symlink_to(root / "binary.dat")
    with pytest.raises(ValueError, match="unsupported file type"):
        snapshot_tree(root)
