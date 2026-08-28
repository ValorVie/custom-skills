from __future__ import annotations

import os
import re
import subprocess
import tempfile
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

import yaml

from script.services.npx_skills.config import SkillEntry
from script.services.npx_skills.migration import (
    MigrationRecord,
    MigrationState,
    VerificationResult,
    read_npx_lock,
)
from script.utils.manifest import FileEntry, classify_file, compute_dir_hash


class GuardAction(str, Enum):
    NOOP = "noop"
    APPLY = "apply"
    BLOCK = "block"
    BOOTSTRAP = "bootstrap"


@dataclass(frozen=True)
class GuardRecord:
    entry: SkillEntry
    classification: str
    action: GuardAction
    source_hash: str
    source_commit: str
    base_hash: str | None
    local_hashes: tuple[tuple[str, str | None], ...]


@dataclass(frozen=True)
class ReconcilePlan:
    records: tuple[GuardRecord, ...]

    def entries_for(self, action: GuardAction) -> tuple[SkillEntry, ...]:
        return tuple(record.entry for record in self.records if record.action is action)


@dataclass(frozen=True)
class SourceSnapshot:
    skills_root: Path
    commit: str


_DIVERGED_HASH = "sha256:local-paths-diverged"
_MISSING_HASH = "sha256:local-path-missing"


def get_first_party_local_roots(
    agents: Sequence[str], *, home: Path | None = None
) -> dict[str, Path]:
    """Resolve the verified npx 1.5.x global paths for ai-dev's agent IDs."""
    root = home or Path.home()
    canonical = root / ".agents" / "skills"
    mapping = {
        "claude-code": root / ".claude" / "skills",
        "codex": canonical,
        "gemini-cli": canonical,
        "opencode": canonical,
        "antigravity": canonical,
    }
    roots = {"canonical": canonical}
    for agent in agents:
        if agent not in mapping:
            raise ValueError(f"第一方 npx agent path 尚未驗證: {agent}")
        roots[agent] = mapping[agent]
    return roots


def read_guard_entries(path: Path) -> dict[str, FileEntry]:
    if not path.exists():
        return {}
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError) as exc:
        raise ValueError(f"第一方 guard manifest 無法讀取: {path}: {exc}") from exc
    if (
        not isinstance(payload, dict)
        or payload.get("managed_by") != "ai-dev-first-party-guard"
    ):
        raise ValueError(f"第一方 guard manifest 格式無效: {path}")
    skills = payload.get("skills", {})
    if not isinstance(skills, dict):
        raise ValueError(f"第一方 guard manifest skills 必須是 mapping: {path}")
    entries: dict[str, FileEntry] = {}
    for name, raw in skills.items():
        if not isinstance(name, str) or not isinstance(raw, dict):
            raise ValueError(f"第一方 guard manifest entry 格式無效: {path}")
        entry = FileEntry.from_dict(raw)
        if entry is None:
            raise ValueError(f"第一方 guard manifest entry 缺少 base: {name}")
        entries[name] = entry
    return entries


def record_guard_success(
    path: Path,
    accepted: Sequence[tuple[SkillEntry, str, str]],
) -> None:
    if not accepted:
        return
    entries = read_guard_entries(path)
    decided_at = datetime.now(timezone.utc).isoformat()
    for skill, source_hash, source_commit in accepted:
        entries[skill.skill] = FileEntry(
            src_hash=source_hash,
            src_commit=source_commit,
            src_source=skill.repo,
            dst_hash_at_sync=source_hash,
            decision="accepted",
            decided_at=decided_at,
        )

    payload = {
        "schema_version": 1,
        "managed_by": "ai-dev-first-party-guard",
        "skills": {name: entry.to_dict() for name, entry in sorted(entries.items())},
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        dir=path.parent,
        text=True,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            yaml.safe_dump(payload, stream, allow_unicode=True, sort_keys=False)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _legacy_base(
    canonical_id: str, records: Sequence[MigrationRecord]
) -> FileEntry | None:
    hashes = {
        record.expected_hash
        for record in records
        if record.canonical_id == canonical_id and record.expected_hash
    }
    if len(hashes) != 1:
        return None
    value = hashes.pop()
    return FileEntry(
        src_hash=value,
        src_commit="legacy-ai-dev-manifest",
        src_source="custom-skills",
        dst_hash_at_sync=value,
        decision="accepted",
        decided_at="",
    )


def _local_hashes(
    canonical_id: str,
    local_roots: Mapping[str, Path],
    legacy_records: Sequence[MigrationRecord],
) -> tuple[tuple[str, str | None], ...]:
    paths: list[tuple[str, Path]] = [
        (label, root / canonical_id) for label, root in local_roots.items()
    ]
    paths.extend(
        (f"legacy:{record.target}", record.path)
        for record in legacy_records
        if record.canonical_id == canonical_id
        and record.state is not MigrationState.ALREADY_MIGRATED
        and (record.path.exists() or record.path.is_symlink())
    )

    seen: set[Path] = set()
    hashes: list[tuple[str, str | None]] = []
    for label, path in paths:
        resolved = path.resolve(strict=False)
        if resolved in seen:
            continue
        seen.add(resolved)
        if not path.exists() or not path.is_dir():
            hashes.append((label, None))
            continue
        hashes.append((label, compute_dir_hash(path)))
    return tuple(hashes)


def _aggregate_local_hash(local_hashes: Sequence[tuple[str, str | None]]) -> str:
    values = [value for _, value in local_hashes]
    if not values or all(value is None for value in values):
        return _MISSING_HASH
    if any(value is None for value in values):
        return _DIVERGED_HASH
    unique = set(values)
    return unique.pop() if len(unique) == 1 else _DIVERGED_HASH


def _aggregate_legacy_hash(local_hashes: Sequence[tuple[str, str | None]]) -> str:
    values = {value for _, value in local_hashes if value is not None}
    if not values:
        return _MISSING_HASH
    return values.pop() if len(values) == 1 else _DIVERGED_HASH


def plan_first_party_reconcile(
    entries: Sequence[SkillEntry],
    *,
    source_skills_root: Path,
    source_commit: str,
    guard_path: Path,
    local_roots: Mapping[str, Path],
    npx_lock: Mapping[str, object] | None = None,
    legacy_records: Sequence[MigrationRecord] = (),
) -> ReconcilePlan:
    guard = read_guard_entries(guard_path)
    lock = npx_lock or {"skills": {}}
    lock_skills = lock.get("skills", {})
    records: list[GuardRecord] = []

    for entry in entries:
        source_path = source_skills_root / entry.skill
        if not source_path.is_dir():
            raise ValueError(f"第一方 source 缺少 skill: {entry.skill}")
        source_hash = compute_dir_hash(source_path)
        local_hashes = _local_hashes(entry.skill, local_roots, legacy_records)
        unsafe_legacy = tuple(
            record
            for record in legacy_records
            if record.canonical_id == entry.skill and not record.safe_to_install
        )
        if unsafe_legacy:
            classification = (
                "local-only"
                if any(
                    record.state is MigrationState.MODIFIED for record in unsafe_legacy
                )
                else "no-base"
            )
            records.append(
                GuardRecord(
                    entry=entry,
                    classification=classification,
                    action=GuardAction.BLOCK,
                    source_hash=source_hash,
                    source_commit=source_commit,
                    base_hash=None,
                    local_hashes=local_hashes,
                )
            )
            continue
        guard_base = guard.get(entry.skill)
        legacy_base = _legacy_base(entry.skill, legacy_records)
        base = guard_base or legacy_base
        aggregate = (
            _aggregate_legacy_hash(local_hashes)
            if guard_base is None and legacy_base is not None
            else _aggregate_local_hash(local_hashes)
        )
        all_missing = aggregate == _MISSING_HASH
        lock_entry = (
            lock_skills.get(entry.skill) if isinstance(lock_skills, dict) else None
        )
        lock_source = lock_entry.get("source") if isinstance(lock_entry, dict) else None

        if base is not None:
            if guard_base is not None and lock_source != entry.repo:
                classification = "no-base"
                action = GuardAction.BLOCK
            else:
                classification = classify_file(base, source_hash, aggregate)
                if classification == "clean":
                    action = (
                        GuardAction.APPLY
                        if source_hash != base.src_hash or all_missing
                        else GuardAction.NOOP
                    )
                else:
                    action = GuardAction.BLOCK
        elif all_missing:
            classification = "no-base"
            action = GuardAction.APPLY
        else:
            local_values = {value for _, value in local_hashes if value is not None}
            if lock_source == entry.repo and local_values == {source_hash}:
                classification = "no-base"
                action = GuardAction.BOOTSTRAP
            else:
                classification = "no-base"
                action = GuardAction.BLOCK

        records.append(
            GuardRecord(
                entry=entry,
                classification=classification,
                action=action,
                source_hash=source_hash,
                source_commit=source_commit,
                base_hash=base.src_hash if base is not None else None,
                local_hashes=local_hashes,
            )
        )

    return ReconcilePlan(records=tuple(records))


def _frontmatter_name(path: Path) -> str | None:
    try:
        content = path.read_text(encoding="utf-8")
    except OSError:
        return None
    if not content.startswith("---\n"):
        return None
    end = content.find("\n---\n", 4)
    if end < 0:
        return None
    try:
        metadata = yaml.safe_load(content[4:end])
    except yaml.YAMLError:
        return None
    if not isinstance(metadata, dict) or not isinstance(metadata.get("name"), str):
        return None
    return metadata["name"].strip()


def verify_first_party_paths(
    entries: Sequence[SkillEntry],
    *,
    source_skills_root: Path,
    local_roots: Mapping[str, Path],
    lock_path: Path | None = None,
) -> VerificationResult:
    lock = read_npx_lock(lock_path)
    lock_skills = lock.get("skills", {})
    failures: list[str] = []
    verified: list[str] = []

    for entry in entries:
        source_path = source_skills_root / entry.skill
        if not source_path.is_dir():
            failures.append(f"{entry.skill}: source path missing: {source_path}")
            continue
        source_hash = compute_dir_hash(source_path)
        for label, root in local_roots.items():
            local_path = root / entry.skill
            skill_md = local_path / "SKILL.md"
            if not skill_md.is_file():
                failures.append(f"{entry.skill}: {label} path missing: {local_path}")
                continue
            if _frontmatter_name(skill_md) != entry.skill:
                failures.append(f"{entry.skill}: {label} frontmatter name mismatch")
                continue
            if compute_dir_hash(local_path) != source_hash:
                failures.append(f"{entry.skill}: {label} hash mismatch")

        lock_entry = (
            lock_skills.get(entry.skill) if isinstance(lock_skills, dict) else None
        )
        lock_source = lock_entry.get("source") if isinstance(lock_entry, dict) else None
        if lock_source != entry.repo:
            failures.append(
                f"{entry.skill}: lock source mismatch: expected {entry.repo}, got {lock_source}"
            )

        if not any(item.startswith(f"{entry.skill}:") for item in failures):
            verified.append(entry.skill)

    return VerificationResult(tuple(verified), tuple(failures))


@contextmanager
def checkout_first_party_source(repo: str) -> Iterator[SourceSnapshot]:
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo):
        raise ValueError(f"第一方 repository 格式無效: {repo}")
    with tempfile.TemporaryDirectory(prefix="ai-dev-first-party-") as temporary:
        checkout = Path(temporary) / "source"
        result = subprocess.run(
            [
                "git",
                "clone",
                "--depth",
                "1",
                "--quiet",
                f"https://github.com/{repo}.git",
                str(checkout),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f"無法取得第一方 source snapshot: {repo}")
        commit = subprocess.run(
            ["git", "-C", str(checkout), "rev-parse", "HEAD"],
            check=False,
            capture_output=True,
            text=True,
        )
        if commit.returncode != 0 or not commit.stdout.strip():
            raise RuntimeError(f"無法解析第一方 source commit: {repo}")
        yield SourceSnapshot(
            skills_root=checkout / "skills",
            commit=commit.stdout.strip(),
        )
