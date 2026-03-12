"""auto-skill 多工具投影 helper。"""

from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .system import get_os


@dataclass
class AutoSkillProjectionResult:
    mode: str
    changed: bool


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


def project_auto_skill(
    source_dir: Path,
    target_dir: Path,
) -> AutoSkillProjectionResult:
    """將 canonical state 投影到工具目錄。"""
    if not source_dir.exists() or not (source_dir / "SKILL.md").exists():
        raise FileNotFoundError(f"找不到 auto-skill canonical state: {source_dir}")

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
