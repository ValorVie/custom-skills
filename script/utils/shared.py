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

from utils.paths import (
    get_custom_skills_dir,
    get_claude_config_dir,
    get_antigravity_config_dir,
    get_opencode_config_dir,
    get_superpowers_dir,
    get_uds_dir,
    get_obsidian_skills_dir,
    get_anthropic_skills_dir,
    get_project_root,
)

console = Console()

# 類型定義
TargetType = Literal["claude", "antigravity", "opencode"]
ResourceType = Literal["skills", "commands", "agents", "workflows"]

# ============================================================
# 共用配置
# ============================================================

NPM_PACKAGES = [
    "@anthropic-ai/claude-code",
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
    src_anthropic = get_anthropic_skills_dir() / "skills" / "skill-creator"
    src_custom = get_custom_skills_dir() / "skills"

    # 目標路徑
    dst_custom = get_custom_skills_dir() / "skills"
    dst_claude = get_claude_config_dir() / "skills"
    dst_antigravity = get_antigravity_config_dir() / "skills"

    # 1. UDS + Obsidian + Anthropic → Custom Skills (統一來源)
    copy_tree_if_exists(
        src_uds, dst_custom, f"正在複製... 從... 從 {src_uds} 到 {dst_custom}..."
    )
    clean_unwanted_files(dst_custom)
    copy_tree_if_exists(
        src_obsidian, dst_custom, f"正在複製... 從 {src_obsidian} 到 {dst_custom}..."
    )
    copy_tree_if_exists(
        src_anthropic,
        dst_custom / "skill-creator",
        f"正在複製... 從 {src_anthropic} 到 {dst_custom / 'skill-creator'}...",
    )

    # 2. UDS + Obsidian + Anthropic → Claude Code
    copy_tree_if_exists(
        src_uds, dst_claude, f"正在複製... 從... 從 {src_uds} 到 {dst_claude}..."
    )
    clean_unwanted_files(dst_claude)
    copy_tree_if_exists(
        src_obsidian, dst_claude, f"正在複製... 從 {src_obsidian} 到 {dst_claude}..."
    )
    copy_tree_if_exists(
        src_anthropic,
        dst_claude / "skill-creator",
        f"正在複製... 從 {src_anthropic} 到 {dst_claude / 'skill-creator'}...",
    )

    # 3. Custom Skills + Obsidian + Anthropic → Antigravity
    copy_tree_if_exists(
        src_custom,
        dst_antigravity,
        f"正在複製... 從... 從 {src_custom} 到 {dst_antigravity}...",
    )
    copy_tree_if_exists(
        src_obsidian,
        dst_antigravity,
        f"正在複製... 從 {src_obsidian} 到 {dst_antigravity}...",
    )
    copy_tree_if_exists(
        src_anthropic,
        dst_antigravity / "skill-creator",
        f"正在複製... 從 {src_anthropic} 到 {dst_antigravity / 'skill-creator'}...",
    )

    # 4. Commands
    src_cmd_claude = get_custom_skills_dir() / "command" / "claude"
    dst_cmd_claude = get_claude_config_dir() / "commands"
    if src_cmd_claude.exists() and dst_cmd_claude.exists():
        console.print(f"正在複製... 從 Commands 到 {dst_cmd_claude}...")
        shutil.copytree(src_cmd_claude, dst_cmd_claude, dirs_exist_ok=True)

    src_cmd_antigravity = get_custom_skills_dir() / "command" / "antigravity"
    dst_cmd_antigravity = get_antigravity_config_dir() / "global_workflows"
    copy_tree_if_exists(
        src_cmd_antigravity,
        dst_cmd_antigravity,
        f"正在複製... 從 Workflows 到 {dst_cmd_antigravity}...",
    )

    # 5. Agents
    src_agent = get_custom_skills_dir() / "agent" / "opencode"
    dst_agent = get_opencode_config_dir() / "agent"
    copy_tree_if_exists(
        src_agent, dst_agent, f"正在複製... 從 Agents 到 {dst_agent}..."
    )

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
        src_uds,
        dst_project_skills,
        f"正在複製... 從... 從 {src_uds} 到 {dst_project_skills}...",
    )
    clean_unwanted_files(dst_project_skills, use_readonly_handler=True)
    copy_tree_if_exists(
        src_obsidian,
        dst_project_skills,
        f"正在複製... 從 {src_obsidian} 到 {dst_project_skills}...",
    )
    copy_tree_if_exists(
        src_anthropic,
        dst_project_skills / "skill-creator",
        f"正在複製... 從 {src_anthropic} 到 {dst_project_skills / 'skill-creator'}...",
    )

    # Commands → Project
    src_command = get_custom_skills_dir() / "command"
    dst_project_command = project_root / "command"
    copy_tree_if_exists(
        src_command,
        dst_project_command,
        f"正在複製... 從... 從 {src_command} 到 {dst_project_command}...",
    )

    # Agents → Project
    src_agent_all = get_custom_skills_dir() / "agent"
    dst_project_agent = project_root / "agent"
    copy_tree_if_exists(
        src_agent_all,
        dst_project_agent,
        f"正在複製... 從... 從 {src_agent_all} 到 {dst_project_agent}...",
    )


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
        target: 目標工具 (claude, antigravity, opencode)
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
        "agents": {"enabled": True, "disabled": []},
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
        ("opencode", "agents"): get_opencode_config_dir() / "agent",
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

    targets = [target] if target else ["claude", "antigravity", "opencode"]
    type_mapping = {
        "claude": ["skills", "commands"],
        "antigravity": ["skills", "workflows"],
        "opencode": ["agents"],
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
                        if item.is_dir():
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
