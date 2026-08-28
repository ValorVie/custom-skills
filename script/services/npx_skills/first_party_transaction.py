from __future__ import annotations

import os
import shutil
from collections.abc import Mapping
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from script.services.npx_skills.first_party_overlay import (
    FirstPartyStateStore,
    TransactionJournal,
    TransactionJournalStore,
    TransactionStatus,
    skill_state_hash,
)


def _remove_path(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)


class SkillTransaction:
    """Backup and restore one skill's installed roots and ai-dev state."""

    def __init__(
        self,
        skill: str,
        *,
        roots: Mapping[str, Path],
        state_store: FirstPartyStateStore,
        journal_store: TransactionJournalStore,
        backup_root: Path,
    ):
        self.skill = skill
        self.roots = dict(roots)
        self.state_store = state_store
        self.journal_store = journal_store
        self.backup_root = backup_root
        self.journal: TransactionJournal | None = None

    def _journal(self) -> TransactionJournal:
        journal = self.journal or self.journal_store.read(self.skill)
        if journal is None:
            raise RuntimeError(f"transaction not started: {self.skill}")
        self.journal = journal
        return journal

    def begin(self) -> TransactionJournal:
        existing = self.journal_store.read(self.skill)
        if existing is not None:
            raise RuntimeError(f"unfinished transaction exists: {self.skill}")
        self.backup_root.mkdir(parents=True, exist_ok=True)
        os.chmod(self.backup_root, 0o700)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        relative_backup = f"{timestamp}-{self.skill}"
        backup_dir = self.backup_root / relative_backup
        backup_dir.mkdir(mode=0o700)
        root_backups = {
            label: f"roots/{index:03d}" for index, label in enumerate(self.roots)
        }
        journal = TransactionJournal(
            skill=self.skill,
            status=TransactionStatus.PLANNED,
            backup_dir=relative_backup,
            roots=root_backups,
            started_at=datetime.now(timezone.utc).isoformat(),
        )
        self.journal_store.write(journal)
        self.journal = journal
        try:
            for label, target in self.roots.items():
                backup = backup_dir / root_backups[label]
                backup.parent.mkdir(parents=True, exist_ok=True)
                if target.is_dir() and not target.is_symlink():
                    shutil.copytree(target, backup, symlinks=True)
                elif target.exists() or target.is_symlink():
                    raise ValueError(f"unsupported installed root: {target}")
                else:
                    backup.with_suffix(".missing").touch(mode=0o600)
            self._backup_state(backup_dir)
            return self.mark(TransactionStatus.BACKED_UP)
        except Exception:
            self.journal_store.path_for(self.skill).unlink(missing_ok=True)
            raise

    def _backup_state(self, backup_dir: Path) -> None:
        manifest_backup = backup_dir / "manifest.yaml"
        if self.state_store.manifest_path.is_file():
            shutil.copy2(self.state_store.manifest_path, manifest_backup)
        elif self.state_store.manifest_path.exists():
            raise ValueError("unsupported first-party manifest type")
        else:
            (backup_dir / "manifest.missing").touch(mode=0o600)

        active_overlay = self.state_store.overlay_root / self.skill
        overlay_backup = backup_dir / "overlay"
        if active_overlay.is_dir() and not active_overlay.is_symlink():
            shutil.copytree(active_overlay, overlay_backup, symlinks=True)
        elif active_overlay.exists() or active_overlay.is_symlink():
            raise ValueError("unsupported active overlay type")
        else:
            (backup_dir / "overlay.missing").touch(mode=0o600)

    def mark(self, status: TransactionStatus) -> TransactionJournal:
        self.journal = self.journal_store.update(self._journal(), status)
        return self.journal

    def expect_state(
        self, expected_state_hash: str, *, retain_backup: bool
    ) -> TransactionJournal:
        journal = self._journal()
        if journal.status is not TransactionStatus.VERIFIED:
            raise RuntimeError(f"transaction not verified: {self.skill}")
        self.journal = replace(
            journal,
            expected_state_hash=expected_state_hash,
            retain_backup=retain_backup,
        )
        self.journal_store.write(self.journal)
        return self.journal

    def _restore_roots(self, journal: TransactionJournal) -> None:
        backup_dir = self.backup_root / journal.backup_dir
        for label, relative in journal.roots.items():
            if label not in self.roots:
                raise RuntimeError(f"rollback root unavailable: {label}")
            target = self.roots[label]
            backup = backup_dir / relative
            missing = backup.with_suffix(".missing")
            _remove_path(target)
            if backup.is_dir():
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copytree(backup, target, symlinks=True)
            elif not missing.is_file():
                raise RuntimeError(f"rollback evidence missing: {label}")

    def _restore_state(self, journal: TransactionJournal) -> None:
        backup_dir = self.backup_root / journal.backup_dir
        manifest_backup = backup_dir / "manifest.yaml"
        _remove_path(self.state_store.manifest_path)
        if manifest_backup.is_file():
            self.state_store.manifest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(manifest_backup, self.state_store.manifest_path)
        elif not (backup_dir / "manifest.missing").is_file():
            raise RuntimeError("manifest rollback evidence missing")

        active_overlay = self.state_store.overlay_root / self.skill
        overlay_backup = backup_dir / "overlay"
        _remove_path(active_overlay)
        if overlay_backup.is_dir():
            active_overlay.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(overlay_backup, active_overlay, symlinks=True)
        elif not (backup_dir / "overlay.missing").is_file():
            raise RuntimeError("overlay rollback evidence missing")

    def rollback(self) -> None:
        journal = self._journal()
        try:
            if journal.status is not TransactionStatus.PLANNED:
                self._restore_roots(journal)
                self._restore_state(journal)
        except Exception as exc:
            raise RuntimeError(
                f"rollback failed; evidence retained: "
                f"{self.backup_root / journal.backup_dir}"
            ) from exc
        self.journal_store.path_for(self.skill).unlink(missing_ok=True)
        self.journal = None

    def recover_if_needed(self) -> bool:
        journal = self.journal_store.read(self.skill)
        if journal is None:
            return False
        self.journal = journal
        if journal.status is TransactionStatus.COMMITTED:
            if journal.expected_state_hash is not None:
                self.finish_commit(retain_backup=journal.retain_backup)
            else:
                self.journal_store.path_for(self.skill).unlink(missing_ok=True)
                self.journal = None
            return False
        if (
            journal.status is TransactionStatus.VERIFIED
            and journal.expected_state_hash is not None
        ):
            state = self.state_store.read().skills.get(self.skill)
            if (
                state is not None
                and skill_state_hash(state) == journal.expected_state_hash
            ):
                self.prepare_commit()
                self.finish_commit(retain_backup=journal.retain_backup)
                return False
        self.rollback()
        return True

    def prepare_commit(self) -> TransactionJournal:
        return self.mark(TransactionStatus.COMMITTED)

    def finish_commit(self, *, retain_backup: bool) -> None:
        journal = self._journal()
        if journal.status is not TransactionStatus.COMMITTED:
            raise RuntimeError(f"transaction not committed: {self.skill}")
        backup_dir = self.backup_root / journal.backup_dir
        if not retain_backup and backup_dir.exists():
            shutil.rmtree(backup_dir)
        self.journal_store.path_for(self.skill).unlink(missing_ok=True)
        self.journal = None

    def commit(self, *, retain_backup: bool) -> None:
        self.prepare_commit()
        self.finish_commit(retain_backup=retain_backup)
