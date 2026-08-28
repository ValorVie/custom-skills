from __future__ import annotations

import json
import os
import shutil
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from collections.abc import Callable
from typing import Iterable, Mapping, Sequence

import yaml

from script.services.npx_skills.config import SkillEntry
from script.utils.manifest import (
    compute_dir_hash,
    compute_skill_file_map,
)
from script.utils.paths import get_agents_skills_dir

FIRST_PARTY_SOURCE = "ai-dev-first-party"
FIRST_PARTY_REPOSITORY = "ValorVie/ai-dev-skills"
LEGACY_PATH_BY_CANONICAL_ID = {"simplify": "custom-simplify"}


class MigrationState(str, Enum):
    MISSING = "missing"
    UNCHANGED = "unchanged"
    MODIFIED = "modified"
    UNKNOWN = "unknown"
    ALREADY_MIGRATED = "already-migrated"


@dataclass(frozen=True)
class MigrationRecord:
    target: str
    canonical_id: str
    legacy_name: str
    path: Path
    state: MigrationState
    manifest_source: str | None = None
    expected_hash: str | None = None
    actual_hash: str | None = None
    changed_files: tuple[str, ...] = ()

    @property
    def safe_to_install(self) -> bool:
        return self.state in {
            MigrationState.MISSING,
            MigrationState.UNCHANGED,
            MigrationState.ALREADY_MIGRATED,
        }


@dataclass(frozen=True)
class VerificationResult:
    verified_names: tuple[str, ...]
    failures: tuple[str, ...]


def first_party_entries(entries: Iterable[SkillEntry]) -> tuple[SkillEntry, ...]:
    return tuple(entry for entry in entries if entry.source == FIRST_PARTY_SOURCE)


def legacy_name_for(canonical_id: str) -> str:
    return LEGACY_PATH_BY_CANONICAL_ID.get(canonical_id, canonical_id)


def manifest_names_for_detach(canonical_ids: Iterable[str]) -> set[str]:
    names: set[str] = set()
    for canonical_id in canonical_ids:
        names.add(canonical_id)
        names.add(legacy_name_for(canonical_id))
    return names


def get_npx_lock_path() -> Path:
    xdg_state_home = os.environ.get("XDG_STATE_HOME")
    if xdg_state_home:
        return Path(xdg_state_home) / "skills" / ".skill-lock.json"
    return Path.home() / ".agents" / ".skill-lock.json"


def read_npx_lock(path: Path | None = None) -> dict:
    lock_path = path or get_npx_lock_path()
    if not lock_path.is_file():
        return {"skills": {}}
    try:
        payload = json.loads(lock_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"skills": {}}
    if not isinstance(payload, dict) or not isinstance(payload.get("skills"), dict):
        return {"skills": {}}
    return payload


def _changed_files(path: Path, manifest_entry: Mapping[str, object]) -> tuple[str, ...]:
    files = manifest_entry.get("files")
    if not isinstance(files, dict):
        return ()
    current = compute_skill_file_map(path)
    base: dict[str, str] = {}
    for relative, block in files.items():
        if not isinstance(relative, str) or not isinstance(block, dict):
            continue
        value = block.get("dst_hash_at_sync")
        if isinstance(value, str) and value:
            base[relative] = value
    return tuple(
        sorted(
            relative
            for relative in set(base) | set(current)
            if base.get(relative) != current.get(relative)
        )
    )


def classify_legacy_skill(
    *,
    target: str,
    canonical_id: str,
    legacy_name: str,
    target_root: Path,
    manifest: Mapping[str, object] | None,
    npx_lock: Mapping[str, object],
    expected_repo: str,
) -> MigrationRecord:
    path = target_root / legacy_name
    lock_skills = npx_lock.get("skills", {})
    lock_entry = (
        lock_skills.get(canonical_id) if isinstance(lock_skills, dict) else None
    )
    lock_source = lock_entry.get("source") if isinstance(lock_entry, dict) else None

    if legacy_name == canonical_id and path.exists() and lock_source == expected_repo:
        return MigrationRecord(
            target=target,
            canonical_id=canonical_id,
            legacy_name=legacy_name,
            path=path,
            state=MigrationState.ALREADY_MIGRATED,
            manifest_source=expected_repo,
        )

    if not path.exists() and not path.is_symlink():
        return MigrationRecord(
            target=target,
            canonical_id=canonical_id,
            legacy_name=legacy_name,
            path=path,
            state=MigrationState.MISSING,
        )

    files = manifest.get("files", {}) if isinstance(manifest, Mapping) else {}
    skills = files.get("skills", {}) if isinstance(files, Mapping) else {}
    entry = skills.get(legacy_name) if isinstance(skills, Mapping) else None
    if not isinstance(entry, Mapping):
        return MigrationRecord(
            target=target,
            canonical_id=canonical_id,
            legacy_name=legacy_name,
            path=path,
            state=MigrationState.UNKNOWN,
        )

    source = entry.get("source")
    expected_hash = entry.get("hash")
    if (
        source != "custom-skills"
        or not isinstance(expected_hash, str)
        or not expected_hash
        or path.is_symlink()
        or not path.is_dir()
    ):
        return MigrationRecord(
            target=target,
            canonical_id=canonical_id,
            legacy_name=legacy_name,
            path=path,
            state=MigrationState.UNKNOWN,
            manifest_source=source if isinstance(source, str) else None,
            expected_hash=expected_hash if isinstance(expected_hash, str) else None,
        )

    actual_hash = compute_dir_hash(path)
    state = (
        MigrationState.UNCHANGED
        if actual_hash == expected_hash
        else MigrationState.MODIFIED
    )
    return MigrationRecord(
        target=target,
        canonical_id=canonical_id,
        legacy_name=legacy_name,
        path=path,
        state=state,
        manifest_source=source,
        expected_hash=expected_hash,
        actual_hash=actual_hash,
        changed_files=(
            _changed_files(path, entry) if state is MigrationState.MODIFIED else ()
        ),
    )


def _frontmatter_name(skill_md: Path) -> str | None:
    try:
        content = skill_md.read_text(encoding="utf-8")
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


def verify_npx_installations(
    entries: Sequence[SkillEntry],
    *,
    canonical_root: Path | None = None,
    lock_path: Path | None = None,
    agent_roots: Sequence[Path] = (),
) -> VerificationResult:
    root = canonical_root or get_agents_skills_dir()
    lock = read_npx_lock(lock_path)
    lock_skills = lock.get("skills", {})
    failures: list[str] = []
    verified: list[str] = []

    for entry in entries:
        skill_md = root / entry.skill / "SKILL.md"
        if not skill_md.is_file():
            failures.append(f"{entry.skill}: canonical path missing: {skill_md}")
        elif _frontmatter_name(skill_md) != entry.skill:
            failures.append(f"{entry.skill}: canonical frontmatter name mismatch")

        lock_entry = (
            lock_skills.get(entry.skill) if isinstance(lock_skills, dict) else None
        )
        source = lock_entry.get("source") if isinstance(lock_entry, dict) else None
        if source != entry.repo:
            failures.append(
                f"{entry.skill}: lock source mismatch: expected {entry.repo}, got {source}"
            )

        for agent_root in agent_roots:
            agent_skill = agent_root / entry.skill / "SKILL.md"
            if not agent_skill.is_file():
                failures.append(f"{entry.skill}: agent path missing: {agent_skill}")

        if not any(failure.startswith(f"{entry.skill}:") for failure in failures):
            verified.append(entry.skill)

    return VerificationResult(
        verified_names=tuple(verified),
        failures=tuple(failures),
    )


def backup_and_remove_legacy_paths(
    records: Sequence[MigrationRecord],
    *,
    verified_names: Sequence[str],
    backup_func: Callable[[str, str, str], Path | None] | None = None,
) -> tuple[str, ...]:
    """備份並移除已驗證的一次性 legacy alias；同名 canonical path 不處理。"""
    if backup_func is None:
        from script.utils.manifest import backup_file

        backup_func = backup_file

    verified = set(verified_names)
    failures: list[str] = []
    for record in records:
        if (
            record.canonical_id not in verified
            or record.legacy_name == record.canonical_id
            or record.state is not MigrationState.UNCHANGED
            or not record.path.exists()
        ):
            continue
        backup = backup_func(record.target, "skills", record.legacy_name)
        if backup is None:
            failures.append(
                f"{record.target}/{record.legacy_name}: backup failed; legacy path kept"
            )
            continue
        try:
            if record.path.is_symlink() or record.path.is_file():
                record.path.unlink()
            else:
                shutil.rmtree(record.path)
        except OSError as exc:
            failures.append(
                f"{record.target}/{record.legacy_name}: remove failed: {exc}"
            )
    return tuple(failures)
