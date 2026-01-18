"""
install 與 maintain 指令的共用函式與配置。
"""

import os
import stat
import errno
import shutil
from pathlib import Path
from rich.console import Console

from utils.paths import (
    get_custom_skills_dir,
    get_claude_config_dir,
    get_antigravity_config_dir,
    get_opencode_config_dir,
    get_superpowers_dir,
    get_uds_dir,
    get_obsidian_skills_dir,
    get_project_root,
)

console = Console()

# ============================================================
# 共用配置
# ============================================================

NPM_PACKAGES = [
    "@anthropic-ai/claude-code",
    "@fission-ai/openspec@latest",
    "@google/gemini-cli",
    "universal-dev-standards",
    "opencode-ai@latest",
]

REPOS = {
    "custom_skills": (
        "https://github.com/ValorVie/custom-skills.git",
        get_custom_skills_dir,
    ),
    "superpowers": ("https://github.com/obra/superpowers.git", get_superpowers_dir),
    "uds": ("https://github.com/AsiaOstrich/universal-dev-standards.git", get_uds_dir),
    "obsidian_skills": (
        "https://github.com/kepano/obsidian-skills.git",
        get_obsidian_skills_dir,
    ),
}

UNWANTED_UDS_FILES = [
    "tdd-assistant",
    "CONTRIBUTING.template.md",
    "install.ps1",
    "install.sh",
    "README.md",
]


# ============================================================
# 輔助函式
# ============================================================


def handle_remove_readonly(func, path, exc):
    """處理 Windows 下刪除唯讀檔案時的 PermissionError。"""
    excvalue = exc[1]
    if func in (os.rmdir, os.remove, os.unlink) and excvalue.errno == errno.EACCES:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    else:
        raise


def clean_unwanted_files(target_dir: Path, use_readonly_handler: bool = False):
    """清理目標目錄中不需要的 UDS 檔案。"""
    for item in UNWANTED_UDS_FILES:
        path = target_dir / item
        if not path.exists():
            continue
        if path.is_dir():
            handler = handle_remove_readonly if use_readonly_handler else None
            shutil.rmtree(path, onerror=handler)
        else:
            path.unlink()


def copy_tree_if_exists(src: Path, dst: Path, msg: str):
    """若來源存在，複製目錄樹到目標位置。"""
    if src.exists():
        console.print(msg)
        dst.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src, dst, dirs_exist_ok=True)
        return True
    return False


# ============================================================
# 主要函式
# ============================================================


def copy_skills():
    """複製 Skills 從來源到目標目錄。"""
    # 來源路徑
    src_uds = get_uds_dir() / "skills" / "claude-code"
    src_obsidian = get_obsidian_skills_dir() / "skills"
    src_custom = get_custom_skills_dir() / "skills"

    # 目標路徑
    dst_custom = get_custom_skills_dir() / "skills"
    dst_claude = get_claude_config_dir() / "skills"
    dst_antigravity = get_antigravity_config_dir() / "skills"

    # 1. UDS + Obsidian → Custom Skills (統一來源)
    copy_tree_if_exists(src_uds, dst_custom, f"正在複製從 {src_uds} 到 {dst_custom}...")
    clean_unwanted_files(dst_custom)
    copy_tree_if_exists(
        src_obsidian, dst_custom, f"正在複製 Obsidian Skills 到 {dst_custom}..."
    )

    # 2. UDS + Obsidian → Claude Code
    copy_tree_if_exists(src_uds, dst_claude, f"正在複製從 {src_uds} 到 {dst_claude}...")
    clean_unwanted_files(dst_claude)
    copy_tree_if_exists(
        src_obsidian, dst_claude, f"正在複製 Obsidian Skills 到 {dst_claude}..."
    )

    # 3. Custom Skills + Obsidian → Antigravity
    copy_tree_if_exists(
        src_custom, dst_antigravity, f"正在複製從 {src_custom} 到 {dst_antigravity}..."
    )
    copy_tree_if_exists(
        src_obsidian,
        dst_antigravity,
        f"正在複製 Obsidian Skills 到 {dst_antigravity}...",
    )

    # 4. Commands
    src_cmd_claude = get_custom_skills_dir() / "command" / "claude"
    dst_cmd_claude = get_claude_config_dir() / "commands"
    if src_cmd_claude.exists() and dst_cmd_claude.exists():
        console.print(f"正在複製 Commands 到 {dst_cmd_claude}...")
        shutil.copytree(src_cmd_claude, dst_cmd_claude, dirs_exist_ok=True)

    src_cmd_antigravity = get_custom_skills_dir() / "command" / "antigravity"
    dst_cmd_antigravity = get_antigravity_config_dir() / "global_workflows"
    copy_tree_if_exists(
        src_cmd_antigravity,
        dst_cmd_antigravity,
        f"正在複製 Workflows 到 {dst_cmd_antigravity}...",
    )

    # 5. Agents
    src_agent = get_custom_skills_dir() / "agent" / "opencode"
    dst_agent = get_opencode_config_dir() / "agent"
    copy_tree_if_exists(src_agent, dst_agent, f"正在複製 Agents 到 {dst_agent}...")

    # 6. 專案目錄 (開發環境)
    project_root = get_project_root()
    if not (
        (project_root / ".git").exists() and (project_root / "pyproject.toml").exists()
    ):
        return

    console.print(f"[bold yellow]偵測到專案目錄：{project_root}[/bold yellow]")

    # Skills → Project
    dst_project_skills = project_root / "skills"
    copy_tree_if_exists(
        src_uds, dst_project_skills, f"正在複製從 {src_uds} 到 {dst_project_skills}..."
    )
    clean_unwanted_files(dst_project_skills, use_readonly_handler=True)
    copy_tree_if_exists(
        src_obsidian,
        dst_project_skills,
        f"正在複製 Obsidian Skills 到 {dst_project_skills}...",
    )

    # Commands → Project
    src_command = get_custom_skills_dir() / "command"
    dst_project_command = project_root / "command"
    copy_tree_if_exists(
        src_command,
        dst_project_command,
        f"正在複製從 {src_command} 到 {dst_project_command}...",
    )

    # Agents → Project
    src_agent_all = get_custom_skills_dir() / "agent"
    dst_project_agent = project_root / "agent"
    copy_tree_if_exists(
        src_agent_all,
        dst_project_agent,
        f"正在複製從 {src_agent_all} 到 {dst_project_agent}...",
    )
