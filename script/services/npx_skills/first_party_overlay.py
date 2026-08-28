from __future__ import annotations

import hashlib
import os
import stat
import tempfile
from dataclasses import dataclass, field, replace
from enum import Enum
from pathlib import Path, PurePosixPath
from typing import Literal

import yaml

from script.utils.manifest import (
    FileEntry,
    compute_dir_hash,
    compute_skill_file_map,
    is_excluded_skill_path,
)

MISSING_HASH = "missing"

ConflictClass = Literal["clean", "local-only", "both-changed", "no-base"]


def _safe_relative(value: str, *, label: str) -> PurePosixPath:
    path = PurePosixPath(value)
    if not value or path.is_absolute() or ".." in path.parts:
        raise ValueError(f"invalid {label}: {value}")
    return path


def _bytes_hash(content: bytes) -> str:
    return f"sha256:{hashlib.sha256(content).hexdigest()}"


@dataclass(frozen=True)
class OverlayEntry:
    kind: Literal["file", "deleted"]
    hash: str
    path: str | None = None

    def to_dict(self) -> dict:
        payload = {"kind": self.kind, "hash": self.hash}
        if self.path is not None:
            payload["path"] = self.path
        return payload

    @classmethod
    def from_dict(cls, data: dict) -> OverlayEntry:
        kind = data.get("kind")
        value_hash = data.get("hash")
        path = data.get("path")
        if kind not in {"file", "deleted"} or not isinstance(value_hash, str):
            raise ValueError("invalid overlay entry")
        if kind == "file":
            if not isinstance(path, str):
                raise ValueError("invalid overlay path")
            _safe_relative(path, label="overlay path")
        elif path is not None:
            raise ValueError("deleted overlay must not have a path")
        return cls(kind=kind, hash=value_hash, path=path)


@dataclass(frozen=True)
class FilePlan:
    path: str
    classification: ConflictClass
    base_hash: str | None
    source_hash: str
    local_hash: str
    overlay_hash: str | None
    effective_hash: str


@dataclass(frozen=True)
class TreeFile:
    hash: str
    content: bytes | None

    @classmethod
    def from_content(cls, content: bytes) -> TreeFile:
        return cls(_bytes_hash(content), content)

    @classmethod
    def missing(cls) -> TreeFile:
        return cls(MISSING_HASH, None)


@dataclass(frozen=True)
class PlannedFile:
    plan: FilePlan
    base_content: bytes | None
    source_content: bytes | None
    local_content: bytes | None


def plan_file(
    path: str,
    *,
    base_hash: str | None,
    source_hash: str,
    local_hash: str,
    overlay_hash: str | None,
) -> FilePlan:
    """Classify one base/source/overlay/local tuple without filesystem writes."""
    _safe_relative(path, label="file path")

    if overlay_hash is not None:
        # Installed content equal to source means raw npx may have erased the
        # materialized overlay. Keep the durable overlay as local intent.
        effective_hash = (
            local_hash
            if local_hash not in {overlay_hash, source_hash}
            else overlay_hash
        )
        if base_hash is None:
            classification: ConflictClass = (
                "clean" if effective_hash == source_hash else "no-base"
            )
        else:
            classification = (
                "local-only" if source_hash == base_hash else "both-changed"
            )
    elif base_hash is None:
        effective_hash = local_hash
        if source_hash == local_hash:
            classification = "clean"
            effective_hash = source_hash
        elif local_hash == MISSING_HASH:
            classification = "clean"
            effective_hash = source_hash
        elif source_hash == MISSING_HASH:
            classification = "local-only"
        else:
            classification = "no-base"
    elif source_hash == base_hash:
        effective_hash = local_hash
        classification = "clean" if local_hash == base_hash else "local-only"
    elif local_hash in {base_hash, source_hash}:
        classification = "clean"
        effective_hash = source_hash
    else:
        classification = "both-changed"
        effective_hash = local_hash

    return FilePlan(
        path=path,
        classification=classification,
        base_hash=base_hash,
        source_hash=source_hash,
        local_hash=local_hash,
        overlay_hash=overlay_hash,
        effective_hash=effective_hash,
    )


def snapshot_tree(root: Path) -> dict[str, TreeFile]:
    """Read a regular-file tree; symlinks and special files fail closed."""
    if root.is_symlink():
        try:
            root = root.resolve(strict=True)
        except OSError as exc:
            raise ValueError(f"unsupported file type: {root}") from exc
    if not root.is_dir():
        raise ValueError(f"unsupported file type: {root}")
    files: dict[str, TreeFile] = {}
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
        relative = path.relative_to(root)
        if is_excluded_skill_path(relative):
            continue
        mode = path.lstat().st_mode
        if stat.S_ISDIR(mode):
            continue
        if not stat.S_ISREG(mode):
            raise ValueError(f"unsupported file type: {relative.as_posix()}")
        content = path.read_bytes()
        files[relative.as_posix()] = TreeFile.from_content(content)
    return files


def plan_skill(
    *,
    base: dict[str, TreeFile] | None,
    source: dict[str, TreeFile],
    local: dict[str, TreeFile],
    overlays: dict[str, TreeFile],
) -> tuple[PlannedFile, ...]:
    missing = TreeFile.missing()
    paths = set(source) | set(local) | set(overlays)
    if base is not None:
        paths.update(base)
    planned: list[PlannedFile] = []
    for path in sorted(paths):
        base_file = base.get(path, missing) if base is not None else None
        source_file = source.get(path, missing)
        local_file = local.get(path, missing)
        overlay_file = overlays.get(path)
        plan = plan_file(
            path,
            base_hash=base_file.hash if base_file is not None else None,
            source_hash=source_file.hash,
            local_hash=local_file.hash,
            overlay_hash=overlay_file.hash if overlay_file is not None else None,
        )
        if overlay_file is not None and local_file.hash in {
            overlay_file.hash,
            source_file.hash,
        }:
            effective_local = overlay_file
        else:
            effective_local = local_file
        planned.append(
            PlannedFile(
                plan=plan,
                base_content=base_file.content if base_file is not None else None,
                source_content=source_file.content,
                local_content=effective_local.content,
            )
        )
    return tuple(planned)


@dataclass(frozen=True)
class FileState:
    src_hash: str
    src_commit: str
    src_source: str
    dst_hash_at_sync: str
    decision: str
    decided_at: str
    overlay: OverlayEntry | None = None

    def to_dict(self) -> dict:
        payload = {
            "src_hash": self.src_hash,
            "src_commit": self.src_commit,
            "src_source": self.src_source,
            "dst_hash_at_sync": self.dst_hash_at_sync,
            "decision": self.decision,
            "decided_at": self.decided_at,
        }
        if self.overlay is not None:
            payload["overlay"] = self.overlay.to_dict()
        return payload

    @classmethod
    def from_dict(cls, data: dict) -> FileState:
        required = (
            "src_hash",
            "src_commit",
            "src_source",
            "dst_hash_at_sync",
        )
        if not all(isinstance(data.get(key), str) for key in required):
            raise ValueError("invalid first-party file state")
        overlay_raw = data.get("overlay")
        overlay = (
            OverlayEntry.from_dict(overlay_raw)
            if isinstance(overlay_raw, dict)
            else None
        )
        return cls(
            src_hash=data["src_hash"],
            src_commit=data["src_commit"],
            src_source=data["src_source"],
            dst_hash_at_sync=data["dst_hash_at_sync"],
            decision=str(data.get("decision", "accepted")),
            decided_at=str(data.get("decided_at", "")),
            overlay=overlay,
        )


@dataclass(frozen=True)
class SkillState:
    source: str
    source_commit: str
    files: dict[str, FileState] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "source_commit": self.source_commit,
            "files": {
                path: state.to_dict() for path, state in sorted(self.files.items())
            },
        }

    @classmethod
    def from_dict(cls, data: dict) -> SkillState:
        source = data.get("source")
        source_commit = data.get("source_commit")
        files_raw = data.get("files", {})
        if (
            not isinstance(source, str)
            or not isinstance(source_commit, str)
            or not isinstance(files_raw, dict)
        ):
            raise ValueError("invalid first-party skill state")
        files: dict[str, FileState] = {}
        for relative, raw in files_raw.items():
            if not isinstance(relative, str) or not isinstance(raw, dict):
                raise ValueError("invalid first-party file mapping")
            _safe_relative(relative, label="file path")
            files[relative] = FileState.from_dict(raw)
        return cls(source=source, source_commit=source_commit, files=files)


@dataclass(frozen=True)
class FirstPartyState:
    skills: dict[str, SkillState] = field(default_factory=dict)


class TransactionStatus(str, Enum):
    PLANNED = "PLANNED"
    BACKED_UP = "BACKED_UP"
    BASE_APPLIED = "BASE_APPLIED"
    OVERLAY_APPLIED = "OVERLAY_APPLIED"
    VERIFIED = "VERIFIED"
    COMMITTED = "COMMITTED"


@dataclass(frozen=True)
class TransactionJournal:
    skill: str
    status: TransactionStatus
    backup_dir: str
    roots: dict[str, str]
    started_at: str

    def to_dict(self) -> dict:
        return {
            "schema_version": 1,
            "skill": self.skill,
            "status": self.status.value,
            "backup_dir": self.backup_dir,
            "roots": dict(sorted(self.roots.items())),
            "started_at": self.started_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> TransactionJournal:
        try:
            skill = data["skill"]
            status = TransactionStatus(data["status"])
            backup_dir = data["backup_dir"]
            roots = data["roots"]
            started_at = data["started_at"]
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("invalid transaction journal") from exc
        if (
            data.get("schema_version") != 1
            or not isinstance(skill, str)
            or not isinstance(backup_dir, str)
            or not isinstance(roots, dict)
            or not isinstance(started_at, str)
        ):
            raise ValueError("invalid transaction journal")
        _safe_relative(skill, label="skill name")
        _safe_relative(backup_dir, label="backup directory")
        checked_roots: dict[str, str] = {}
        for label, relative in roots.items():
            if not isinstance(label, str) or not isinstance(relative, str):
                raise ValueError("invalid transaction journal")
            _safe_relative(relative, label="backup root")
            checked_roots[label] = relative
        return cls(skill, status, backup_dir, checked_roots, started_at)


class TransactionJournalStore:
    def __init__(self, root: Path):
        self.root = root

    def path_for(self, skill: str) -> Path:
        safe = _safe_relative(skill, label="skill name")
        if len(safe.parts) != 1:
            raise ValueError(f"invalid skill name: {skill}")
        return self.root / f"{skill}.yaml"

    def read(self, skill: str) -> TransactionJournal | None:
        path = self.path_for(skill)
        if not path.exists():
            return None
        try:
            payload = yaml.safe_load(path.read_text(encoding="utf-8"))
            if not isinstance(payload, dict):
                raise ValueError("invalid transaction journal")
            return TransactionJournal.from_dict(payload)
        except (OSError, yaml.YAMLError, ValueError) as exc:
            raise ValueError(f"invalid transaction journal: {path}") from exc

    def write(self, journal: TransactionJournal) -> None:
        path = self.path_for(journal.skill)
        self.root.mkdir(parents=True, exist_ok=True)
        os.chmod(self.root, 0o700)
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{path.name}.", dir=self.root, text=True
        )
        temporary = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                yaml.safe_dump(
                    journal.to_dict(), stream, allow_unicode=True, sort_keys=False
                )
                stream.flush()
                os.fsync(stream.fileno())
            os.chmod(temporary, 0o600)
            os.replace(temporary, path)
        finally:
            if temporary.exists():
                temporary.unlink()

    def update(
        self, journal: TransactionJournal, status: TransactionStatus
    ) -> TransactionJournal:
        updated = replace(journal, status=status)
        self.write(updated)
        return updated


class FirstPartyStateStore:
    def __init__(self, manifest_path: Path, overlay_root: Path):
        self.manifest_path = manifest_path
        self.overlay_root = overlay_root

    def _overlay_path(self, relative: PurePosixPath) -> Path:
        if self.overlay_root.is_symlink():
            raise ValueError("overlay symlink is not supported")
        cursor = self.overlay_root
        for part in relative.parts[:-1]:
            cursor = cursor / part
            if cursor.is_symlink():
                raise ValueError(f"overlay symlink is not supported: {cursor}")
        target = self.overlay_root.joinpath(*relative.parts)
        if target.is_symlink():
            raise ValueError(f"overlay symlink is not supported: {target}")
        root = self.overlay_root.resolve(strict=False)
        if not target.resolve(strict=False).is_relative_to(root):
            raise ValueError("overlay path escapes overlay root")
        return target

    def read(self) -> FirstPartyState:
        if not self.manifest_path.exists():
            return FirstPartyState()
        try:
            payload = (
                yaml.safe_load(self.manifest_path.read_text(encoding="utf-8")) or {}
            )
        except (OSError, yaml.YAMLError) as exc:
            raise ValueError(
                f"first-party overlay state unreadable: {self.manifest_path}"
            ) from exc
        if (
            not isinstance(payload, dict)
            or payload.get("schema_version") != 2
            or payload.get("managed_by") != "ai-dev-first-party-reconcile"
        ):
            raise ValueError(f"invalid first-party overlay state: {self.manifest_path}")
        skills_raw = payload.get("skills", {})
        if not isinstance(skills_raw, dict):
            raise ValueError("first-party skills state must be a mapping")
        skills: dict[str, SkillState] = {}
        for name, raw in skills_raw.items():
            if not isinstance(name, str) or not isinstance(raw, dict):
                raise ValueError("invalid first-party skill state entry")
            _safe_relative(name, label="skill name")
            skills[name] = SkillState.from_dict(raw)
        return FirstPartyState(skills=skills)

    def write(self, state: FirstPartyState) -> None:
        payload = {
            "schema_version": 2,
            "managed_by": "ai-dev-first-party-reconcile",
            "skills": {
                name: skill.to_dict() for name, skill in sorted(state.skills.items())
            },
        }
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{self.manifest_path.name}.",
            dir=self.manifest_path.parent,
            text=True,
        )
        temporary = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                yaml.safe_dump(payload, stream, allow_unicode=True, sort_keys=False)
                stream.flush()
                os.fsync(stream.fileno())
            os.chmod(temporary, 0o600)
            os.replace(temporary, self.manifest_path)
        finally:
            if temporary.exists():
                temporary.unlink()

    def write_overlay(
        self, skill: str, relative: str, content: bytes | None
    ) -> OverlayEntry:
        skill_path = _safe_relative(skill, label="skill name")
        relative_path = _safe_relative(relative, label="overlay path")
        stored_relative = skill_path / relative_path
        self.overlay_root.mkdir(parents=True, exist_ok=True)
        os.chmod(self.overlay_root, 0o700)
        target = self._overlay_path(stored_relative)
        if content is None:
            if target.exists():
                target.unlink()
            return OverlayEntry(kind="deleted", hash=MISSING_HASH, path=None)

        target.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{target.name}.",
            dir=target.parent,
        )
        temporary = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            os.chmod(temporary, 0o600)
            os.replace(temporary, target)
        finally:
            if temporary.exists():
                temporary.unlink()
        return OverlayEntry(
            kind="file",
            hash=_bytes_hash(content),
            path=stored_relative.as_posix(),
        )

    def read_overlay(self, entry: OverlayEntry) -> bytes | None:
        if entry.kind == "deleted":
            return None
        if entry.path is None:
            raise ValueError("overlay path missing")
        relative = _safe_relative(entry.path, label="overlay path")
        path = self._overlay_path(relative)
        try:
            content = path.read_bytes()
        except OSError as exc:
            raise ValueError(f"overlay content unreadable: {entry.path}") from exc
        if _bytes_hash(content) != entry.hash:
            raise ValueError(f"overlay hash mismatch: {entry.path}")
        return content


def expand_v1_skill(
    name: str,
    legacy: FileEntry,
    base_root: Path | None,
) -> SkillState:
    if base_root is None or not base_root.is_dir():
        raise ValueError(f"base commit unavailable: {name}")
    if compute_dir_hash(base_root) != legacy.src_hash:
        raise ValueError(f"base hash mismatch: {name}")
    files = {
        relative: FileState(
            src_hash=file_hash,
            src_commit=legacy.src_commit,
            src_source=legacy.src_source,
            dst_hash_at_sync=file_hash,
            decision="accepted",
            decided_at=legacy.decided_at,
        )
        for relative, file_hash in compute_skill_file_map(base_root).items()
    }
    return SkillState(
        source=legacy.src_source,
        source_commit=legacy.src_commit,
        files=files,
    )
