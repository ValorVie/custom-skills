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


def list_installed_resources(
    target: TargetType | None = None, resource_type: ResourceType | None = None
) -> dict[str, list[dict[str, str]]]:
    """列出已安裝的資源及其來源。

    回傳格式：
    {
        "claude": {
            "skills": [{"name": "foo", "source": "uds"}, ...],
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
            path = get_target_path(t, rt)
            if path and path.exists():
                items = []

                # Skills 是目錄結構
                if rt == "skills":
                    for item in sorted(path.iterdir()):
                        if item.is_dir():
                            source = identify_source(item.name, skill_sources)
                            items.append({"name": item.name, "source": source})
                # Commands, Workflows, Agents 是 .md 檔案
                else:
                    sources_map = {
                        "commands": command_sources,
                        "workflows": workflow_sources,
                        "agents": agent_sources,
                    }
                    sources = sources_map.get(rt, {})

                    for item in sorted(path.iterdir()):
                        if item.is_file() and item.suffix == ".md":
                            name = item.stem
                            source = identify_source(name, sources)
                            items.append({"name": name, "source": source})

                result[t][rt] = items
            else:
                result[t][rt] = []

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
