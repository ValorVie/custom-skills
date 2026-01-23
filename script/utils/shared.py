"""
install 與 maintain 指令的共用函式與配置。
"""

import os
import stat
import errno
import shutil
from pathlib import Path
from typing import Literal

import yaml
from rich.console import Console

from .paths import (
    get_custom_skills_dir,
    get_claude_config_dir,
    get_antigravity_config_dir,
    get_opencode_config_dir,
    get_codex_config_dir,
    get_gemini_cli_config_dir,
    get_superpowers_dir,
    get_uds_dir,
    get_obsidian_skills_dir,
    get_anthropic_skills_dir,
    get_project_root,
)

console = Console()

# 類型定義
TargetType = Literal["claude", "antigravity", "opencode", "codex", "gemini"]
ResourceType = Literal["skills", "commands", "agents", "workflows"]

# ============================================================
# 共用配置
# ============================================================

NPM_PACKAGES = [
    "@fission-ai/openspec@latest",
    "@google/gemini-cli",
    "universal-dev-standards",
    "opencode-ai@latest",
    "skills",
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
    "anthropic_skills": (
        "https://github.com/anthropics/skills.git",
        get_anthropic_skills_dir,
    ),
}

UNWANTED_UDS_FILES = [
    "tdd-assistant",
    "CONTRIBUTING.template.md",
    "install.ps1",
    "install.sh",
    "README.md",
]

# 複製目標配置表：定義各工具的資源目錄
COPY_TARGETS = {
    "claude": {
        "skills": get_claude_config_dir() / "skills",
        "commands": get_claude_config_dir() / "commands",
    },
    "antigravity": {
        "skills": get_antigravity_config_dir() / "skills",
        "workflows": get_antigravity_config_dir() / "global_workflows",
    },
    "opencode": {
        "skills": get_opencode_config_dir() / "skills",
        "commands": get_opencode_config_dir() / "commands",
        "agents": get_opencode_config_dir() / "agent",
    },
    "codex": {
        "skills": get_codex_config_dir() / "skills",
    },
    "gemini": {
        "skills": get_gemini_cli_config_dir() / "skills",
        "commands": get_gemini_cli_config_dir() / "commands",
    },
}


# ============================================================
# Claude Code 安裝檢測
# ============================================================


def check_claude_installed() -> bool:
    """檢查 Claude Code CLI 是否已安裝。"""
    return shutil.which("claude") is not None


def show_claude_install_instructions() -> None:
    """顯示 Claude Code 安裝指引。"""
    console.print()
    console.print("[yellow]⚠️  Claude Code CLI 尚未安裝。[/yellow]")
    console.print()
    console.print("[bold]推薦安裝方式（自動更新）：[/bold]")
    console.print("[cyan]  curl -fsSL https://claude.ai/install.sh | bash[/cyan]")
    console.print()
    console.print("[dim]其他安裝方式：[/dim]")
    console.print("[dim]  - Homebrew (macOS): brew install --cask claude-code[/dim]")
    console.print("[dim]  - WinGet (Windows): winget install Anthropic.ClaudeCode[/dim]")
    console.print("[dim]  - 參考文件: https://code.claude.com/docs[/dim]")
    console.print()


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
# 三階段複製邏輯
# ============================================================


def copy_sources_to_custom_skills() -> None:
    """Stage 2: 將外部來源整合到 custom-skills 目錄。

    來源：
    - UDS skills
    - Obsidian skills
    - Anthropic skill-creator
    """
    console.print("[bold cyan]Stage 2: 整合外部來源到 custom-skills...[/bold cyan]")

    dst_custom = get_custom_skills_dir() / "skills"
    dst_custom.mkdir(parents=True, exist_ok=True)

    # UDS skills
    src_uds = get_uds_dir() / "skills" / "claude-code"
    if src_uds.exists():
        console.print(f"  從 UDS 複製 skills...")
        shutil.copytree(src_uds, dst_custom, dirs_exist_ok=True)
        clean_unwanted_files(dst_custom)

    # Obsidian skills
    src_obsidian = get_obsidian_skills_dir() / "skills"
    if src_obsidian.exists():
        console.print(f"  從 obsidian-skills 複製 skills...")
        shutil.copytree(src_obsidian, dst_custom, dirs_exist_ok=True)

    # Anthropic skill-creator
    src_anthropic = get_anthropic_skills_dir() / "skills" / "skill-creator"
    if src_anthropic.exists():
        dst_skill_creator = dst_custom / "skill-creator"
        console.print(f"  從 anthropic-skills 複製 skill-creator...")
        shutil.copytree(src_anthropic, dst_skill_creator, dirs_exist_ok=True)


def copy_custom_skills_to_targets(sync_project: bool = True) -> None:
    """Stage 3: 將 custom-skills 分發到各工具目錄。

    Args:
        sync_project: 是否同步到專案目錄（預設為 True）
    """
    console.print("[bold cyan]Stage 3: 分發到各工具目錄...[/bold cyan]")

    # 來源路徑
    src_skills = get_custom_skills_dir() / "skills"
    src_cmd_claude = get_custom_skills_dir() / "command" / "claude"
    src_cmd_antigravity = get_custom_skills_dir() / "command" / "antigravity"
    src_cmd_opencode = get_custom_skills_dir() / "command" / "opencode"
    src_cmd_gemini = get_custom_skills_dir() / "command" / "gemini"
    src_agent_opencode = get_custom_skills_dir() / "agent" / "opencode"

    # 1. Claude Code
    dst_claude_skills = COPY_TARGETS["claude"]["skills"]
    dst_claude_commands = COPY_TARGETS["claude"]["commands"]
    if src_skills.exists():
        console.print(f"  複製 skills 到 Claude Code...")
        dst_claude_skills.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src_skills, dst_claude_skills, dirs_exist_ok=True)
    if src_cmd_claude.exists():
        console.print(f"  複製 commands 到 Claude Code...")
        dst_claude_commands.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src_cmd_claude, dst_claude_commands, dirs_exist_ok=True)

    # 2. Antigravity
    dst_antigravity_skills = COPY_TARGETS["antigravity"]["skills"]
    dst_antigravity_workflows = COPY_TARGETS["antigravity"]["workflows"]
    if src_skills.exists():
        console.print(f"  複製 skills 到 Antigravity...")
        dst_antigravity_skills.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src_skills, dst_antigravity_skills, dirs_exist_ok=True)
    if src_cmd_antigravity.exists():
        console.print(f"  複製 workflows 到 Antigravity...")
        dst_antigravity_workflows.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src_cmd_antigravity, dst_antigravity_workflows, dirs_exist_ok=True)

    # 3. OpenCode（新增完整支援）
    dst_opencode_skills = COPY_TARGETS["opencode"]["skills"]
    dst_opencode_commands = COPY_TARGETS["opencode"]["commands"]
    dst_opencode_agents = COPY_TARGETS["opencode"]["agents"]
    if src_skills.exists():
        console.print(f"  複製 skills 到 OpenCode...")
        dst_opencode_skills.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src_skills, dst_opencode_skills, dirs_exist_ok=True)
    if src_cmd_opencode.exists():
        console.print(f"  複製 commands 到 OpenCode...")
        dst_opencode_commands.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src_cmd_opencode, dst_opencode_commands, dirs_exist_ok=True)
    if src_agent_opencode.exists():
        console.print(f"  複製 agents 到 OpenCode...")
        dst_opencode_agents.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src_agent_opencode, dst_opencode_agents, dirs_exist_ok=True)

    # 4. Codex
    dst_codex_skills = COPY_TARGETS["codex"]["skills"]
    if src_skills.exists():
        console.print(f"  複製 skills 到 Codex...")
        dst_codex_skills.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src_skills, dst_codex_skills, dirs_exist_ok=True)

    # 5. Gemini CLI
    dst_gemini_skills = COPY_TARGETS["gemini"]["skills"]
    dst_gemini_commands = COPY_TARGETS["gemini"]["commands"]
    if src_skills.exists():
        console.print(f"  複製 skills 到 Gemini CLI...")
        dst_gemini_skills.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src_skills, dst_gemini_skills, dirs_exist_ok=True)
    if src_cmd_gemini.exists():
        console.print(f"  複製 commands 到 Gemini CLI...")
        dst_gemini_commands.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src_cmd_gemini, dst_gemini_commands, dirs_exist_ok=True)

    # 6. 專案目錄同步
    if sync_project:
        _sync_to_project_directory(src_skills)


def _sync_to_project_directory(src_skills: Path) -> None:
    """同步資源到專案目錄（內部函式）。"""
    project_root = get_project_root()

    # 檢查是否在有效專案目錄中
    if not ((project_root / ".git").exists() and (project_root / "pyproject.toml").exists()):
        return

    console.print(f"[bold yellow]  偵測到專案目錄：{project_root}[/bold yellow]")

    # Skills → Project
    if src_skills.exists():
        dst_project_skills = project_root / "skills"
        console.print(f"  複製 skills 到專案目錄...")
        dst_project_skills.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src_skills, dst_project_skills, dirs_exist_ok=True)
        clean_unwanted_files(dst_project_skills, use_readonly_handler=True)

    # Commands → Project
    src_command = get_custom_skills_dir() / "command"
    if src_command.exists():
        dst_project_command = project_root / "command"
        console.print(f"  複製 commands 到專案目錄...")
        shutil.copytree(src_command, dst_project_command, dirs_exist_ok=True)

    # Agents → Project
    src_agent_all = get_custom_skills_dir() / "agent"
    if src_agent_all.exists():
        dst_project_agent = project_root / "agent"
        console.print(f"  複製 agents 到專案目錄...")
        shutil.copytree(src_agent_all, dst_project_agent, dirs_exist_ok=True)


def copy_skills(sync_project: bool = True) -> None:
    """複製 Skills 從來源到目標目錄（三階段流程）。

    三階段流程：
    1. Stage 1: Clone 外部套件（由 install/update 指令處理）
    2. Stage 2: 整合到 custom-skills
    3. Stage 3: 分發到各工具目錄

    Args:
        sync_project: 是否同步到專案目錄（預設為 True）
    """
    # Stage 2: 整合外部來源
    copy_sources_to_custom_skills()

    # Stage 3: 分發到目標目錄
    copy_custom_skills_to_targets(sync_project=sync_project)


# ============================================================
# Disabled 目錄管理
# ============================================================


def get_disabled_base_dir() -> Path:
    """取得 disabled 目錄的基礎路徑。"""
    return get_custom_skills_dir() / "disabled"


def get_disabled_path(target: TargetType, resource_type: ResourceType, name: str) -> Path:
    """取得特定資源在 disabled 目錄中的路徑。

    Args:
        target: 目標工具 (claude, antigravity, opencode)
        resource_type: 資源類型 (skills, commands, agents, workflows)
        name: 資源名稱

    Returns:
        Path: disabled 目錄中的完整路徑
    """
    return get_disabled_base_dir() / target / resource_type / name


def get_resource_file_path(
    target: TargetType, resource_type: ResourceType, name: str
) -> Path | None:
    """取得資源在目標工具目錄中的完整路徑（包含副檔名）。

    Args:
        target: 目標工具
        resource_type: 資源類型
        name: 資源名稱

    Returns:
        Path | None: 完整路徑，若目標路徑不存在則回傳 None
    """
    base_path = get_target_path(target, resource_type)
    if not base_path:
        return None

    # Skills 是目錄，其他是 .md 檔案
    if resource_type == "skills":
        return base_path / name
    else:
        return base_path / f"{name}.md"


def show_restart_reminder(target: TargetType) -> None:
    """顯示重啟提醒訊息。

    Args:
        target: 目標工具 (claude, antigravity, opencode, codex, gemini)
    """
    reminders = {
        "claude": """
⚠️  請重啟 Claude Code 以套用變更

重啟方式：
  1. 輸入 exit 離開 Claude Code
  2. 重新執行 claude 指令
""",
        "antigravity": """
⚠️  請重啟 Antigravity 以套用變更

重啟方式：
  1. 關閉 VSCode
  2. 重新開啟 VSCode
""",
        "opencode": """
⚠️  請重啟 OpenCode 以套用變更

重啟方式：
  1. 輸入 exit 離開 OpenCode
  2. 重新執行 opencode 指令
""",
        "codex": """
⚠️  請重啟 Codex CLI 以套用變更

重啟方式：
  1. 輸入 exit 離開 Codex
  2. 重新執行 codex 指令
""",
        "gemini": """
⚠️  請重啟 Gemini CLI 以套用變更

重啟方式：
  1. 輸入 exit 離開 Gemini CLI
  2. 重新執行 gemini 指令
""",
    }

    reminder = reminders.get(target)
    if reminder:
        console.print(f"[yellow]{reminder}[/yellow]")


def disable_resource(
    target: TargetType, resource_type: ResourceType, name: str
) -> bool:
    """停用資源：將檔案從目標工具目錄複製到 disabled 目錄，再刪除原檔案。

    Args:
        target: 目標工具 (claude, antigravity, opencode)
        resource_type: 資源類型 (skills, commands, agents, workflows)
        name: 資源名稱

    Returns:
        bool: True 表示成功，False 表示失敗
    """
    # 1. 取得來源路徑
    source_path = get_resource_file_path(target, resource_type, name)
    if not source_path:
        console.print(f"[red]無法取得 {target}/{resource_type} 的路徑[/red]")
        return False

    # 2. 檢查來源是否存在
    if not source_path.exists():
        console.print(f"[red]資源 {name} 不存在，無法停用[/red]")
        return False

    # 3. 取得 disabled 路徑
    if resource_type == "skills":
        disabled_path = get_disabled_path(target, resource_type, name)
    else:
        disabled_path = get_disabled_path(target, resource_type, f"{name}.md")

    # 4. 確保 disabled 目錄存在
    disabled_path.parent.mkdir(parents=True, exist_ok=True)

    # 5. 若目標已存在，先移除
    if disabled_path.exists():
        if disabled_path.is_dir():
            shutil.rmtree(disabled_path)
        else:
            disabled_path.unlink()

    # 6. 複製後刪除（先複製到 disabled，確認成功後再刪除原檔案）
    try:
        if source_path.is_dir():
            shutil.copytree(source_path, disabled_path)
        else:
            shutil.copy2(source_path, disabled_path)
    except Exception as e:
        console.print(f"[red]複製檔案失敗：{e}[/red]")
        return False

    # 複製成功後刪除原檔案
    try:
        if source_path.is_dir():
            shutil.rmtree(source_path)
        else:
            source_path.unlink()
    except Exception as e:
        console.print(f"[red]刪除原檔案失敗：{e}[/red]")
        # 複製已成功，繼續執行

    # 7. 更新 toggle-config.yaml
    config = load_toggle_config()
    if target not in config:
        config[target] = {}
    if resource_type not in config[target]:
        config[target][resource_type] = {"enabled": True, "disabled": []}
    disabled_list = config[target][resource_type].get("disabled", [])
    if name not in disabled_list:
        disabled_list.append(name)
    config[target][resource_type]["disabled"] = disabled_list
    save_toggle_config(config)

    console.print(f"[yellow]已停用 {target}/{resource_type}/{name}[/yellow]")

    # 8. 顯示重啟提醒
    show_restart_reminder(target)

    return True


def enable_resource(
    target: TargetType, resource_type: ResourceType, name: str
) -> bool:
    """啟用資源：將檔案從 disabled 目錄複製回目標工具目錄，再刪除 disabled 中的檔案。

    Args:
        target: 目標工具 (claude, antigravity, opencode)
        resource_type: 資源類型 (skills, commands, agents, workflows)
        name: 資源名稱

    Returns:
        bool: True 表示成功，False 表示失敗
    """
    # 1. 取得 disabled 路徑
    if resource_type == "skills":
        disabled_path = get_disabled_path(target, resource_type, name)
    else:
        disabled_path = get_disabled_path(target, resource_type, f"{name}.md")

    # 2. 取得目標路徑
    target_path = get_resource_file_path(target, resource_type, name)
    if not target_path:
        console.print(f"[red]無法取得 {target}/{resource_type} 的路徑[/red]")
        return False

    # 3. 確保目標目錄存在
    target_path.parent.mkdir(parents=True, exist_ok=True)

    # 4. 檢查 disabled 目錄中是否存在
    if disabled_path.exists():
        # 若目標已存在，先移除
        if target_path.exists():
            if target_path.is_dir():
                shutil.rmtree(target_path)
            else:
                target_path.unlink()

        # 複製後刪除（先複製回目標目錄，確認成功後再刪除 disabled 中的檔案）
        try:
            if disabled_path.is_dir():
                shutil.copytree(disabled_path, target_path)
            else:
                shutil.copy2(disabled_path, target_path)
        except Exception as e:
            console.print(f"[red]複製檔案失敗：{e}[/red]")
            return False

        # 複製成功後刪除 disabled 中的檔案
        try:
            if disabled_path.is_dir():
                shutil.rmtree(disabled_path)
            else:
                disabled_path.unlink()
        except Exception as e:
            console.print(f"[red]刪除 disabled 檔案失敗：{e}[/red]")
            # 複製已成功，繼續執行
    else:
        # disabled 中不存在，從來源重新複製
        console.print(f"[dim]disabled 目錄中不存在 {name}，嘗試從來源重新複製...[/dim]")
        if not copy_single_resource(target, resource_type, name):
            console.print(f"[red]無法找到資源 {name} 的來源[/red]")
            return False

    # 5. 更新 toggle-config.yaml（移除 disabled 記錄）
    config = load_toggle_config()
    if target in config and resource_type in config[target]:
        disabled_list = config[target][resource_type].get("disabled", [])
        if name in disabled_list:
            disabled_list.remove(name)
        config[target][resource_type]["disabled"] = disabled_list
        save_toggle_config(config)

    console.print(f"[green]已啟用 {target}/{resource_type}/{name}[/green]")

    # 6. 顯示重啟提醒
    show_restart_reminder(target)

    return True


def copy_single_resource(
    target: TargetType, resource_type: ResourceType, name: str
) -> bool:
    """從來源複製單一資源到目標目錄。

    Args:
        target: 目標工具
        resource_type: 資源類型
        name: 資源名稱

    Returns:
        bool: True 表示成功，False 表示失敗
    """
    target_path = get_resource_file_path(target, resource_type, name)
    if not target_path:
        return False

    # 根據資源類型尋找來源
    if resource_type == "skills":
        # Skills 來源：UDS, Obsidian, Anthropic, Custom
        sources = [
            get_uds_dir() / "skills" / "claude-code" / name,
            get_obsidian_skills_dir() / "skills" / name,
            get_custom_skills_dir() / "skills" / name,
        ]
        if name == "skill-creator":
            sources.insert(0, get_anthropic_skills_dir() / "skills" / "skill-creator")

        for src in sources:
            if src.exists() and src.is_dir():
                target_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copytree(src, target_path, dirs_exist_ok=True)
                return True

    elif resource_type == "commands":
        # Commands 來源：custom-skills/command/claude
        src = get_custom_skills_dir() / "command" / "claude" / f"{name}.md"
        if src.exists():
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, target_path)
            return True

    elif resource_type == "workflows":
        # Workflows 來源：custom-skills/command/antigravity
        src = get_custom_skills_dir() / "command" / "antigravity" / f"{name}.md"
        if src.exists():
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, target_path)
            return True

    elif resource_type == "agents":
        # Agents 來源：custom-skills/agent/opencode
        src = get_custom_skills_dir() / "agent" / "opencode" / f"{name}.md"
        if src.exists():
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, target_path)
            return True

    return False


# ============================================================
# Toggle 配置管理
# ============================================================

TOGGLE_CONFIG_PATH = get_custom_skills_dir() / "toggle-config.yaml"

DEFAULT_TOGGLE_CONFIG = {
    "claude": {
        "skills": {"enabled": True, "disabled": []},
        "commands": {"enabled": True, "disabled": []},
    },
    "antigravity": {
        "skills": {"enabled": True, "disabled": []},
        "workflows": {"enabled": True, "disabled": []},
    },
    "opencode": {
        "skills": {"enabled": True, "disabled": []},
        "commands": {"enabled": True, "disabled": []},
        "agents": {"enabled": True, "disabled": []},
    },
    "codex": {
        "skills": {"enabled": True, "disabled": []},
    },
    "gemini": {
        "skills": {"enabled": True, "disabled": []},
        "commands": {"enabled": True, "disabled": []},
    },
}


def load_toggle_config() -> dict:
    """載入 toggle 配置檔，不存在時回傳預設值。"""
    if not TOGGLE_CONFIG_PATH.exists():
        return DEFAULT_TOGGLE_CONFIG.copy()
    try:
        with open(TOGGLE_CONFIG_PATH, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            if config is None:
                return DEFAULT_TOGGLE_CONFIG.copy()
            # 合併預設值以確保結構完整
            for target, settings in DEFAULT_TOGGLE_CONFIG.items():
                if target not in config:
                    config[target] = settings
                else:
                    for resource_type, defaults in settings.items():
                        if resource_type not in config[target]:
                            config[target][resource_type] = defaults
            return config
    except Exception:
        return DEFAULT_TOGGLE_CONFIG.copy()


def save_toggle_config(config: dict) -> None:
    """儲存 toggle 配置檔。"""
    TOGGLE_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(TOGGLE_CONFIG_PATH, "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


def is_resource_enabled(
    config: dict, target: TargetType, resource_type: ResourceType, name: str
) -> bool:
    """檢查特定資源是否啟用。"""
    target_config = config.get(target, {})
    type_config = target_config.get(resource_type, {"enabled": True, "disabled": []})
    if not type_config.get("enabled", True):
        return False
    disabled_list = type_config.get("disabled", [])
    return name not in disabled_list


# ============================================================
# 資源列表與來源識別
# ============================================================

# 來源名稱映射
SOURCE_NAMES = {
    "uds": "universal-dev-standards",
    "obsidian": "obsidian-skills",
    "anthropic": "anthropic-skills",
    "custom": "custom-skills",
    "user": "user",
}


def get_source_skills() -> dict[str, set[str]]:
    """取得各來源的 skill 名稱集合。"""
    sources = {}

    # UDS skills
    uds_path = get_uds_dir() / "skills" / "claude-code"
    if uds_path.exists():
        sources["uds"] = {d.name for d in uds_path.iterdir() if d.is_dir()}
    else:
        sources["uds"] = set()

    # Obsidian skills
    obsidian_path = get_obsidian_skills_dir() / "skills"
    if obsidian_path.exists():
        sources["obsidian"] = {d.name for d in obsidian_path.iterdir() if d.is_dir()}
    else:
        sources["obsidian"] = set()

    # Anthropic skills
    anthropic_path = get_anthropic_skills_dir() / "skills" / "skill-creator"
    if anthropic_path.exists():
        sources["anthropic"] = {"skill-creator"}
    else:
        sources["anthropic"] = set()

    # Custom skills (本專案)
    custom_path = get_custom_skills_dir() / "skills"
    if custom_path.exists():
        # 排除來自其他來源的
        all_known = sources["uds"] | sources["obsidian"] | sources["anthropic"]
        sources["custom"] = {
            d.name for d in custom_path.iterdir() if d.is_dir() and d.name not in all_known
        }
    else:
        sources["custom"] = set()

    return sources


def identify_source(name: str, sources: dict[str, set[str]]) -> str:
    """識別資源的來源。"""
    for source_key, names in sources.items():
        if name in names:
            return SOURCE_NAMES.get(source_key, source_key)
    return SOURCE_NAMES["user"]


def get_target_path(target: TargetType, resource_type: ResourceType) -> Path | None:
    """取得目標工具的資源路徑。"""
    paths = {
        ("claude", "skills"): get_claude_config_dir() / "skills",
        ("claude", "commands"): get_claude_config_dir() / "commands",
        ("antigravity", "skills"): get_antigravity_config_dir() / "skills",
        ("antigravity", "workflows"): get_antigravity_config_dir() / "global_workflows",
        ("opencode", "skills"): get_opencode_config_dir() / "skills",
        ("opencode", "commands"): get_opencode_config_dir() / "commands",
        ("opencode", "agents"): get_opencode_config_dir() / "agent",
        ("codex", "skills"): get_codex_config_dir() / "skills",
        ("gemini", "skills"): get_gemini_cli_config_dir() / "skills",
        ("gemini", "commands"): get_gemini_cli_config_dir() / "commands",
    }
    return paths.get((target, resource_type))


def get_source_commands() -> dict[str, set[str]]:
    """取得 commands 的來源名稱集合。"""
    sources = {}

    # Custom commands (本專案)
    custom_cmd_claude = get_custom_skills_dir() / "command" / "claude"
    if custom_cmd_claude.exists():
        sources["custom"] = {
            f.stem for f in custom_cmd_claude.iterdir() if f.is_file() and f.suffix == ".md"
        }
    else:
        sources["custom"] = set()

    return sources


def get_source_workflows() -> dict[str, set[str]]:
    """取得 workflows 的來源名稱集合。"""
    sources = {}

    # Custom workflows (本專案)
    custom_wf = get_custom_skills_dir() / "command" / "antigravity"
    if custom_wf.exists():
        sources["custom"] = {
            f.stem for f in custom_wf.iterdir() if f.is_file() and f.suffix == ".md"
        }
    else:
        sources["custom"] = set()

    return sources


def get_source_agents() -> dict[str, set[str]]:
    """取得 agents 的來源名稱集合。"""
    sources = {}

    # Custom agents (本專案)
    custom_agent = get_custom_skills_dir() / "agent" / "opencode"
    if custom_agent.exists():
        sources["custom"] = {
            f.stem for f in custom_agent.iterdir() if f.is_file() and f.suffix == ".md"
        }
    else:
        sources["custom"] = set()

    return sources


def list_disabled_resources(
    target: TargetType, resource_type: ResourceType
) -> list[str]:
    """列出 disabled 目錄中的資源名稱。

    Args:
        target: 目標工具
        resource_type: 資源類型

    Returns:
        list[str]: 被停用的資源名稱列表
    """
    disabled_path = get_disabled_base_dir() / target / resource_type
    if not disabled_path.exists():
        return []

    names = []
    if resource_type == "skills":
        # Skills 是目錄
        for item in disabled_path.iterdir():
            if item.is_dir():
                names.append(item.name)
    else:
        # Commands, Workflows, Agents 是 .md 檔案
        for item in disabled_path.iterdir():
            if item.is_file() and item.suffix == ".md":
                names.append(item.stem)

    return sorted(names)


def list_installed_resources(
    target: TargetType | None = None, resource_type: ResourceType | None = None
) -> dict[str, list[dict[str, str]]]:
    """列出已安裝的資源及其來源（包含被停用的資源）。

    回傳格式：
    {
        "claude": {
            "skills": [{"name": "foo", "source": "uds", "disabled": False}, ...],
            "commands": [...],
        },
        ...
    }
    """
    skill_sources = get_source_skills()
    command_sources = get_source_commands()
    workflow_sources = get_source_workflows()
    agent_sources = get_source_agents()

    result = {}

    targets = [target] if target else ["claude", "antigravity", "opencode", "codex", "gemini"]
    type_mapping = {
        "claude": ["skills", "commands"],
        "antigravity": ["skills", "workflows"],
        "opencode": ["skills", "commands", "agents"],
        "codex": ["skills"],
        "gemini": ["skills", "commands"],
    }

    for t in targets:
        result[t] = {}
        types = [resource_type] if resource_type else type_mapping.get(t, [])

        for rt in types:
            items = []
            seen_names = set()

            # 1. 先列出啟用中的資源（目標目錄）
            path = get_target_path(t, rt)
            if path and path.exists():
                # Skills 是目錄結構
                if rt == "skills":
                    for item in path.iterdir():
                        # 過濾隱藏目錄（如 .system）
                        if item.is_dir() and not item.name.startswith("."):
                            source = identify_source(item.name, skill_sources)
                            items.append({
                                "name": item.name,
                                "source": source,
                                "disabled": False,
                            })
                            seen_names.add(item.name)
                # Commands, Workflows, Agents 是 .md 檔案
                else:
                    sources_map = {
                        "commands": command_sources,
                        "workflows": workflow_sources,
                        "agents": agent_sources,
                    }
                    sources = sources_map.get(rt, {})

                    for item in path.iterdir():
                        if item.is_file() and item.suffix == ".md":
                            name = item.stem
                            source = identify_source(name, sources)
                            items.append({
                                "name": name,
                                "source": source,
                                "disabled": False,
                            })
                            seen_names.add(name)

            # 2. 再列出被停用的資源（disabled 目錄）
            disabled_names = list_disabled_resources(t, rt)
            for name in disabled_names:
                if name not in seen_names:
                    if rt == "skills":
                        source = identify_source(name, skill_sources)
                    else:
                        sources_map = {
                            "commands": command_sources,
                            "workflows": workflow_sources,
                            "agents": agent_sources,
                        }
                        sources = sources_map.get(rt, {})
                        source = identify_source(name, sources)

                    items.append({
                        "name": name,
                        "source": source,
                        "disabled": True,
                    })

            # 排序：先依啟用狀態（啟用在前），再依名稱
            items.sort(key=lambda x: (x["disabled"], x["name"]))
            result[t][rt] = items

    return result


def get_all_skill_names() -> list[str]:
    """取得所有已安裝的 skill 名稱（用於重複名稱警告）。"""
    sources = get_source_skills()
    all_names = set()
    for names in sources.values():
        all_names.update(names)
    return sorted(all_names)


def show_skills_npm_hint() -> None:
    """顯示 npx skills 可用指令提示。"""
    console.print()
    console.print("[cyan]💡 第三方 Skills 管理（使用 npx skills）：[/cyan]")
    console.print("   可用指令：")
    console.print("   - npx skills add <package>      安裝 skill 套件")
    console.print("   - npx skills a <package>        同上（別名）")
    console.print("   - npx skills install <package>  同上（別名）")
    console.print("   - npx skills i <package>        同上（別名）")
    console.print()
    console.print("   計畫中：")
    console.print("   - npx skills find <query>       搜尋 skills")
    console.print("   - npx skills update             更新已安裝的 skills")
    console.print()
    console.print("   範例：npx skills add vercel-labs/agent-skills")


# ============================================================
# MCP Config 路徑管理
# ============================================================


def get_mcp_config_path(target: TargetType) -> tuple[Path, bool]:
    """取得各工具的 MCP 設定檔路徑。

    Args:
        target: 目標工具 (claude, antigravity, opencode, codex, gemini)

    Returns:
        tuple[Path, bool]: (設定檔路徑, 檔案是否存在)
    """
    home = Path.home()

    paths = {
        "claude": home / ".claude.json",
        "antigravity": home / ".gemini" / "antigravity" / "mcp_config.json",
        "opencode": home / ".config" / "opencode" / "opencode.json",
        "codex": home / ".codex" / "config.json",
        "gemini": home / ".gemini" / "settings.json",
    }

    path = paths.get(target, home / ".claude.json")
    return path, path.exists()


def open_in_editor(file_path: Path) -> bool:
    """在外部編輯器中開啟檔案。

    優先順序：
    1. 環境變數 EDITOR 指定的編輯器
    2. VS Code (code)
    3. 系統預設開啟方式 (open on macOS, xdg-open on Linux)

    Args:
        file_path: 要開啟的檔案路徑

    Returns:
        bool: True 表示成功啟動編輯器，False 表示失敗
    """
    import subprocess
    import platform

    # 1. 嘗試使用 EDITOR 環境變數
    editor = os.environ.get("EDITOR")
    if editor:
        try:
            subprocess.Popen([editor, str(file_path)])
            return True
        except Exception:
            pass

    # 2. 嘗試使用 VS Code
    try:
        subprocess.Popen(["code", str(file_path)])
        return True
    except Exception:
        pass

    # 3. 使用系統預設開啟方式
    system = platform.system()
    try:
        if system == "Darwin":  # macOS
            subprocess.Popen(["open", str(file_path)])
            return True
        elif system == "Linux":
            subprocess.Popen(["xdg-open", str(file_path)])
            return True
        elif system == "Windows":
            subprocess.Popen(["start", "", str(file_path)], shell=True)
            return True
    except Exception:
        pass

    return False


def open_in_file_manager(file_path: Path) -> bool:
    """在檔案管理器中開啟檔案所在目錄（並選取該檔案）。

    Args:
        file_path: 要開啟的檔案路徑

    Returns:
        bool: True 表示成功啟動檔案管理器，False 表示失敗
    """
    import subprocess
    import platform

    system = platform.system()
    try:
        if system == "Darwin":  # macOS Finder
            # -R 選項會在 Finder 中顯示並選取檔案
            subprocess.Popen(["open", "-R", str(file_path)])
            return True
        elif system == "Linux":
            # 嘗試使用 nautilus 或 xdg-open
            parent_dir = file_path.parent
            try:
                subprocess.Popen(["nautilus", "--select", str(file_path)])
                return True
            except Exception:
                subprocess.Popen(["xdg-open", str(parent_dir)])
                return True
        elif system == "Windows":
            # Explorer 的 /select 選項會選取檔案
            subprocess.Popen(["explorer", "/select,", str(file_path)])
            return True
    except Exception:
        pass

    return False
