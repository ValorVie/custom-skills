"""auto-skill canonical state 管理工具。"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from .paths import (
    get_auto_skill_dir,
    get_auto_skill_repo_dir,
    get_custom_skills_dir,
)

AUTO_SKILL_IGNORE_TOP_LEVEL = {".git", "assets"}
AUTO_SKILL_IGNORE_FILES = {"README.md"}


def _is_valid_auto_skill_dir(path: Path | None) -> bool:
    if path is None:
        return False
    return path.exists() and (path / "SKILL.md").exists()


def _stage_auto_skill_source(source_dir: Path, staged_dir: Path) -> Path:
    """建立可安全合併的 staged source，排除不應進 state 的檔案。"""
    staged_dir.mkdir(parents=True, exist_ok=True)

    for src_path in sorted(source_dir.rglob("*")):
        if not src_path.is_file():
            continue

        relative_path = src_path.relative_to(source_dir)
        if relative_path.parts and relative_path.parts[0] in AUTO_SKILL_IGNORE_TOP_LEVEL:
            continue
        if len(relative_path.parts) == 1 and relative_path.name in AUTO_SKILL_IGNORE_FILES:
            continue

        dst_path = staged_dir / relative_path
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_path, dst_path)

    return staged_dir


def _merge_source_into_state(source_dir: Path, state_dir: Path) -> None:
    """以 clone policy 規則合併單一來源到 canonical state。"""
    from . import shared

    policy = shared._load_clone_policy(source_dir, show_warning=False)
    if policy is None:
        policy = {"rules": []}

    shared._copy_skill_with_policy(
        source_dir,
        state_dir,
        policy,
        force=False,
        skip_conflicts=True,
    )


def refresh_auto_skill_state(
    template_dir: Path | None = None,
    upstream_dir: Path | None = None,
    state_dir: Path | None = None,
) -> Path | None:
    """刷新 auto-skill canonical state。"""
    if template_dir is None:
        template_dir = get_custom_skills_dir() / "skills" / "auto-skill"
    if upstream_dir is None:
        upstream_dir = get_auto_skill_repo_dir()
    if state_dir is None:
        state_dir = get_auto_skill_dir()

    source_dirs: list[Path] = []
    if _is_valid_auto_skill_dir(template_dir):
        source_dirs.append(template_dir)
    if _is_valid_auto_skill_dir(upstream_dir):
        source_dirs.append(upstream_dir)

    if not source_dirs:
        return None

    state_dir.parent.mkdir(parents=True, exist_ok=True)
    state_dir.mkdir(parents=True, exist_ok=True)

    for source_dir in source_dirs:
        with tempfile.TemporaryDirectory(prefix="ai-dev-auto-skill-") as tmp:
            staged_dir = _stage_auto_skill_source(source_dir, Path(tmp) / "source")
            if not _is_valid_auto_skill_dir(staged_dir):
                continue
            _merge_source_into_state(staged_dir, state_dir)

    return state_dir


def ensure_auto_skill_state(
    template_dir: Path | None = None,
    upstream_dir: Path | None = None,
    state_dir: Path | None = None,
) -> Path | None:
    """確保 auto-skill canonical state 存在，必要時同步刷新。"""
    return refresh_auto_skill_state(
        template_dir=template_dir,
        upstream_dir=upstream_dir,
        state_dir=state_dir,
    )
