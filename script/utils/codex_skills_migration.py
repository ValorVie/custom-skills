"""將舊版 Codex user skills 安全遷移到共用 Agent Skills 目錄。"""

from __future__ import annotations

import errno
import hashlib
import json
import os
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from rich.console import Console

from .paths import get_agents_skills_dir, get_ai_dev_config_dir, get_codex_config_dir

console = Console()


@dataclass(frozen=True)
class CodexSkillsMigrationResult:
    migrated: tuple[str, ...] = ()
    deduplicated: tuple[str, ...] = ()
    conflicts: tuple[str, ...] = ()
    skipped: tuple[str, ...] = ()
    backup_dir: Path | None = None
    dry_run: bool = False

    @property
    def changed(self) -> bool:
        return not self.dry_run and bool(self.migrated or self.deduplicated)


def _lexists(path: Path) -> bool:
    return path.exists() or path.is_symlink()


def _fingerprint(path: Path) -> str:
    """計算包含空目錄與 symlink 目標的內容指紋。"""
    digest = hashlib.sha256()

    def add_entry(entry: Path, relative_path: str) -> None:
        encoded_path = relative_path.encode("utf-8")
        if entry.is_symlink():
            digest.update(
                b"L\0" + encoded_path + b"\0" + os.readlink(entry).encode("utf-8")
            )
        elif entry.is_dir():
            digest.update(b"D\0" + encoded_path)
        elif entry.is_file():
            digest.update(b"F\0" + encoded_path + b"\0")
            with entry.open("rb") as file_handle:
                for chunk in iter(lambda: file_handle.read(8192), b""):
                    digest.update(chunk)
        else:
            digest.update(b"O\0" + encoded_path)

    add_entry(path, ".")
    if path.is_dir() and not path.is_symlink():
        for entry in sorted(
            path.rglob("*"), key=lambda item: item.relative_to(path).as_posix()
        ):
            add_entry(entry, entry.relative_to(path).as_posix())
    return digest.hexdigest()


def _entry_digest(entry: Path) -> str:
    """單一項目的內容標記，供逐檔差異比對。"""
    if entry.is_symlink():
        return "L:" + os.readlink(entry)
    if entry.is_dir():
        return "D"
    if entry.is_file():
        digest = hashlib.sha256()
        with entry.open("rb") as file_handle:
            for chunk in iter(lambda: file_handle.read(8192), b""):
                digest.update(chunk)
        return "F:" + digest.hexdigest()
    return "O"


def _entry_map(root: Path) -> dict[str, str]:
    entries = {".": _entry_digest(root)}
    if root.is_dir() and not root.is_symlink():
        for entry in root.rglob("*"):
            entries[entry.relative_to(root).as_posix()] = _entry_digest(entry)
    return entries


def _describe_conflict(source: Path, destination: Path) -> dict[str, object]:
    """列出衝突 skill 兩端的實際差異，讓使用者不必自行 diff。"""
    legacy_entries = _entry_map(source)
    target_entries = _entry_map(destination)
    shared = legacy_entries.keys() & target_entries.keys()
    return {
        "name": source.name,
        "legacy_only": sorted(legacy_entries.keys() - target_entries.keys()),
        "target_only": sorted(target_entries.keys() - legacy_entries.keys()),
        "content_differs": sorted(
            path for path in shared if legacy_entries[path] != target_entries[path]
        ),
    }


def _print_conflicts(
    details: list[dict[str, object]], *, legacy_dir: Path, target_dir: Path
) -> None:
    console.print(
        f"[yellow]Codex skills 遷移略過 {len(details)} 個內容衝突，"
        "其餘項目照常處理。舊版與共用路徑都保留。[/yellow]"
    )
    for detail in details:
        name = detail["name"]
        console.print(f"[yellow]  {name}[/yellow]")
        for label, key in (
            ("舊版獨有", "legacy_only"),
            ("共用端獨有", "target_only"),
            ("同名內容不同", "content_differs"),
        ):
            paths = [path for path in detail[key] if path != "."]
            if paths:
                console.print(f"[dim]    {label}：{', '.join(paths)}[/dim]")
        console.print(
            f"[dim]    比對：diff -r {legacy_dir / name} {target_dir / name}[/dim]"
        )
        console.print(
            f"[dim]    處理：確認要保留的版本後補齊差異使兩端一致（下次執行會自動去重），"
            f"或直接移除 {legacy_dir / name}[/dim]"
        )


def _copy_entry(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if source.is_symlink():
        os.symlink(
            os.readlink(source),
            destination,
            target_is_directory=source.is_dir(),
        )
    elif source.is_dir():
        shutil.copytree(source, destination, symlinks=True)
    else:
        shutil.copy2(source, destination, follow_symlinks=False)


def _remove_entry(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)


def _move_entry(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        source.rename(destination)
    except OSError as exc:
        if exc.errno != errno.EXDEV:
            raise
        shutil.move(str(source), str(destination))


def _create_audit_dir(backup_root: Path) -> Path:
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S_%f")
    audit_dir = backup_root / timestamp
    audit_dir.mkdir(parents=True, exist_ok=False)
    return audit_dir


def _write_audit(
    backup_dir: Path,
    *,
    status: str,
    legacy_dir: Path,
    target_dir: Path,
    actions: list[dict[str, str]],
    conflicts: list[dict[str, object]],
) -> None:
    payload = {
        "status": status,
        "created_at": datetime.now().astimezone().isoformat(),
        "legacy_dir": str(legacy_dir),
        "target_dir": str(target_dir),
        "actions": actions,
        "conflicts": conflicts,
    }
    (backup_dir / "audit.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def migrate_legacy_codex_skills(
    *,
    legacy_dir: Path | None = None,
    target_dir: Path | None = None,
    backup_root: Path | None = None,
    dry_run: bool = False,
) -> CodexSkillsMigrationResult:
    """遷移 ``~/.codex/skills`` 的可見 skill，不處理 Codex 內建隱藏目錄。"""
    legacy_dir = legacy_dir or (get_codex_config_dir() / "skills")
    target_dir = target_dir or get_agents_skills_dir()
    backup_root = backup_root or (
        get_ai_dev_config_dir() / "backups" / "codex-skills-migration"
    )

    if not legacy_dir.exists():
        return CodexSkillsMigrationResult(dry_run=dry_run)

    migrate_names: list[str] = []
    deduplicate_names: list[str] = []
    conflict_names: list[str] = []
    conflict_details: list[dict[str, object]] = []
    skipped_names: list[str] = []

    for source in sorted(legacy_dir.iterdir(), key=lambda item: item.name):
        if (
            source.name.startswith(".")
            or source.name == "auto-skill"
            or not (source.is_dir() or source.is_symlink())
        ):
            skipped_names.append(source.name)
            continue

        destination = target_dir / source.name
        if not _lexists(destination):
            migrate_names.append(source.name)
        elif _fingerprint(source) == _fingerprint(destination):
            deduplicate_names.append(source.name)
        else:
            conflict_names.append(source.name)
            conflict_details.append(_describe_conflict(source, destination))

    migrated = tuple(migrate_names)
    deduplicated = tuple(deduplicate_names)
    conflicts = tuple(conflict_names)
    skipped = tuple(skipped_names)
    actions = [
        *({"action": "migrate", "name": name} for name in migrated),
        *({"action": "deduplicate", "name": name} for name in deduplicated),
    ]

    if conflicts:
        _print_conflicts(conflict_details, legacy_dir=legacy_dir, target_dir=target_dir)

    if not actions:
        if conflicts and not dry_run:
            audit_dir = _create_audit_dir(backup_root)
            try:
                _write_audit(
                    audit_dir,
                    status="conflict",
                    legacy_dir=legacy_dir,
                    target_dir=target_dir,
                    actions=actions,
                    conflicts=conflict_details,
                )
            except Exception:
                shutil.rmtree(audit_dir, ignore_errors=True)
                raise
            console.print(f"[dim]衝突稽核：{audit_dir}[/dim]")
        return CodexSkillsMigrationResult(
            conflicts=conflicts,
            skipped=skipped,
            dry_run=dry_run,
        )

    action_text = f"搬移 {len(migrated)}、去重 {len(deduplicated)}"
    if conflicts:
        action_text += f"、略過衝突 {len(conflicts)}"
    if dry_run:
        console.print(
            "[dim][dry-run] Codex skills 遷移："
            f"{action_text} → {target_dir}；不會寫入檔案。[/dim]"
        )
        return CodexSkillsMigrationResult(
            migrated=migrated,
            deduplicated=deduplicated,
            conflicts=conflicts,
            skipped=skipped,
            dry_run=True,
        )

    backup_dir = _create_audit_dir(backup_root)

    try:
        for action in actions:
            source = legacy_dir / action["name"]
            backup = backup_dir / action["name"]
            _copy_entry(source, backup)
            if _fingerprint(source) != _fingerprint(backup):
                raise OSError(f"備份驗證失敗：{source}")
        _write_audit(
            backup_dir,
            status="planned",
            legacy_dir=legacy_dir,
            target_dir=target_dir,
            actions=actions,
            conflicts=conflict_details,
        )
    except Exception:
        shutil.rmtree(backup_dir, ignore_errors=True)
        raise

    target_existed = target_dir.exists()
    completed: list[dict[str, str]] = []
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
        for action in actions:
            name = action["name"]
            source = legacy_dir / name
            destination = target_dir / name
            if action["action"] == "migrate":
                if _lexists(destination):
                    raise FileExistsError(f"遷移期間出現同名目標：{destination}")
                completed.append(action)
                _move_entry(source, destination)
            else:
                if not _lexists(destination) or _fingerprint(source) != _fingerprint(
                    destination
                ):
                    raise FileExistsError(f"遷移期間同名內容已變更：{destination}")
                completed.append(action)
                _remove_entry(source)

        _write_audit(
            backup_dir,
            status="partial" if conflicts else "complete",
            legacy_dir=legacy_dir,
            target_dir=target_dir,
            actions=actions,
            conflicts=conflict_details,
        )
    except Exception as exc:
        rollback_errors: list[str] = []
        for action in reversed(completed):
            name = action["name"]
            source = legacy_dir / name
            destination = target_dir / name
            try:
                if action["action"] == "migrate" and _lexists(destination):
                    _remove_entry(destination)
                if _lexists(source):
                    _remove_entry(source)
                _copy_entry(backup_dir / name, source)
            except Exception as rollback_exc:
                rollback_errors.append(f"{name}: {rollback_exc}")

        if not target_existed and target_dir.exists():
            try:
                target_dir.rmdir()
            except OSError:
                pass

        status = "rollback_failed" if rollback_errors else "rolled_back"
        _write_audit(
            backup_dir,
            status=status,
            legacy_dir=legacy_dir,
            target_dir=target_dir,
            actions=actions,
            conflicts=conflict_details,
        )
        if rollback_errors:
            raise RuntimeError(
                f"Codex skills 遷移失敗，回復不完整；請查閱 {backup_dir / 'audit.json'}"
            ) from exc
        raise RuntimeError(
            f"Codex skills 遷移失敗，已回復原狀；備份保留於 {backup_dir}"
        ) from exc

    console.print(f"[green]Codex skills 遷移完成：{action_text} → {target_dir}[/green]")
    console.print(f"[dim]備份與稽核：{backup_dir}[/dim]")
    return CodexSkillsMigrationResult(
        migrated=migrated,
        deduplicated=deduplicated,
        conflicts=conflicts,
        skipped=skipped,
        backup_dir=backup_dir,
    )
