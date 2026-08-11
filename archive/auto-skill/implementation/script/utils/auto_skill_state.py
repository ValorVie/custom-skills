"""auto-skill canonical state 管理工具。"""

from __future__ import annotations

import json
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
CLONE_POLICY_FILE = ".clonepolicy.json"
AUTO_SKILL_INDEX_PATHS = {
    Path("knowledge-base") / "_index.json",
    Path("experience") / "_index.json",
}


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
        if relative_path in AUTO_SKILL_INDEX_PATHS:
            try:
                json.loads(src_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue

        dst_path = staged_dir / relative_path
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_path, dst_path)

    return staged_dir


def _copy_existing_state_base(state_dir: Path, staged_dir: Path) -> None:
    if not state_dir.exists():
        return

    shutil.copytree(
        state_dir,
        staged_dir,
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns(CLONE_POLICY_FILE),
    )


def _load_clone_policy(source_dir: Path | None) -> dict | None:
    from . import shared

    if source_dir is None:
        return None
    return shared._load_clone_policy(source_dir, show_warning=False)


def _resolve_effective_policy(
    source_dir: Path,
    fallback_policy: dict | None,
) -> dict:
    policy = _load_clone_policy(source_dir)
    if policy is not None:
        return policy
    if fallback_policy is not None:
        return fallback_policy
    return {"rules": []}


def _merge_source_into_state(
    source_dir: Path,
    state_dir: Path,
    policy: dict,
    *,
    force: bool,
    skip_conflicts: bool,
) -> None:
    """以 clone policy 規則合併單一來源到 canonical state。"""
    from . import shared

    shared._copy_skill_with_policy(
        source_dir,
        state_dir,
        policy,
        force=force,
        skip_conflicts=skip_conflicts,
        log_conflicts=False,
    )


def _write_clone_policy_file(state_dir: Path, policy: dict | None) -> None:
    if policy is None:
        return

    (state_dir / CLONE_POLICY_FILE).write_text(
        json.dumps(policy, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _replace_state_dir(temp_state_dir: Path, state_dir: Path) -> None:
    old_state_dir: Path | None = None
    if state_dir.exists():
        old_state_dir = state_dir.parent / f".auto-skill-prev-{state_dir.name}"
        if old_state_dir.exists():
            shutil.rmtree(old_state_dir)
        state_dir.rename(old_state_dir)

    try:
        temp_state_dir.rename(state_dir)
    except Exception:
        if old_state_dir is not None and old_state_dir.exists() and not state_dir.exists():
            old_state_dir.rename(state_dir)
        raise
    else:
        if old_state_dir is not None and old_state_dir.exists():
            shutil.rmtree(old_state_dir)


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

    template_exists = _is_valid_auto_skill_dir(template_dir)
    upstream_exists = _is_valid_auto_skill_dir(upstream_dir)

    source_dirs: list[Path] = []
    if template_exists:
        source_dirs.append(template_dir)
    if upstream_exists:
        source_dirs.append(upstream_dir)

    if not source_dirs:
        return None

    state_dir.parent.mkdir(parents=True, exist_ok=True)
    template_policy = _load_clone_policy(template_dir)
    upstream_policy = _load_clone_policy(upstream_dir)
    authoritative_policy = template_policy or upstream_policy

    with tempfile.TemporaryDirectory(
        prefix="ai-dev-auto-skill-",
        dir=str(state_dir.parent),
    ) as tmp:
        tmp_root = Path(tmp)
        temp_state_dir = tmp_root / "state"
        temp_state_dir.mkdir(parents=True, exist_ok=True)
        _copy_existing_state_base(state_dir, temp_state_dir)

        if template_exists:
            staged_template = _stage_auto_skill_source(template_dir, tmp_root / "template")
            if _is_valid_auto_skill_dir(staged_template):
                _merge_source_into_state(
                    staged_template,
                    temp_state_dir,
                    _resolve_effective_policy(template_dir, None),
                    force=True,
                    skip_conflicts=False,
                )

        if upstream_exists:
            staged_upstream = _stage_auto_skill_source(upstream_dir, tmp_root / "upstream")
            if _is_valid_auto_skill_dir(staged_upstream):
                _merge_source_into_state(
                    staged_upstream,
                    temp_state_dir,
                    _resolve_effective_policy(upstream_dir, template_policy),
                    force=not template_exists,
                    skip_conflicts=template_exists,
                )

        if authoritative_policy is not None:
            _write_clone_policy_file(temp_state_dir, authoritative_policy)

        _replace_state_dir(temp_state_dir, state_dir)

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
