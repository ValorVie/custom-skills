"""auto-skill 多工具投影 helper。"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .paths import (
    get_auto_skill_backup_dir,
    get_auto_skill_projection_root,
    get_auto_skill_shadow_dir,
    get_auto_skill_shadow_state_path,
)
from .system import get_os


@dataclass
class AutoSkillProjectionResult:
    mode: str
    changed: bool
    migrated_from: str | None = None
    shadow_dir: Path | None = None


def _clean_target(path: Path) -> None:
    """清理既有 target，支援 symlink、junction、真實目錄。"""
    if not path.exists() and not path.is_symlink():
        return

    try:
        path.unlink()
        return
    except (OSError, PermissionError):
        pass

    shutil.rmtree(path)


def _resolved_target_candidate(path: Path) -> Path | None:
    try:
        return path.parent.resolve() / path.name
    except OSError:
        return None


def _points_to_source(source_dir: Path, target_dir: Path) -> bool:
    try:
        if target_dir.exists() or target_dir.is_symlink():
            return target_dir.resolve() == source_dir.resolve()
    except OSError:
        pass

    candidate = _resolved_target_candidate(target_dir)
    if candidate is None:
        return False
    try:
        return candidate == source_dir.resolve()
    except OSError:
        return False


def _create_directory_link(source_dir: Path, target_dir: Path) -> str | None:
    """建立目錄 link。"""
    if get_os() == "windows":
        result = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(target_dir), str(source_dir)],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            return "junction"

        try:
            os.symlink(str(source_dir), str(target_dir), target_is_directory=True)
            return "symlink"
        except OSError:
            return None

    try:
        relative_target = os.path.relpath(source_dir, start=target_dir.parent.resolve())
        os.symlink(relative_target, target_dir)
        return "symlink"
    except OSError:
        return None


def _project_directory(source_dir: Path, target_dir: Path) -> AutoSkillProjectionResult:
    """將指定目錄投影到 target。"""
    if not source_dir.exists() or not (source_dir / "SKILL.md").exists():
        raise FileNotFoundError(f"找不到 auto-skill source: {source_dir}")

    if _points_to_source(source_dir, target_dir):
        mode = "symlink" if target_dir.is_symlink() else "copy"
        return AutoSkillProjectionResult(mode=mode, changed=False)

    _clean_target(target_dir)
    target_dir.parent.mkdir(parents=True, exist_ok=True)

    link_mode = _create_directory_link(source_dir, target_dir)
    if link_mode is not None:
        return AutoSkillProjectionResult(mode=link_mode, changed=True)

    shutil.copytree(source_dir, target_dir, dirs_exist_ok=True)
    return AutoSkillProjectionResult(mode="copy", changed=True)


def _load_clone_policy(policy_source_dir: Path | None) -> tuple[dict, bool]:
    if policy_source_dir is None:
        return {"rules": []}, False

    from . import shared

    policy = shared._load_clone_policy(policy_source_dir, show_warning=False)
    if policy is None:
        return {"rules": []}, False
    return policy, True


def _copy_base_dir(base_dir: Path, dst_dir: Path) -> None:
    if not base_dir.exists():
        return

    shutil.copytree(
        base_dir,
        dst_dir,
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns(".clonepolicy.json"),
    )


def _merge_source_into_shadow(source_dir: Path, shadow_dir: Path, policy: dict) -> None:
    from . import shared

    shared._copy_skill_with_policy(
        source_dir,
        shadow_dir,
        policy,
        force=True,
        skip_conflicts=False,
    )


def _compute_revision(source_dir: Path, policy: dict) -> str:
    from .manifest import compute_dir_hash

    payload = {
        "source_hash": compute_dir_hash(source_dir),
        "policy": policy,
    }
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    return f"sha256:{digest}"


def _read_shadow_state(state_path: Path) -> dict | None:
    if not state_path.exists():
        return None

    try:
        return json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _write_shadow_state(state_path: Path, data: dict) -> None:
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _backup_legacy_dir(target_dir: Path, backup_root: Path) -> Path | None:
    if not target_dir.exists():
        return None

    backup_root.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    backup_dir = backup_root / timestamp
    shutil.copytree(target_dir, backup_dir)
    return backup_dir


def _detect_projection_state(
    source_dir: Path,
    target_dir: Path,
    shadow_dir: Path,
) -> str:
    if _points_to_source(shadow_dir, target_dir):
        return "shadow_link"
    if _points_to_source(source_dir, target_dir):
        return "canonical_link"
    if target_dir.is_symlink():
        try:
            target_dir.resolve(strict=True)
        except (FileNotFoundError, OSError, RuntimeError):
            return "broken_link"
        return "other_link"
    if target_dir.exists():
        return "legacy_dir"
    return "missing"


def _replace_shadow_dir(temp_shadow_dir: Path, shadow_dir: Path) -> None:
    old_shadow_dir: Path | None = None
    if shadow_dir.exists() or shadow_dir.is_symlink():
        old_shadow_dir = shadow_dir.parent / f".auto-skill-prev-{shadow_dir.name}"
        _clean_target(old_shadow_dir)
        shadow_dir.rename(old_shadow_dir)

    try:
        temp_shadow_dir.rename(shadow_dir)
    except Exception:
        if old_shadow_dir is not None and old_shadow_dir.exists() and not shadow_dir.exists():
            old_shadow_dir.rename(shadow_dir)
        raise
    else:
        if old_shadow_dir is not None and old_shadow_dir.exists():
            shutil.rmtree(old_shadow_dir)


def project_auto_skill(
    source_dir: Path,
    target_dir: Path,
    *,
    target_name: str | None = None,
    policy_source_dir: Path | None = None,
    projection_root: Path | None = None,
    backups_root: Path | None = None,
) -> AutoSkillProjectionResult:
    """將 canonical state 或 shadow state 投影到工具目錄。"""
    if not source_dir.exists() or not (source_dir / "SKILL.md").exists():
        raise FileNotFoundError(f"找不到 auto-skill canonical state: {source_dir}")

    # 舊 API：直接投影 canonical state
    if target_name is None:
        return _project_directory(source_dir, target_dir)

    if projection_root is None:
        projection_root = get_auto_skill_projection_root()
    if backups_root is None:
        backups_root = get_auto_skill_backup_dir(target_name)
    else:
        backups_root = backups_root / target_name

    shadow_dir = get_auto_skill_shadow_dir(target_name)
    state_path = get_auto_skill_shadow_state_path(target_name)
    if projection_root != get_auto_skill_projection_root():
        shadow_dir = projection_root / target_name / "auto-skill"
        state_path = projection_root / target_name / "auto-skill.state.json"

    canonical_policy, _ = _load_clone_policy(policy_source_dir)
    revision = _compute_revision(source_dir, canonical_policy)
    current_state = _detect_projection_state(source_dir, target_dir, shadow_dir)
    shadow_state = _read_shadow_state(state_path)

    if (
        shadow_state is not None
        and shadow_state.get("revision") == revision
        and shadow_dir.exists()
    ):
        projection_result = _project_directory(shadow_dir, target_dir)
        return AutoSkillProjectionResult(
            mode=projection_result.mode,
            changed=projection_result.changed,
            migrated_from=None,
            shadow_dir=shadow_dir,
        )

    migrated_from: str | None = None
    effective_policy = canonical_policy
    policy_source = "canonical"
    base_dir: Path | None = None

    if current_state == "legacy_dir":
        migrated_from = "legacy_dir"
        base_dir = target_dir
        _backup_legacy_dir(target_dir, backups_root)
        legacy_policy, legacy_policy_found = _load_clone_policy(target_dir)
        if legacy_policy_found:
            effective_policy = legacy_policy
            policy_source = "legacy"
    elif current_state == "shadow_link" and shadow_dir.exists():
        base_dir = shadow_dir
    elif current_state in {"missing", "broken_link"} and shadow_dir.exists():
        base_dir = shadow_dir
    elif current_state == "canonical_link":
        migrated_from = "canonical_link"
    elif current_state == "other_link":
        migrated_from = "other_link"

    shadow_parent = shadow_dir.parent
    shadow_parent.mkdir(parents=True, exist_ok=True)
    temp_shadow_parent = Path(
        tempfile.mkdtemp(prefix=".auto-skill-shadow-", dir=str(shadow_parent))
    )
    temp_shadow_dir = temp_shadow_parent / "auto-skill"
    temp_shadow_dir.mkdir(parents=True, exist_ok=True)

    try:
        if base_dir is not None and base_dir.exists():
            _copy_base_dir(base_dir, temp_shadow_dir)

        _merge_source_into_shadow(source_dir, temp_shadow_dir, effective_policy)
        if not (temp_shadow_dir / "SKILL.md").exists():
            raise FileNotFoundError(f"shadow build 失敗，缺少 SKILL.md: {temp_shadow_dir}")

        _replace_shadow_dir(temp_shadow_dir, shadow_dir)
        temp_shadow_dir = Path()
        _write_shadow_state(
            state_path,
            {
                "target": target_name,
                "revision": revision,
                "mode": "shadow",
                "migrated_from": migrated_from,
                "policy_source": policy_source,
            },
        )
    finally:
        if temp_shadow_parent.exists():
            shutil.rmtree(temp_shadow_parent, ignore_errors=True)

    projection_result = _project_directory(shadow_dir, target_dir)
    return AutoSkillProjectionResult(
        mode=projection_result.mode,
        changed=True,
        migrated_from=migrated_from,
        shadow_dir=shadow_dir,
    )
