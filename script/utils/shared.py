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
    get_config_dir,
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

# 不需要的 UDS 檔案（複製後清理）
UNWANTED_UDS_FILES = [
    "tdd-assistant",
    "CONTRIBUTING.template.md",
    "install.ps1",
    "install.sh",
    "README.md",
]


# ============================================================
# 共用函式
# ============================================================


def handle_remove_readonly(func, path, exc):
    """
    處理 Windows 下刪除唯讀檔案時的 PermissionError。
    當 shutil.rmtree 遇到唯讀檔案時會調用此函數。
    """
    excvalue = exc[1]
    if func in (os.rmdir, os.remove, os.unlink) and excvalue.errno == errno.EACCES:
        # 修改權限為可寫
        os.chmod(path, stat.S_IWRITE)
        # 重試操作
        func(path)
    else:
        # 其他錯誤則拋出
        raise


def clean_unwanted_files(target_dir: Path, use_readonly_handler: bool = False):
    """清理目標目錄中不需要的 UDS 檔案。"""
    for item in UNWANTED_UDS_FILES:
        path = target_dir / item
        if path.exists():
            if path.is_dir():
                if use_readonly_handler:
                    shutil.rmtree(path, onerror=handle_remove_readonly)
                else:
                    shutil.rmtree(path)
            else:
                path.unlink()


def copy_skills():
    """複製 Skills 從來源到目標目錄。"""
    # 來源路徑
    src_uds_claude = get_uds_dir() / "skills" / "claude-code"
    src_obsidian_skills = get_obsidian_skills_dir() / "skills"

    # 目標路徑
    dst_custom_skills = get_custom_skills_dir() / "skills"
    dst_claude_skills = get_claude_config_dir() / "skills"
    dst_antigravity_skills = get_antigravity_config_dir() / "skills"

    # --------------------------------------------------------
    # 1. UDS → Custom Skills (統一來源)
    # --------------------------------------------------------
    if src_uds_claude.exists():
        console.print(f"正在複製從 {src_uds_claude} 到 {dst_custom_skills}...")
        dst_custom_skills.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src_uds_claude, dst_custom_skills, dirs_exist_ok=True)

    clean_unwanted_files(dst_custom_skills)

    # --------------------------------------------------------
    # 2. Obsidian Skills → Custom Skills (合併)
    # --------------------------------------------------------
    if src_obsidian_skills.exists():
        console.print(f"正在複製 Obsidian Skills 到 {dst_custom_skills}...")
        shutil.copytree(src_obsidian_skills, dst_custom_skills, dirs_exist_ok=True)

    # --------------------------------------------------------
    # 3. UDS → Claude Code
    # --------------------------------------------------------
    if src_uds_claude.exists():
        console.print(f"正在複製從 {src_uds_claude} 到 {dst_claude_skills}...")
        dst_claude_skills.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src_uds_claude, dst_claude_skills, dirs_exist_ok=True)

    clean_unwanted_files(dst_claude_skills)

    # Obsidian Skills → Claude Code
    if src_obsidian_skills.exists():
        console.print(f"正在複製 Obsidian Skills 到 {dst_claude_skills}...")
        shutil.copytree(src_obsidian_skills, dst_claude_skills, dirs_exist_ok=True)

    # --------------------------------------------------------
    # 4. Custom Skills → Antigravity
    # --------------------------------------------------------
    src_custom_skills = get_custom_skills_dir() / "skills"
    if src_custom_skills.exists():
        console.print(f"正在複製從 {src_custom_skills} 到 {dst_antigravity_skills}...")
        dst_antigravity_skills.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src_custom_skills, dst_antigravity_skills, dirs_exist_ok=True)

    # Obsidian Skills → Antigravity
    if src_obsidian_skills.exists():
        console.print(f"正在複製 Obsidian Skills 到 {dst_antigravity_skills}...")
        shutil.copytree(src_obsidian_skills, dst_antigravity_skills, dirs_exist_ok=True)

    # --------------------------------------------------------
    # 5. Commands
    # --------------------------------------------------------
    src_cmd_claude = get_custom_skills_dir() / "command" / "claude"
    dst_cmd_claude = get_claude_config_dir() / "commands"
    if src_cmd_claude.exists():
        console.print(f"正在複製 Commands 到 {dst_cmd_claude}...")
        if dst_cmd_claude.exists():
            shutil.copytree(src_cmd_claude, dst_cmd_claude, dirs_exist_ok=True)

    src_cmd_antigravity = get_custom_skills_dir() / "command" / "antigravity"
    dst_cmd_antigravity = get_antigravity_config_dir() / "global_workflows"
    if src_cmd_antigravity.exists():
        console.print(f"正在複製 Workflows 到 {dst_cmd_antigravity}...")
        shutil.copytree(src_cmd_antigravity, dst_cmd_antigravity, dirs_exist_ok=True)

    # --------------------------------------------------------
    # 6. Agents
    # --------------------------------------------------------
    src_agent_opencode = get_custom_skills_dir() / "agent" / "opencode"
    dst_agent_opencode = get_opencode_config_dir() / "agent"
    if src_agent_opencode.exists():
        console.print(f"正在複製 Agents 到 {dst_agent_opencode}...")
        shutil.copytree(src_agent_opencode, dst_agent_opencode, dirs_exist_ok=True)

    # --------------------------------------------------------
    # 7. 專案目錄 (開發環境)
    # --------------------------------------------------------
    project_root = get_project_root()
    if (project_root / ".git").exists() and (project_root / "pyproject.toml").exists():
        console.print(f"[bold yellow]偵測到專案目錄：{project_root}[/bold yellow]")

        # UDS → Project/skills
        dst_project_skills = project_root / "skills"
        if src_uds_claude.exists():
            console.print(f"正在複製從 {src_uds_claude} 到 {dst_project_skills}...")
            dst_project_skills.mkdir(parents=True, exist_ok=True)
            shutil.copytree(src_uds_claude, dst_project_skills, dirs_exist_ok=True)

        clean_unwanted_files(dst_project_skills, use_readonly_handler=True)

        # Obsidian Skills → Project/skills
        if src_obsidian_skills.exists():
            console.print(f"正在複製 Obsidian Skills 到 {dst_project_skills}...")
            shutil.copytree(src_obsidian_skills, dst_project_skills, dirs_exist_ok=True)

        # Commands → Project/command
        src_msg_command = get_custom_skills_dir() / "command"
        dst_project_command = project_root / "command"
        if src_msg_command.exists():
            console.print(f"正在複製從 {src_msg_command} 到 {dst_project_command}...")
            shutil.copytree(src_msg_command, dst_project_command, dirs_exist_ok=True)

        # Agents → Project/agent
        src_msg_agent = get_custom_skills_dir() / "agent"
        dst_project_agent = project_root / "agent"
        if src_msg_agent.exists():
            console.print(f"正在複製從 {src_msg_agent} 到 {dst_project_agent}...")
            shutil.copytree(src_msg_agent, dst_project_agent, dirs_exist_ok=True)
