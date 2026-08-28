from pathlib import Path

import pytest

from script.services.npx_skills.first_party_overlay import (
    FirstPartyStateStore,
    TransactionJournalStore,
    TransactionStatus,
)
from script.services.npx_skills.first_party_transaction import SkillTransaction


def _transaction(tmp_path: Path) -> tuple[SkillTransaction, Path, Path]:
    installed = tmp_path / "home" / ".agents" / "skills" / "demo"
    installed.mkdir(parents=True)
    (installed / "SKILL.md").write_text("old\n", encoding="utf-8")
    manifest = tmp_path / "config" / "manifests" / "npx-first-party.yaml"
    overlay = tmp_path / "config" / "overlays" / "npx-first-party"
    state_store = FirstPartyStateStore(manifest, overlay)
    manifest.parent.mkdir(parents=True)
    manifest.write_text("old-state\n", encoding="utf-8")
    old_overlay = overlay / "demo" / "SKILL.md"
    old_overlay.parent.mkdir(parents=True)
    old_overlay.write_text("old-overlay\n", encoding="utf-8")
    transaction = SkillTransaction(
        "demo",
        roots={"canonical": installed},
        state_store=state_store,
        journal_store=TransactionJournalStore(tmp_path / "config" / "transactions"),
        backup_root=tmp_path / "config" / "backups",
    )
    return transaction, installed, old_overlay


def test_transaction_rollback_restores_roots_manifest_and_overlay(tmp_path: Path):
    transaction, installed, old_overlay = _transaction(tmp_path)
    journal = transaction.begin()

    (installed / "SKILL.md").write_text("new\n", encoding="utf-8")
    transaction.state_store.manifest_path.write_text("new-state\n", encoding="utf-8")
    old_overlay.write_text("new-overlay\n", encoding="utf-8")
    transaction.mark(TransactionStatus.BASE_APPLIED)
    transaction.rollback()

    assert (installed / "SKILL.md").read_text(encoding="utf-8") == "old\n"
    assert transaction.state_store.manifest_path.read_text(encoding="utf-8") == (
        "old-state\n"
    )
    assert old_overlay.read_text(encoding="utf-8") == "old-overlay\n"
    assert transaction.journal_store.read("demo") is None
    assert (transaction.backup_root / journal.backup_dir).exists()


def test_transaction_rollback_removes_roots_created_after_backup(tmp_path: Path):
    state_store = FirstPartyStateStore(
        tmp_path / "manifest.yaml", tmp_path / "overlays"
    )
    installed = tmp_path / "installed" / "demo"
    transaction = SkillTransaction(
        "demo",
        roots={"canonical": installed},
        state_store=state_store,
        journal_store=TransactionJournalStore(tmp_path / "transactions"),
        backup_root=tmp_path / "backups",
    )
    transaction.begin()
    installed.mkdir(parents=True)
    (installed / "SKILL.md").write_text("created", encoding="utf-8")

    transaction.rollback()

    assert not installed.exists()
    assert not state_store.manifest_path.exists()


def test_interrupted_transaction_recovers_before_new_begin(tmp_path: Path):
    transaction, installed, _old_overlay = _transaction(tmp_path)
    transaction.begin()
    (installed / "SKILL.md").write_text("partial\n", encoding="utf-8")
    transaction.mark(TransactionStatus.BASE_APPLIED)

    assert transaction.recover_if_needed()
    assert (installed / "SKILL.md").read_text(encoding="utf-8") == "old\n"
    assert transaction.journal_store.read("demo") is None


def test_committed_transaction_can_retain_user_backup(tmp_path: Path):
    transaction, _installed, _old_overlay = _transaction(tmp_path)
    journal = transaction.begin()

    transaction.commit(retain_backup=True)

    assert transaction.journal_store.read("demo") is None
    assert (transaction.backup_root / journal.backup_dir).is_dir()


def test_rollback_failure_keeps_journal_and_evidence(tmp_path: Path, monkeypatch):
    transaction, _installed, _old_overlay = _transaction(tmp_path)
    transaction.begin()
    monkeypatch.setattr(transaction, "_restore_roots", lambda _journal: 1 / 0)

    with pytest.raises(RuntimeError, match="rollback failed"):
        transaction.rollback()

    assert transaction.journal_store.read("demo") is not None
