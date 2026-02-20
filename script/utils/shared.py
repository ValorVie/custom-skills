"""
install 與 maintain 指令的共用函式與配置。
"""

import os
import stat
import errno
import shutil
import difflib
import fnmatch
import json
from datetime import datetime
from pathlib import Path
from typing import Literal

import yaml
from rich.console import Console

from .paths import (
    get_custom_skills_dir,
    get_claude_config_dir,
    get_claude_agents_dir,
    get_claude_workflows_dir,
    get_antigravity_config_dir,
    get_opencode_config_dir,
    get_opencode_plugin_dir,
    get_opencode_superpowers_dir,
    get_codex_config_dir,
    get_gemini_cli_config_dir,
    get_superpowers_dir,
    get_uds_dir,
    get_obsidian_skills_dir,
    get_anthropic_skills_dir,
    get_auto_skill_dir,
    get_project_root,
)
from .system import run_command

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
    "happy-coder",
]

BUN_PACKAGES = [
    "@openai/codex",
]

OPENCODE_SUPERPOWERS_URL = "https://github.com/obra/superpowers.git"


def get_ecc_dir() -> Path:
    """回傳 everything-claude-code 儲存庫的本地路徑。"""
    from .paths import get_config_dir

    return get_config_dir() / "everything-claude-code"


def get_ecc_sources_dir() -> Path:
    """回傳專案內 sources/ecc 目錄的路徑。"""
    return get_project_root() / "sources" / "ecc"


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
    "everything_claude_code": (
        "https://github.com/affaan-m/everything-claude-code.git",
        get_ecc_dir,
    ),
    "auto_skill": (
        "https://github.com/Toolsai/auto-skill.git",
        get_auto_skill_dir,
    ),
}


def sync_opencode_superpowers_repo() -> Path:
    """確保 OpenCode superpowers 儲存庫存在，若有就 pull，否則 clone。"""
    repo_path = get_opencode_superpowers_dir()
    repo_path.parent.mkdir(parents=True, exist_ok=True)

    if (repo_path / ".git").exists():
        console.print(
            f"[green]更新 OpenCode superpowers[/green] → [dim]{shorten_path(repo_path)}[/dim]"
        )
        run_command(["git", "pull"], cwd=str(repo_path), check=False)
    else:
        console.print(
            f"[green]Clone OpenCode superpowers[/green] → [dim]{shorten_path(repo_path)}[/dim]"
        )
        run_command(
            ["git", "clone", OPENCODE_SUPERPOWERS_URL, str(repo_path)], check=False
        )

    return repo_path


def refresh_opencode_superpowers_symlinks(repo_path: Path) -> bool:
    """建立或刷新 OpenCode superpowers 的 plugin/skills symlink。"""
    plugin_src = repo_path / ".opencode" / "plugins" / "superpowers.js"
    skills_src = repo_path / "skills"
    plugin_dst = get_opencode_plugin_dir() / "superpowers.js"
    skills_dst = get_opencode_config_dir() / "skills" / "superpowers"

    if not plugin_src.exists() or not skills_src.exists():
        console.print("[red]✗ 找不到 superpowers 原始檔，請確認儲存庫內容[/red]")
        return False

    plugin_dst.parent.mkdir(parents=True, exist_ok=True)
    skills_dst.parent.mkdir(parents=True, exist_ok=True)

    def _clean(path: Path):
        # Windows 目錄 junction/symlink 可能無法被 is_symlink()/os.path.islink() 偵測，
        # 但 shutil.rmtree 內部會用 FILE_ATTRIBUTE_REPARSE_POINT 偵測並拒絕操作。
        # 因此對存在的路徑，先嘗試 unlink（處理 symlink/junction/file），
        # 失敗才 fallback 到 rmtree（處理真實目錄）。
        if not path.exists() and not path.is_symlink():
            return
        try:
            path.unlink()
        except (OSError, PermissionError):
            shutil.rmtree(path)

    _clean(plugin_dst)
    _clean(skills_dst)

    try:
        os.symlink(plugin_src, plugin_dst)
        os.symlink(skills_src, skills_dst)
        method = "symlink"
    except OSError:
        # Windows 無 symlink 權限時 fallback 為複製
        try:
            shutil.copy2(plugin_src, plugin_dst)
            if skills_src.is_dir():
                shutil.copytree(skills_src, skills_dst)
            else:
                shutil.copy2(skills_src, skills_dst)
            method = "copy"
        except OSError as e:
            console.print(f"[red]✗ 建立連結失敗：{e}[/red]")
            return False

    if method == "symlink":
        console.print("[green]✓[/green] OpenCode superpowers symlink 已更新")
    else:
        console.print(
            "[green]✓[/green] OpenCode superpowers 已複製"
            "（無 symlink 權限，使用檔案複製）"
        )
    console.print(f"[dim]驗證：[/dim] ls -l {shorten_path(plugin_dst)}")
    console.print(f"[dim]驗證：[/dim] ls -l {shorten_path(skills_dst)}")
    return True


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
        "agents": get_claude_agents_dir(),
        "workflows": get_claude_workflows_dir(),
    },
    "antigravity": {
        "skills": get_antigravity_config_dir() / "global_skills",
        "workflows": get_antigravity_config_dir() / "global_workflows",
    },
    "opencode": {
        "skills": get_opencode_config_dir() / "skills",
        "commands": get_opencode_config_dir() / "commands",
        "agents": get_opencode_config_dir() / "agents",
        "plugins": get_opencode_plugin_dir(),
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


def get_claude_install_type() -> str | None:
    """判斷 Claude Code 的安裝方式。

    Returns:
        "npm": 透過 npm 全域安裝
        "native": 透過 native 方式安裝（curl / Homebrew / WinGet）
        None: 未安裝
    """
    import subprocess

    claude_path = shutil.which("claude")
    if not claude_path:
        return None

    # 檢查是否透過 npm 安裝
    try:
        result = subprocess.run(
            ["npm", "list", "-g", "@anthropic-ai/claude-code", "--depth=0"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0 and "@anthropic-ai/claude-code" in result.stdout:
            return "npm"
    except Exception:
        pass

    # 如果 npm 找不到，視為 native 安裝
    return "native"


def update_claude_code() -> None:
    """根據安裝方式更新 Claude Code。"""
    from .system import run_command

    install_type = get_claude_install_type()

    if install_type is None:
        console.print("[yellow]⚠️  Claude Code CLI 尚未安裝[/yellow]")
        show_claude_install_instructions()
        return

    if install_type == "npm":
        console.print("[bold cyan]正在更新 Claude Code (npm)...[/bold cyan]")
        run_command(["npm", "install", "-g", "@anthropic-ai/claude-code@latest"])
        # 提醒切換到 native 安裝
        console.print()
        console.print("[yellow]💡 建議切換到 native 安裝方式以獲得自動更新：[/yellow]")
        console.print(
            "[dim]   1. 移除 npm 版本: npm uninstall -g @anthropic-ai/claude-code[/dim]"
        )
        console.print(
            "[dim]   2. 安裝 native 版本: curl -fsSL https://claude.ai/install.sh | bash[/dim]"
        )
        console.print()
    else:
        # native 安裝使用 claude update 強制更新
        console.print("[bold cyan]正在更新 Claude Code (native)...[/bold cyan]")
        result = run_command(["claude", "update"], check=False)
        if result and result.returncode == 0:
            console.print("[green]✓ Claude Code (native) - 更新完成[/green]")
        else:
            console.print("[green]✓ Claude Code (native) - 已是最新版本[/green]")


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
    console.print(
        "[dim]  - WinGet (Windows): winget install Anthropic.ClaudeCode[/dim]"
    )
    console.print("[dim]  - 參考文件: https://code.claude.com/docs[/dim]")
    console.print()


def show_claude_status() -> None:
    """顯示 Claude Code 的安裝狀態（用於 install 流程）。"""
    install_type = get_claude_install_type()

    if install_type is None:
        show_claude_install_instructions()
    elif install_type == "npm":
        console.print("[yellow]⚠️  Claude Code (npm) 已安裝[/yellow]")
        console.print("[dim]   建議切換到 native 安裝以獲得自動更新功能[/dim]")
    else:
        console.print("[green]✓ Claude Code (native) 已安裝[/green]")


# ============================================================
# NPM 套件檢查
# ============================================================


def get_npm_package_version(package_name: str) -> str | None:
    """檢查 NPM 套件是否已全域安裝，並回傳版本號。

    Args:
        package_name: NPM 套件名稱（可包含 @latest 等版本標籤）

    Returns:
        str | None: 已安裝的版本號，未安裝則回傳 None
    """
    import subprocess

    # 移除版本標籤（如 @latest）
    clean_name = package_name.split("@")[0] if "@" in package_name else package_name
    # 處理 scoped packages（如 @google/gemini-cli）
    if package_name.startswith("@"):
        parts = package_name.split("/")
        if len(parts) >= 2:
            # @scope/name@version -> @scope/name
            clean_name = f"{parts[0]}/{parts[1].split('@')[0]}"

    try:
        result = subprocess.run(
            ["npm", "list", "-g", clean_name, "--depth=0", "--json"],
            capture_output=True,
            text=True,
            timeout=15,
            shell=True,  # Windows 需要
        )
        if result.returncode == 0:
            import json

            data = json.loads(result.stdout)
            deps = data.get("dependencies", {})
            if clean_name in deps:
                return deps[clean_name].get("version", "installed")
    except Exception:
        pass

    return None


def check_uds_initialized() -> bool:
    """檢查當前目錄是否已初始化 universal-dev-standards。

    Returns:
        bool: True 表示已初始化（存在 .standards 目錄）
    """
    from pathlib import Path

    cwd = Path.cwd()
    return (cwd / ".standards").exists()


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


def shorten_path(path: Path) -> str:
    """將路徑中的 home 目錄替換為 ~，使顯示更簡潔。"""
    home = str(Path.home())
    path_str = str(path)
    if path_str.startswith(home):
        return path_str.replace(home, "~", 1)
    return path_str


def copy_tree_if_exists(src: Path, dst: Path, msg: str):
    """若來源存在，複製目錄樹到目標位置。"""
    if src.exists():
        console.print(msg)
        dst.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src, dst, dirs_exist_ok=True)
        return True
    return False


# ============================================================
# 分發與整合邏輯
# ============================================================
#
# 流程說明：
# - Stage 1: Clone/Pull 外部套件（由 install/update 指令處理）
# - Stage 3: 分發 ~/.config/custom-skills 到各工具目錄（由 copy_skills 處理）
#
# 注意：Stage 2（整合外部來源到 custom-skills）已移除。
# ~/.config/custom-skills 的內容現由 git repo 控制。
#
# 開發者如需整合外部來源，請使用 integrate_to_dev_project()，
# 該函式會將外部來源整合到開發目錄（非 ~/.config/custom-skills）。
# ============================================================


def copy_sources_to_custom_skills() -> None:
    """[已棄用] 將外部來源整合到 custom-skills 目錄。

    注意：此函式已不再被 copy_skills() 呼叫。
    ~/.config/custom-skills 的內容現由 git repo 控制。
    開發者應使用 integrate_to_dev_project() 來整合外部來源到開發目錄。

    整合來源：
    - UDS (skills, agents, workflows, commands)
    - Obsidian skills
    - Anthropic skill-creator
    """
    console.print("[bold cyan]Stage 2: 整合外部來源到 custom-skills...[/bold cyan]")

    dst_custom = get_custom_skills_dir() / "skills"
    dst_custom.mkdir(parents=True, exist_ok=True)

    # ============================================================
    # UDS 來源 - 主要整合來源
    # ============================================================
    src_uds = get_uds_dir() / "skills" / "claude-code"
    if src_uds.exists():
        console.print(f"  [dim]{shorten_path(src_uds)}[/dim]")
        console.print(f"    → [dim]{shorten_path(dst_custom)}[/dim]")
        # 複製時排除 agents 和 workflows（這些有專門的目的地）
        for item in src_uds.iterdir():
            if item.name in ("agents", "workflows", "commands"):
                continue  # 這些會單獨處理
            dst_item = dst_custom / item.name
            if item.is_dir():
                shutil.copytree(item, dst_item, dirs_exist_ok=True)
            else:
                shutil.copy2(item, dst_item)
        clean_unwanted_files(dst_custom)

    # UDS agents → custom-skills/agents/claude 和 custom-skills/agents/opencode
    src_uds_agents = get_uds_dir() / "skills" / "claude-code" / "agents"
    if src_uds_agents.exists():
        # 複製到 claude
        dst_agents_claude = get_custom_skills_dir() / "agents" / "claude"
        console.print(f"  [dim]{shorten_path(src_uds_agents)}[/dim]")
        console.print(f"    → [dim]{shorten_path(dst_agents_claude)}[/dim]")
        dst_agents_claude.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src_uds_agents, dst_agents_claude, dirs_exist_ok=True)

        # 同時複製到 opencode
        dst_agents_opencode = get_custom_skills_dir() / "agents" / "opencode"
        console.print(f"    → [dim]{shorten_path(dst_agents_opencode)}[/dim]")
        dst_agents_opencode.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src_uds_agents, dst_agents_opencode, dirs_exist_ok=True)

    # UDS workflows → custom-skills/commands/workflows
    src_uds_workflows = get_uds_dir() / "skills" / "claude-code" / "workflows"
    dst_workflows = get_custom_skills_dir() / "commands" / "workflows"
    if src_uds_workflows.exists():
        console.print(f"  [dim]{shorten_path(src_uds_workflows)}[/dim]")
        console.print(f"    → [dim]{shorten_path(dst_workflows)}[/dim]")
        dst_workflows.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src_uds_workflows, dst_workflows, dirs_exist_ok=True)

    # UDS commands → custom-skills/commands/claude（如果存在）
    src_uds_commands = get_uds_dir() / "skills" / "claude-code" / "commands"
    dst_commands = get_custom_skills_dir() / "commands" / "claude"
    if src_uds_commands.exists():
        console.print(f"  [dim]{shorten_path(src_uds_commands)}[/dim]")
        console.print(f"    → [dim]{shorten_path(dst_commands)}[/dim]")
        dst_commands.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src_uds_commands, dst_commands, dirs_exist_ok=True)

    # ============================================================
    # Obsidian skills
    # ============================================================
    src_obsidian = get_obsidian_skills_dir() / "skills"
    if src_obsidian.exists():
        console.print(f"  [dim]{shorten_path(src_obsidian)}[/dim]")
        console.print(f"    → [dim]{shorten_path(dst_custom)}[/dim]")
        shutil.copytree(src_obsidian, dst_custom, dirs_exist_ok=True)

    # ============================================================
    # Anthropic skill-creator
    # ============================================================
    src_anthropic = get_anthropic_skills_dir() / "skills" / "skill-creator"
    if src_anthropic.exists():
        dst_skill_creator = dst_custom / "skill-creator"
        console.print(f"  [dim]{shorten_path(src_anthropic)}[/dim]")
        console.print(f"    → [dim]{shorten_path(dst_skill_creator)}[/dim]")
        shutil.copytree(src_anthropic, dst_skill_creator, dirs_exist_ok=True)

    # ============================================================
    # Auto-Skill（自進化知識系統）
    # ============================================================
    src_auto_skill = get_auto_skill_dir()
    if src_auto_skill.exists() and (src_auto_skill / "SKILL.md").exists():
        dst_auto_skill = dst_custom / "auto-skill"
        console.print(f"  [dim]{shorten_path(src_auto_skill)}[/dim]")
        console.print(f"    → [dim]{shorten_path(dst_auto_skill)}[/dim]")
        shutil.copytree(
            src_auto_skill,
            dst_auto_skill,
            dirs_exist_ok=True,
            ignore=shutil.ignore_patterns(".git", "assets", "README.md"),
        )

    # ============================================================
    # ECC (everything-claude-code) 資源
    # ============================================================
    src_ecc = get_ecc_sources_dir()
    if src_ecc.exists():
        console.print("[bold cyan]  整合 ECC 資源...[/bold cyan]")

        # ECC skills → custom-skills/skills
        src_ecc_skills = src_ecc / "skills"
        if src_ecc_skills.exists():
            console.print(f"  [dim]{shorten_path(src_ecc_skills)}[/dim]")
            console.print(f"    → [dim]{shorten_path(dst_custom)}[/dim]")
            for skill_dir in src_ecc_skills.iterdir():
                if skill_dir.is_dir():
                    dst_skill = dst_custom / skill_dir.name
                    shutil.copytree(skill_dir, dst_skill, dirs_exist_ok=True)

        # ECC agents → custom-skills/agents/claude
        src_ecc_agents = src_ecc / "agents"
        if src_ecc_agents.exists():
            dst_agents_claude = get_custom_skills_dir() / "agents" / "claude"
            console.print(f"  [dim]{shorten_path(src_ecc_agents)}[/dim]")
            console.print(f"    → [dim]{shorten_path(dst_agents_claude)}[/dim]")
            dst_agents_claude.mkdir(parents=True, exist_ok=True)
            for agent_file in src_ecc_agents.iterdir():
                if agent_file.is_file() and agent_file.suffix == ".md":
                    shutil.copy2(agent_file, dst_agents_claude / agent_file.name)

        # ECC commands → custom-skills/commands/claude
        src_ecc_commands = src_ecc / "commands"
        if src_ecc_commands.exists():
            dst_commands_claude = get_custom_skills_dir() / "commands" / "claude"
            console.print(f"  [dim]{shorten_path(src_ecc_commands)}[/dim]")
            console.print(f"    → [dim]{shorten_path(dst_commands_claude)}[/dim]")
            dst_commands_claude.mkdir(parents=True, exist_ok=True)
            for cmd_file in src_ecc_commands.iterdir():
                if cmd_file.is_file() and cmd_file.suffix == ".md":
                    shutil.copy2(cmd_file, dst_commands_claude / cmd_file.name)


def _ensure_opencode_plugin_entry_file(dst: Path) -> None:
    """確保 OpenCode plugins 第一層存在明確 entry 檔。"""
    plugin_ts = dst / "plugin.ts"
    js_entry = dst / "ecc-hooks-opencode.js"

    if not plugin_ts.exists() or js_entry.exists():
        return

    js_entry.write_text(
        'import { EccHooksPlugin } from "./plugin.ts";\n\n'
        "export default EccHooksPlugin;\n"
        "export { EccHooksPlugin };\n",
        encoding="utf-8",
    )
    console.print(
        f"    [dim]建立 OpenCode plugin entry: {shorten_path(js_entry)}[/dim]"
    )


def _migrate_opencode_plugin_dir_if_needed() -> None:
    """偵測並處理 OpenCode legacy plugin 路徑遷移。"""
    legacy_dir = get_opencode_config_dir() / "plugin"
    modern_dir = get_opencode_plugin_dir()

    if not legacy_dir.exists():
        return

    modern_dir.parent.mkdir(parents=True, exist_ok=True)

    if not modern_dir.exists():
        shutil.move(str(legacy_dir), str(modern_dir))
        console.print(
            "[cyan]偵測到 OpenCode legacy plugin 路徑，已遷移："
            f"{shorten_path(legacy_dir)} → {shorten_path(modern_dir)}[/cyan]"
        )
        return

    console.print(
        "[yellow]偵測到 OpenCode 新舊 plugin 路徑並存："
        f"{shorten_path(legacy_dir)} 與 {shorten_path(modern_dir)}。"
        "將以 plugins 路徑為主要目標並保留 legacy 相容。[/yellow]"
    )


def _load_clone_policy(skill_dir: Path, show_warning: bool = True) -> dict | None:
    """載入並驗證 skill 目錄中的 .clonepolicy.json。"""
    policy_file = skill_dir / ".clonepolicy.json"
    if not policy_file.exists():
        return None

    def _warn(message: str) -> None:
        if show_warning:
            console.print(
                f"[yellow]⚠ clone policy 無效：{shorten_path(policy_file)} ({message})，改用 copytree[/yellow]"
            )

    try:
        data = json.loads(policy_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        _warn(str(e))
        return None

    if not isinstance(data, dict):
        _warn("根節點必須是 object")
        return None

    rules = data.get("rules")
    if not isinstance(rules, list):
        _warn("缺少 rules 陣列")
        return None

    normalized_rules: list[dict[str, str]] = []
    valid_strategies = {"key-merge", "skip-if-exists"}
    for idx, rule in enumerate(rules, start=1):
        if not isinstance(rule, dict):
            _warn(f"rules[{idx}] 必須是 object")
            return None

        pattern = rule.get("pattern")
        strategy = rule.get("strategy")

        if not isinstance(pattern, str) or not pattern:
            _warn(f"rules[{idx}].pattern 必須是非空字串")
            return None

        if strategy not in valid_strategies:
            _warn(f"rules[{idx}].strategy 必須是 {', '.join(sorted(valid_strategies))}")
            return None

        normalized_rules.append({"pattern": pattern, "strategy": strategy})

    return {"rules": normalized_rules}


def _resolve_clone_strategy(relative_path: str, rules: list[dict[str, str]]) -> str:
    """依規則決定檔案複製策略。"""
    for rule in rules:
        if fnmatch.fnmatch(relative_path, rule["pattern"]):
            return rule["strategy"]
    return "default"


def _merge_index_json(src_file: Path, dst_file: Path) -> None:
    """以 id/skillId 為 key 合併 _index.json。"""
    if not dst_file.exists():
        dst_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_file, dst_file)
        return

    try:
        src_data = json.loads(src_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        console.print(
            f"[yellow]⚠ 來源 JSON 讀取失敗，跳過 key-merge: {shorten_path(src_file)} ({e})[/yellow]"
        )
        return

    try:
        dst_data = json.loads(dst_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        console.print(
            f"[yellow]⚠ 目標 JSON 讀取失敗，強制覆蓋: {shorten_path(dst_file)} ({e})[/yellow]"
        )
        shutil.copy2(src_file, dst_file)
        return

    if not isinstance(src_data, dict) or not isinstance(dst_data, dict):
        console.print(
            f"[yellow]⚠ JSON 結構錯誤，跳過 key-merge: {shorten_path(dst_file)}[/yellow]"
        )
        return

    def _get_key(item: dict) -> tuple[str, str] | None:
        item_id = item.get("id")
        if isinstance(item_id, str):
            return ("id", item_id)

        skill_id = item.get("skillId")
        if isinstance(skill_id, str):
            return ("skillId", skill_id)

        return None

    for field_name, src_value in src_data.items():
        dst_value = dst_data.get(field_name)
        if not isinstance(src_value, list) or not isinstance(dst_value, list):
            continue

        existing_keys: set[tuple[str, str]] = set()
        for dst_item in dst_value:
            if not isinstance(dst_item, dict):
                continue
            key = _get_key(dst_item)
            if key is not None:
                existing_keys.add(key)

        for src_item in src_value:
            if not isinstance(src_item, dict):
                continue
            key = _get_key(src_item)
            if key is None or key in existing_keys:
                continue
            dst_value.append(src_item)
            existing_keys.add(key)

    dst_file.parent.mkdir(parents=True, exist_ok=True)
    dst_file.write_text(
        json.dumps(dst_data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _show_clone_file_diff(src_file: Path, dst_file: Path) -> None:
    """顯示來源與目標檔案差異（文字檔）。"""
    try:
        src_lines = src_file.read_text(encoding="utf-8").splitlines()
        dst_lines = dst_file.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        console.print("    [yellow]無法顯示差異（可能為二進位檔案）[/yellow]")
        return
    except OSError as e:
        console.print(f"    [yellow]無法讀取檔案顯示差異: {e}[/yellow]")
        return

    diff_lines = list(
        difflib.unified_diff(
            dst_lines,
            src_lines,
            fromfile=str(dst_file),
            tofile=str(src_file),
            lineterm="",
        )
    )
    if not diff_lines:
        console.print("    [dim]無差異[/dim]")
        return

    console.print("\n".join(diff_lines))


def _copy_skill_with_policy(
    src: Path,
    dst: Path,
    policy: dict,
    force: bool,
    skip_conflicts: bool,
) -> None:
    """依 clone policy 逐檔複製 skill。"""
    from .manifest import compute_file_hash

    rules = policy.get("rules", [])
    dst.mkdir(parents=True, exist_ok=True)

    for src_file in sorted(src.rglob("*")):
        if not src_file.is_file():
            continue

        relative_path = src_file.relative_to(src).as_posix()
        if relative_path == ".clonepolicy.json":
            continue

        strategy = _resolve_clone_strategy(relative_path, rules)
        dst_file = dst / relative_path
        dst_file.parent.mkdir(parents=True, exist_ok=True)

        if strategy == "skip-if-exists":
            if dst_file.exists():
                continue
            shutil.copy2(src_file, dst_file)
            continue

        if strategy == "key-merge":
            _merge_index_json(src_file, dst_file)
            continue

        if not dst_file.exists():
            shutil.copy2(src_file, dst_file)
            continue

        src_hash = compute_file_hash(src_file)
        dst_hash = compute_file_hash(dst_file)
        if src_hash == dst_hash:
            continue

        if force:
            shutil.copy2(src_file, dst_file)
            continue

        if skip_conflicts:
            console.print(f"    [yellow]跳過（衝突）: {relative_path}[/yellow]")
            continue

        while True:
            console.print()
            console.print(f"    [bold yellow]檔案衝突: {relative_path}[/bold yellow]")
            console.print("    [cyan]1[/cyan]. 覆蓋")
            console.print("    [cyan]2[/cyan]. 跳過")
            console.print("    [cyan]3[/cyan]. 備份後覆蓋")
            console.print("    [cyan]4[/cyan]. 查看差異")

            try:
                choice = input("    請輸入選項 (1-4): ").strip()
            except (EOFError, KeyboardInterrupt):
                choice = "2"

            if choice == "1":
                shutil.copy2(src_file, dst_file)
                break
            if choice == "2":
                break
            if choice == "3":
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = dst_file.with_name(f"{dst_file.name}.{timestamp}.bak")
                shutil.copy2(dst_file, backup_path)
                console.print(f"    [dim]已備份: {shorten_path(backup_path)}[/dim]")
                shutil.copy2(src_file, dst_file)
                break
            if choice == "4":
                _show_clone_file_diff(src_file, dst_file)
                continue

            console.print("    [red]無效選項，請輸入 1-4[/red]")


def _copy_with_log(
    src: Path,
    dst: Path,
    resource_type: str,
    target_name: str,
    tracker: "ManifestTracker | None" = None,
    skip_names: set[str] | None = None,
    source: str = "custom-skills",
    force: bool = False,
    skip_conflicts: bool = False,
) -> None:
    """複製目錄並輸出帶路徑的日誌。

    Args:
        src: 來源目錄
        dst: 目標目錄
        resource_type: 資源類型 (skills, commands, agents, workflows)
        target_name: 目標平台名稱
        tracker: ManifestTracker 實例（用於記錄已複製的檔案）
        skip_names: 要跳過的資源名稱集合（用於衝突跳過）
        source: 資源來源名稱（用於 manifest 追蹤）
        force: 預設策略衝突時是否強制覆蓋
        skip_conflicts: 預設策略衝突時是否直接跳過
    """
    if not src.exists():
        return

    console.print(f"  [green]{resource_type}[/green] → [cyan]{target_name}[/cyan]")
    console.print(f"    [dim]{shorten_path(src)} → {shorten_path(dst)}[/dim]")
    dst.mkdir(parents=True, exist_ok=True)

    # 如果有 tracker，需要逐一記錄
    if tracker is not None:
        record_method = {
            "skills": tracker.record_skill,
            "commands": tracker.record_command,
            "agents": tracker.record_agent,
            "workflows": tracker.record_workflow,
        }.get(resource_type)

        if resource_type == "skills":
            # Skills 是目錄結構
            for item in src.iterdir():
                if item.is_dir() and not item.name.startswith("."):
                    if skip_names and item.name in skip_names:
                        console.print(f"    [yellow]跳過（衝突）: {item.name}[/yellow]")
                        continue
                    dst_item = dst / item.name
                    policy = _load_clone_policy(item)
                    if policy is not None:
                        _copy_skill_with_policy(
                            item,
                            dst_item,
                            policy,
                            force=force,
                            skip_conflicts=skip_conflicts,
                        )
                    else:
                        shutil.copytree(item, dst_item, dirs_exist_ok=True)
                    if record_method:
                        record_method(item.name, item, source=source)
        elif resource_type == "plugins":
            # Plugins 可能包含任意檔案結構（ts/json/scripts），直接複製整個目錄
            shutil.copytree(src, dst, dirs_exist_ok=True)
            if target_name == "OpenCode":
                _ensure_opencode_plugin_entry_file(dst)
        else:
            # Commands, Agents, Workflows 是 .md 檔案
            for item in src.iterdir():
                if item.is_file() and item.suffix == ".md":
                    # 跳過 README.md（避免被解析為 agent）
                    if item.name.lower() == "readme.md":
                        continue
                    name = item.stem
                    if skip_names and name in skip_names:
                        console.print(f"    [yellow]跳過（衝突）: {name}[/yellow]")
                        continue
                    dst_item = dst / item.name
                    shutil.copy2(item, dst_item)
                    if record_method:
                        record_method(name, item, source=source)
    else:
        # 無 tracker，仍需尊重 clone policy
        if resource_type == "skills":
            for item in src.iterdir():
                if item.is_dir() and not item.name.startswith("."):
                    dst_item = dst / item.name
                    policy = _load_clone_policy(item)
                    if policy is not None:
                        _copy_skill_with_policy(
                            item,
                            dst_item,
                            policy,
                            force=force,
                            skip_conflicts=skip_conflicts,
                        )
                    else:
                        shutil.copytree(item, dst_item, dirs_exist_ok=True)
        else:
            shutil.copytree(src, dst, dirs_exist_ok=True)


def copy_custom_skills_to_targets(
    sync_project: bool = True,
    force: bool = False,
    skip_conflicts: bool = False,
    backup: bool = False,
) -> None:
    """Stage 3: 將 custom-skills 分發到各工具目錄。

    Args:
        sync_project: 是否同步到專案目錄（預設為 True）
        force: 強制覆蓋所有衝突
        skip_conflicts: 跳過有衝突的檔案
        backup: 備份衝突檔案後覆蓋
    """
    from .manifest import (
        ManifestTracker,
        read_manifest,
        write_manifest,
        detect_conflicts,
        display_conflicts,
        prompt_conflict_action,
        show_conflict_diff,
        find_orphans,
        cleanup_orphans,
        backup_file,
        get_project_version,
    )

    console.print("[bold cyan]Stage 3: 分發到各工具目錄...[/bold cyan]")
    _migrate_opencode_plugin_dir_if_needed()

    # 來源路徑
    src_skills = get_custom_skills_dir() / "skills"
    src_cmd_claude = get_custom_skills_dir() / "commands" / "claude"
    src_cmd_antigravity = get_custom_skills_dir() / "commands" / "antigravity"
    src_cmd_opencode = get_custom_skills_dir() / "commands" / "opencode"
    src_cmd_gemini = get_custom_skills_dir() / "commands" / "gemini"
    src_cmd_workflows = get_custom_skills_dir() / "commands" / "workflows"
    src_agents_claude = get_custom_skills_dir() / "agents" / "claude"
    src_agents_opencode = get_custom_skills_dir() / "agents" / "opencode"
    src_plugins_opencode = get_custom_skills_dir() / "plugins" / "ecc-hooks-opencode"

    # 定義各平台的分發配置
    platform_configs = {
        "claude": {
            "name": "Claude Code",
            "resources": [
                ("skills", src_skills, COPY_TARGETS["claude"]["skills"]),
                ("commands", src_cmd_claude, COPY_TARGETS["claude"]["commands"]),
                ("agents", src_agents_claude, COPY_TARGETS["claude"]["agents"]),
                ("workflows", src_cmd_workflows, COPY_TARGETS["claude"]["workflows"]),
            ],
        },
        "antigravity": {
            "name": "Antigravity",
            "resources": [
                ("skills", src_skills, COPY_TARGETS["antigravity"]["skills"]),
                (
                    "workflows",
                    src_cmd_antigravity,
                    COPY_TARGETS["antigravity"]["workflows"],
                ),
            ],
        },
        "opencode": {
            "name": "OpenCode",
            "resources": [
                ("skills", src_skills, COPY_TARGETS["opencode"]["skills"]),
                ("commands", src_cmd_opencode, COPY_TARGETS["opencode"]["commands"]),
                ("agents", src_agents_opencode, COPY_TARGETS["opencode"]["agents"]),
                ("plugins", src_plugins_opencode, COPY_TARGETS["opencode"]["plugins"]),
            ],
        },
        "codex": {
            "name": "Codex",
            "resources": [
                ("skills", src_skills, COPY_TARGETS["codex"]["skills"]),
            ],
        },
        "gemini": {
            "name": "Gemini CLI",
            "resources": [
                ("skills", src_skills, COPY_TARGETS["gemini"]["skills"]),
                ("commands", src_cmd_gemini, COPY_TARGETS["gemini"]["commands"]),
            ],
        },
    }

    version = get_project_version()

    # 對每個平台執行分發
    for target, config in platform_configs.items():
        target_name = config["name"]

        # 1. 讀取舊 manifest
        old_manifest = read_manifest(target)

        # 2. 建立 tracker 並預先掃描要分發的檔案
        tracker = ManifestTracker(target=target)

        # 先掃描所有要分發的檔案以建立 tracker（用於衝突檢測）
        # 資源類型到方法名的映射
        record_method_map = {
            "skills": tracker.record_skill,
            "commands": tracker.record_command,
            "agents": tracker.record_agent,
            "workflows": tracker.record_workflow,
        }

        for resource_type, src, dst in config["resources"]:
            if not src.exists():
                continue
            record_method = record_method_map.get(resource_type)
            if resource_type == "skills":
                for item in src.iterdir():
                    if item.is_dir() and not item.name.startswith("."):
                        # 含 .clonepolicy.json 的 skill 跳過 prescan：
                        # 其衝突在 _copy_skill_with_policy 中以檔案層級處理，
                        # 不需要目錄層級的衝突檢測。
                        # copy 階段仍會呼叫 record_method 記錄 hash（用於孤兒清理）。
                        if _load_clone_policy(item, show_warning=False) is not None:
                            continue
                        if record_method:
                            record_method(item.name, item, source="custom-skills")
            else:
                for item in src.iterdir():
                    if item.is_file() and item.suffix == ".md":
                        if record_method:
                            record_method(item.stem, item, source="custom-skills")

        # 預掃描 custom repos 的資源
        _prescan_custom_repos(target, record_method_map)

        # 3. 檢測衝突
        conflicts = detect_conflicts(target, old_manifest, tracker)
        skip_names: set[str] = set()

        if conflicts:
            # 決定衝突處理方式
            if force:
                action = "force"
            elif skip_conflicts:
                action = "skip"
            elif backup:
                action = "backup"
            else:
                # 互動式詢問（支援查看差異後重新選擇）
                display_conflicts(conflicts)
                action = prompt_conflict_action(conflicts)
                while action == "diff":
                    show_conflict_diff(conflicts)
                    display_conflicts(conflicts)
                    action = prompt_conflict_action(conflicts)

            if action == "abort":
                console.print("[yellow]已取消分發[/yellow]")
                return
            elif action == "skip":
                skip_names = {c.name for c in conflicts}
                console.print(f"[yellow]跳過 {len(skip_names)} 個衝突檔案[/yellow]")
            elif action == "backup":
                console.print("[cyan]備份衝突檔案...[/cyan]")
                for conflict in conflicts:
                    backup_file(target, conflict.resource_type, conflict.name)

        # 4. 重新建立 tracker（因為可能有跳過的檔案）
        tracker = ManifestTracker(target=target)

        # 5. 執行複製並記錄
        for resource_type, src, dst in config["resources"]:
            _copy_with_log(
                src,
                dst,
                resource_type,
                target_name,
                tracker=tracker,
                skip_names=(
                    skip_names
                    if resource_type in ["skills", "commands", "agents", "workflows"]
                    else None
                ),
                source="custom-skills",
                force=force,
                skip_conflicts=skip_conflicts,
            )

        # 5.5 分發 custom repos 的資源
        _distribute_custom_repos(
            target,
            target_name,
            tracker,
            skip_names,
            force=force,
            skip_conflicts=skip_conflicts,
        )

        # 6. 產生新 manifest
        new_manifest = tracker.to_manifest(version)

        # 7. 處理跳過的衝突檔案
        # 跳過的檔案應保留在 manifest 中（保留舊 hash），這樣下次分發仍可檢測衝突
        if skip_names and old_manifest:
            old_files = old_manifest.get("files", {})
            for resource_type in ["skills", "commands", "agents", "workflows"]:
                for name in skip_names:
                    if name in old_files.get(resource_type, {}):
                        # 保留舊的 hash 到新 manifest
                        if resource_type not in new_manifest["files"]:
                            new_manifest["files"][resource_type] = {}
                        new_manifest["files"][resource_type][name] = old_files[
                            resource_type
                        ][name]

        # 8. 清理孤兒檔案
        # 注意：跳過的衝突檔案不應被視為孤兒（因為已在步驟 7 中加回 manifest）
        orphans = find_orphans(old_manifest, new_manifest)
        cleanup_orphans(target, orphans)

        # 9. 寫入新 manifest
        write_manifest(target, new_manifest)

    # 專案目錄同步（不使用 manifest 追蹤）
    if sync_project:
        _sync_to_project_directory(src_skills)


def _prescan_custom_repos(
    target: str,
    record_method_map: dict,
) -> None:
    """預掃描 custom repos 的資源（用於衝突檢測）。"""
    from .custom_repos import load_custom_repos

    custom_repos = load_custom_repos().get("repos", {})
    for repo_name, repo_info in custom_repos.items():
        local_path = Path(
            repo_info.get("local_path", "").replace("~", str(Path.home()))
        )
        if not local_path.exists():
            continue
        _scan_repo_resources(local_path, target, record_method_map, source=repo_name)


def _scan_repo_resources(
    repo_dir: Path,
    target: str,
    record_method_map: dict,
    source: str,
) -> None:
    """掃描單一 repo 的資源並記錄到 tracker。"""
    # Skills（所有平台共用）
    skills_dir = repo_dir / "skills"
    if skills_dir.exists():
        record = record_method_map.get("skills")
        if record:
            for item in skills_dir.iterdir():
                if item.is_dir() and not item.name.startswith("."):
                    # 含 clone policy 的 skill 跳過 prescan（衝突在檔案層級處理）
                    if _load_clone_policy(item, show_warning=False) is not None:
                        continue
                    record(item.name, item, source=source)

    # Commands（按平台子目錄）
    _scan_platform_resources(
        repo_dir / "commands", target, "commands", record_method_map, source
    )

    # Agents（按平台子目錄）
    _scan_platform_resources(
        repo_dir / "agents", target, "agents", record_method_map, source
    )


def _scan_platform_resources(
    base_dir: Path,
    target: str,
    resource_type: str,
    record_method_map: dict,
    source: str,
) -> None:
    """掃描按平台子目錄組織的資源。"""
    platform_dir = base_dir / target
    if not platform_dir.exists():
        return

    record = record_method_map.get(resource_type)
    if not record:
        return

    for item in platform_dir.iterdir():
        if item.is_file() and item.suffix == ".md":
            if item.name.lower() == "readme.md":
                continue
            record(item.stem, item, source=source)


def _distribute_custom_repos(
    target: str,
    target_name: str,
    tracker: "ManifestTracker",
    skip_names: set[str],
    force: bool = False,
    skip_conflicts: bool = False,
) -> None:
    """分發 custom repos 的資源到指定平台。"""
    from .custom_repos import load_custom_repos

    custom_repos = load_custom_repos().get("repos", {})
    if not custom_repos:
        return

    for repo_name, repo_info in custom_repos.items():
        local_path = Path(
            repo_info.get("local_path", "").replace("~", str(Path.home()))
        )
        if not local_path.exists():
            console.print(
                f"  [yellow]⚠ Custom repo 目錄不存在，跳過: {repo_name} ({local_path})[/yellow]"
            )
            continue

        console.print(f"  [bold cyan]分發 custom repo: {repo_name}[/bold cyan]")

        # Skills（所有平台共用）
        skills_src = local_path / "skills"
        if skills_src.exists():
            skills_dst = COPY_TARGETS.get(target, {}).get("skills")
            if skills_dst:
                _copy_with_log(
                    skills_src,
                    skills_dst,
                    "skills",
                    target_name,
                    tracker=tracker,
                    skip_names=skip_names,
                    source=repo_name,
                    force=force,
                    skip_conflicts=skip_conflicts,
                )

        # Commands（按平台子目錄）
        cmd_src = local_path / "commands" / target
        if cmd_src.exists():
            cmd_dst = COPY_TARGETS.get(target, {}).get("commands")
            if cmd_dst:
                _copy_with_log(
                    cmd_src,
                    cmd_dst,
                    "commands",
                    target_name,
                    tracker=tracker,
                    skip_names=skip_names,
                    source=repo_name,
                    force=force,
                    skip_conflicts=skip_conflicts,
                )

        # Agents（按平台子目錄）
        agents_src = local_path / "agents" / target
        if agents_src.exists():
            agents_dst = COPY_TARGETS.get(target, {}).get("agents")
            if agents_dst:
                _copy_with_log(
                    agents_src,
                    agents_dst,
                    "agents",
                    target_name,
                    tracker=tracker,
                    skip_names=skip_names,
                    source=repo_name,
                    force=force,
                    skip_conflicts=skip_conflicts,
                )


def _is_custom_skills_project(project_root: Path) -> bool:
    """檢查是否在 custom-skills 專案目錄中。

    透過檢查 pyproject.toml 中的 name = "ai-dev" 來判斷。
    """
    pyproject_path = project_root / "pyproject.toml"
    if not pyproject_path.exists():
        return False

    try:
        content = pyproject_path.read_text(encoding="utf-8")
        # 簡單檢查是否包含 name = "ai-dev"
        return 'name = "ai-dev"' in content
    except Exception:
        return False


def _sync_to_project_directory(src_skills: Path) -> None:
    """同步資源到 custom-skills 專案目錄（內部函式）。

    只有當前目錄是 custom-skills 專案時才會同步，
    這是為了讓開發人員在本地開發時能同步最新的外部資源。
    """
    project_root = get_project_root()

    # 只在 custom-skills 專案中才同步
    if not _is_custom_skills_project(project_root):
        return

    # 防止在分發目錄中執行 clone 時自我複製
    # 當專案目錄就是 ~/.config/custom-skills 時，跳過同步
    custom_skills_dir = get_custom_skills_dir()
    if project_root.resolve() == custom_skills_dir.resolve():
        console.print(
            f"[yellow]  跳過專案同步：當前目錄就是分發目錄 ({shorten_path(custom_skills_dir)})[/yellow]"
        )
        return

    console.print(
        f"[bold yellow]  偵測到 custom-skills 專案：{shorten_path(project_root)}[/bold yellow]"
    )

    # Skills → Project
    if src_skills.exists():
        dst_project_skills = project_root / "skills"
        console.print(f"  [green]skills[/green] → [cyan]專案目錄[/cyan]")
        console.print(
            f"    [dim]{shorten_path(src_skills)} → {shorten_path(dst_project_skills)}[/dim]"
        )
        dst_project_skills.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src_skills, dst_project_skills, dirs_exist_ok=True)
        clean_unwanted_files(dst_project_skills, use_readonly_handler=True)

    # Commands → Project
    src_commands = get_custom_skills_dir() / "commands"
    if src_commands.exists():
        dst_project_commands = project_root / "commands"
        console.print(f"  [green]commands[/green] → [cyan]專案目錄[/cyan]")
        console.print(
            f"    [dim]{shorten_path(src_commands)} → {shorten_path(dst_project_commands)}[/dim]"
        )
        shutil.copytree(src_commands, dst_project_commands, dirs_exist_ok=True)

    # Agents → Project
    src_agents_all = get_custom_skills_dir() / "agents"
    if src_agents_all.exists():
        dst_project_agents = project_root / "agents"
        console.print(f"  [green]agents[/green] → [cyan]專案目錄[/cyan]")
        console.print(
            f"    [dim]{shorten_path(src_agents_all)} → {shorten_path(dst_project_agents)}[/dim]"
        )
        shutil.copytree(src_agents_all, dst_project_agents, dirs_exist_ok=True)


def copy_skills(
    sync_project: bool = True,
    force: bool = False,
    skip_conflicts: bool = False,
    backup: bool = False,
) -> None:
    """將 ~/.config/custom-skills 分發到各工具目錄。

    流程說明：
    - Stage 1: Clone/Pull 外部套件（由 install/update 指令處理）
    - Stage 3: 分發 ~/.config/custom-skills 到各工具目錄

    注意：不再執行 Stage 2（整合外部來源到 custom-skills）。
    ~/.config/custom-skills 的內容由 git repo 控制。
    開發者如需整合外部來源，請使用 integrate_to_dev_project()。

    Args:
        sync_project: 是否同步到專案目錄（預設為 True，僅對開發目錄有效）
        force: 強制覆蓋所有衝突
        skip_conflicts: 跳過有衝突的檔案
        backup: 備份衝突檔案後覆蓋
    """
    # Stage 3: 分發到目標目錄
    copy_custom_skills_to_targets(
        sync_project=sync_project,
        force=force,
        skip_conflicts=skip_conflicts,
        backup=backup,
    )


def integrate_to_dev_project(dev_project_root: Path) -> None:
    """將外部來源整合到開發目錄。

    此函式供開發者使用，將 ~/.config/<repos> 的外部來源
    整合到指定的開發目錄（非 ~/.config/custom-skills）。

    整合來源：
    - UDS (skills, agents, workflows, commands)
    - Obsidian skills
    - Anthropic skill-creator
    - ECC (skills, agents, commands) - 從專案內的 sources/ecc

    Args:
        dev_project_root: 開發專案的根目錄
    """
    console.print("[bold cyan]整合外部來源到開發目錄...[/bold cyan]")
    console.print(f"  目標：{shorten_path(dev_project_root)}")

    dst_skills = dev_project_root / "skills"
    dst_skills.mkdir(parents=True, exist_ok=True)

    # ============================================================
    # UDS 來源 - 主要整合來源
    # ============================================================
    src_uds = get_uds_dir() / "skills" / "claude-code"
    if src_uds.exists():
        console.print(f"  [dim]{shorten_path(src_uds)}[/dim]")
        console.print(f"    → [dim]{shorten_path(dst_skills)}[/dim]")
        # 複製時排除 agents 和 workflows（這些有專門的目的地）
        for item in src_uds.iterdir():
            if item.name in ("agents", "workflows", "commands"):
                continue  # 這些會單獨處理
            dst_item = dst_skills / item.name
            if item.is_dir():
                shutil.copytree(item, dst_item, dirs_exist_ok=True)
            else:
                shutil.copy2(item, dst_item)
        clean_unwanted_files(dst_skills)

    # UDS agents → dev/agents/claude 和 dev/agents/opencode
    src_uds_agents = get_uds_dir() / "skills" / "claude-code" / "agents"
    if src_uds_agents.exists():
        # 複製到 claude
        dst_agents_claude = dev_project_root / "agents" / "claude"
        console.print(f"  [dim]{shorten_path(src_uds_agents)}[/dim]")
        console.print(f"    → [dim]{shorten_path(dst_agents_claude)}[/dim]")
        dst_agents_claude.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src_uds_agents, dst_agents_claude, dirs_exist_ok=True)

        # 同時複製到 opencode
        dst_agents_opencode = dev_project_root / "agents" / "opencode"
        console.print(f"    → [dim]{shorten_path(dst_agents_opencode)}[/dim]")
        dst_agents_opencode.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src_uds_agents, dst_agents_opencode, dirs_exist_ok=True)

    # UDS workflows → dev/commands/workflows
    src_uds_workflows = get_uds_dir() / "skills" / "claude-code" / "workflows"
    dst_workflows = dev_project_root / "commands" / "workflows"
    if src_uds_workflows.exists():
        console.print(f"  [dim]{shorten_path(src_uds_workflows)}[/dim]")
        console.print(f"    → [dim]{shorten_path(dst_workflows)}[/dim]")
        dst_workflows.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src_uds_workflows, dst_workflows, dirs_exist_ok=True)

    # UDS commands → dev/commands/claude（如果存在）
    src_uds_commands = get_uds_dir() / "skills" / "claude-code" / "commands"
    dst_commands = dev_project_root / "commands" / "claude"
    if src_uds_commands.exists():
        console.print(f"  [dim]{shorten_path(src_uds_commands)}[/dim]")
        console.print(f"    → [dim]{shorten_path(dst_commands)}[/dim]")
        dst_commands.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src_uds_commands, dst_commands, dirs_exist_ok=True)

    # ============================================================
    # Obsidian skills
    # ============================================================
    src_obsidian = get_obsidian_skills_dir() / "skills"
    if src_obsidian.exists():
        console.print(f"  [dim]{shorten_path(src_obsidian)}[/dim]")
        console.print(f"    → [dim]{shorten_path(dst_skills)}[/dim]")
        shutil.copytree(src_obsidian, dst_skills, dirs_exist_ok=True)

    # ============================================================
    # Anthropic skill-creator
    # ============================================================
    src_anthropic = get_anthropic_skills_dir() / "skills" / "skill-creator"
    if src_anthropic.exists():
        dst_skill_creator = dst_skills / "skill-creator"
        console.print(f"  [dim]{shorten_path(src_anthropic)}[/dim]")
        console.print(f"    → [dim]{shorten_path(dst_skill_creator)}[/dim]")
        shutil.copytree(src_anthropic, dst_skill_creator, dirs_exist_ok=True)

    # ============================================================
    # Auto-Skill（自進化知識系統）
    # ============================================================
    src_auto_skill = get_auto_skill_dir()
    if src_auto_skill.exists() and (src_auto_skill / "SKILL.md").exists():
        dst_auto_skill = dst_skills / "auto-skill"
        console.print(f"  [dim]{shorten_path(src_auto_skill)}[/dim]")
        console.print(f"    → [dim]{shorten_path(dst_auto_skill)}[/dim]")
        shutil.copytree(
            src_auto_skill,
            dst_auto_skill,
            dirs_exist_ok=True,
            ignore=shutil.ignore_patterns(".git", "assets", "README.md"),
        )

    # ============================================================
    # ECC (everything-claude-code) 資源 - 從專案內的 sources/ecc
    # ============================================================
    src_ecc = dev_project_root / "sources" / "ecc"
    if src_ecc.exists():
        console.print("[bold cyan]  整合 ECC 資源...[/bold cyan]")

        # ECC skills → dev/skills
        src_ecc_skills = src_ecc / "skills"
        if src_ecc_skills.exists():
            console.print(f"  [dim]{shorten_path(src_ecc_skills)}[/dim]")
            console.print(f"    → [dim]{shorten_path(dst_skills)}[/dim]")
            for skill_dir in src_ecc_skills.iterdir():
                if skill_dir.is_dir():
                    dst_skill = dst_skills / skill_dir.name
                    shutil.copytree(skill_dir, dst_skill, dirs_exist_ok=True)

        # ECC agents → dev/agents/claude
        src_ecc_agents = src_ecc / "agents"
        if src_ecc_agents.exists():
            dst_agents_claude = dev_project_root / "agents" / "claude"
            console.print(f"  [dim]{shorten_path(src_ecc_agents)}[/dim]")
            console.print(f"    → [dim]{shorten_path(dst_agents_claude)}[/dim]")
            dst_agents_claude.mkdir(parents=True, exist_ok=True)
            for agent_file in src_ecc_agents.iterdir():
                if agent_file.is_file() and agent_file.suffix == ".md":
                    shutil.copy2(agent_file, dst_agents_claude / agent_file.name)

        # ECC commands → dev/commands/claude
        src_ecc_commands = src_ecc / "commands"
        if src_ecc_commands.exists():
            dst_commands_claude = dev_project_root / "commands" / "claude"
            console.print(f"  [dim]{shorten_path(src_ecc_commands)}[/dim]")
            console.print(f"    → [dim]{shorten_path(dst_commands_claude)}[/dim]")
            dst_commands_claude.mkdir(parents=True, exist_ok=True)
            for cmd_file in src_ecc_commands.iterdir():
                if cmd_file.is_file() and cmd_file.suffix == ".md":
                    shutil.copy2(cmd_file, dst_commands_claude / cmd_file.name)

    console.print("[green]✓ 外部來源整合完成[/green]")


# ============================================================
# Disabled 目錄管理
# ============================================================


def get_disabled_base_dir() -> Path:
    """取得 disabled 目錄的基礎路徑。"""
    return get_custom_skills_dir() / "disabled"


def get_disabled_path(
    target: TargetType, resource_type: ResourceType, name: str
) -> Path:
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
    target: TargetType, resource_type: ResourceType, name: str, quiet: bool = False
) -> bool:
    """停用資源：將檔案從目標工具目錄複製到 disabled 目錄，再刪除原檔案。

    Args:
        target: 目標工具 (claude, antigravity, opencode)
        resource_type: 資源類型 (skills, commands, agents, workflows)
        name: 資源名稱
        quiet: 是否抑制輸出訊息

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
        if not quiet:
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

    if not quiet:
        console.print(f"[yellow]已停用 {target}/{resource_type}/{name}[/yellow]")
        # 8. 顯示重啟提醒
        show_restart_reminder(target)

    return True


def enable_resource(
    target: TargetType, resource_type: ResourceType, name: str, quiet: bool = False
) -> bool:
    """啟用資源：將檔案從 disabled 目錄複製回目標工具目錄，再刪除 disabled 中的檔案。

    Args:
        target: 目標工具 (claude, antigravity, opencode)
        resource_type: 資源類型 (skills, commands, agents, workflows)
        name: 資源名稱
        quiet: 是否抑制輸出訊息

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
        if not quiet:
            console.print(
                f"[dim]disabled 目錄中不存在 {name}，嘗試從來源重新複製...[/dim]"
            )
        if not copy_single_resource(target, resource_type, name):
            if not quiet:
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

    if not quiet:
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
        # Skills 來源：UDS, Obsidian, Anthropic, ECC, Custom
        sources = [
            get_uds_dir() / "skills" / "claude-code" / name,
            get_obsidian_skills_dir() / "skills" / name,
            get_ecc_sources_dir() / "skills" / name,
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
        # Commands 來源：ECC, custom-skills/commands/claude
        sources = [
            get_ecc_sources_dir() / "commands" / f"{name}.md",
            get_custom_skills_dir() / "commands" / "claude" / f"{name}.md",
        ]
        for src in sources:
            if src.exists():
                target_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, target_path)
                return True

    elif resource_type == "workflows":
        # Workflows 來源：custom-skills/commands/antigravity
        src = get_custom_skills_dir() / "commands" / "antigravity" / f"{name}.md"
        if src.exists():
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, target_path)
            return True

    elif resource_type == "agents":
        # Agents 來源：ECC, Claude, OpenCode
        sources = [
            get_ecc_sources_dir() / "agents" / f"{name}.md",
            get_custom_skills_dir() / "agents" / "claude" / f"{name}.md",
            get_custom_skills_dir() / "agents" / "opencode" / f"{name}.md",
        ]
        for src in sources:
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
        "agents": {"enabled": True, "disabled": []},
        "workflows": {"enabled": True, "disabled": []},
    },
    "antigravity": {
        "skills": {"enabled": True, "disabled": []},
        "workflows": {"enabled": True, "disabled": []},
    },
    "opencode": {
        "skills": {"enabled": True, "disabled": []},
        "commands": {"enabled": True, "disabled": []},
        "agents": {"enabled": True, "disabled": []},
        "plugins": {"enabled": True, "disabled": []},
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
        yaml.dump(
            config, f, allow_unicode=True, default_flow_style=False, sort_keys=False
        )


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
    "ecc": "everything-claude-code",
    "auto_skill": "auto-skill",
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

    # ECC skills (everything-claude-code)
    ecc_path = get_ecc_sources_dir() / "skills"
    if ecc_path.exists():
        sources["ecc"] = {d.name for d in ecc_path.iterdir() if d.is_dir()}
    else:
        sources["ecc"] = set()

    # Auto-Skill
    auto_skill_path = get_auto_skill_dir()
    if auto_skill_path.exists() and (auto_skill_path / "SKILL.md").exists():
        sources["auto_skill"] = {"auto-skill"}
    else:
        sources["auto_skill"] = set()

    # Custom skills (本專案)
    custom_path = get_custom_skills_dir() / "skills"
    if custom_path.exists():
        # 排除來自其他來源的
        all_known = (
            sources["uds"]
            | sources["obsidian"]
            | sources["anthropic"]
            | sources["ecc"]
            | sources["auto_skill"]
        )
        sources["custom"] = {
            d.name
            for d in custom_path.iterdir()
            if d.is_dir() and d.name not in all_known
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
        ("claude", "agents"): get_claude_agents_dir(),
        ("claude", "workflows"): get_claude_workflows_dir(),
        ("antigravity", "skills"): get_antigravity_config_dir() / "global_skills",
        ("antigravity", "workflows"): get_antigravity_config_dir() / "global_workflows",
        ("opencode", "skills"): get_opencode_config_dir() / "skills",
        ("opencode", "commands"): get_opencode_config_dir() / "commands",
        ("opencode", "agents"): get_opencode_config_dir() / "agents",
        ("codex", "skills"): get_codex_config_dir() / "skills",
        ("gemini", "skills"): get_gemini_cli_config_dir() / "skills",
        ("gemini", "commands"): get_gemini_cli_config_dir() / "commands",
    }
    return paths.get((target, resource_type))


def get_source_commands() -> dict[str, set[str]]:
    """取得 commands 的來源名稱集合。"""
    sources = {}

    # ECC commands (everything-claude-code)
    ecc_cmd = get_ecc_sources_dir() / "commands"
    if ecc_cmd.exists():
        sources["ecc"] = {
            f.stem for f in ecc_cmd.iterdir() if f.is_file() and f.suffix == ".md"
        }
    else:
        sources["ecc"] = set()

    # Custom commands (本專案)
    custom_cmd_claude = get_custom_skills_dir() / "commands" / "claude"
    if custom_cmd_claude.exists():
        # 排除 ECC 來源
        sources["custom"] = {
            f.stem
            for f in custom_cmd_claude.iterdir()
            if f.is_file() and f.suffix == ".md" and f.stem not in sources["ecc"]
        }
    else:
        sources["custom"] = set()

    return sources


def get_source_workflows() -> dict[str, set[str]]:
    """取得 workflows 的來源名稱集合。"""
    sources = {}

    # Custom workflows (本專案)
    custom_wf = get_custom_skills_dir() / "commands" / "antigravity"
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

    # ECC agents (everything-claude-code)
    ecc_agents = get_ecc_sources_dir() / "agents"
    if ecc_agents.exists():
        sources["ecc"] = {
            f.stem for f in ecc_agents.iterdir() if f.is_file() and f.suffix == ".md"
        }
    else:
        sources["ecc"] = set()

    all_agents = set()

    # Claude agents
    claude_agents_dir = get_custom_skills_dir() / "agents" / "claude"
    if claude_agents_dir.exists():
        all_agents.update(
            f.stem
            for f in claude_agents_dir.iterdir()
            if f.is_file() and f.suffix == ".md"
        )

    # OpenCode agents
    opencode_agents_dir = get_custom_skills_dir() / "agents" / "opencode"
    if opencode_agents_dir.exists():
        all_agents.update(
            f.stem
            for f in opencode_agents_dir.iterdir()
            if f.is_file() and f.suffix == ".md"
        )

    # 排除 ECC 來源
    sources["custom"] = all_agents - sources["ecc"]
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

    targets = (
        [target] if target else ["claude", "antigravity", "opencode", "codex", "gemini"]
    )
    type_mapping = {
        "claude": ["skills", "commands", "agents", "workflows"],
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
                            items.append(
                                {
                                    "name": item.name,
                                    "source": source,
                                    "disabled": False,
                                }
                            )
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
                            items.append(
                                {
                                    "name": name,
                                    "source": source,
                                    "disabled": False,
                                }
                            )
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

                    items.append(
                        {
                            "name": name,
                            "source": source,
                            "disabled": True,
                        }
                    )

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


# =============================================================================
# ECC Hooks Plugin Functions
# =============================================================================


def get_ecc_hooks_source_dir() -> Path:
    """取得 ECC Hooks 來源目錄。"""
    return get_ecc_sources_dir() / "hooks"


def get_ecc_hooks_plugin_dir() -> Path:
    """取得 ECC Hooks Plugin 安裝目錄。"""
    return Path.home() / ".claude" / "plugins" / "ecc-hooks"


def get_ecc_hooks_status() -> dict:
    """取得 ECC Hooks Plugin 狀態。

    Returns:
        dict: 包含以下鍵值：
            - installed: bool - 是否已安裝
            - source_exists: bool - 來源目錄是否存在
            - plugin_path: Path - Plugin 安裝路徑
            - hooks_json_path: Path | None - hooks.json 路徑（若存在）
    """
    plugin_dir = get_ecc_hooks_plugin_dir()
    source_dir = get_ecc_hooks_source_dir()

    hooks_json = plugin_dir / "hooks" / "hooks.json"
    if not hooks_json.exists():
        hooks_json = None

    return {
        "installed": plugin_dir.exists() and (plugin_dir / ".claude-plugin").exists(),
        "source_exists": source_dir.exists(),
        "plugin_path": plugin_dir,
        "hooks_json_path": hooks_json,
    }


def show_ecc_hooks_status() -> None:
    """顯示 ECC Hooks Plugin 狀態。"""
    status = get_ecc_hooks_status()

    console.print("[bold]ECC Hooks Plugin Status[/bold]")
    console.print()

    if status["installed"]:
        console.print(
            f"[green]✓ Installed[/green] at {shorten_path(status['plugin_path'])}"
        )
        if status["hooks_json_path"]:
            console.print(f"  Config: {shorten_path(status['hooks_json_path'])}")
    else:
        console.print("[yellow]✗ Not installed[/yellow]")

    if status["source_exists"]:
        console.print(f"[dim]Source: {shorten_path(get_ecc_hooks_source_dir())}[/dim]")
    else:
        console.print("[red]✗ Source not found[/red]")


def install_ecc_hooks_plugin() -> bool:
    """安裝或更新 ECC Hooks Plugin。

    Returns:
        bool: True 表示成功，False 表示失敗
    """
    source_dir = get_ecc_hooks_source_dir()
    plugin_dir = get_ecc_hooks_plugin_dir()

    if not source_dir.exists():
        console.print(f"[red]Error: Source not found at {source_dir}[/red]")
        console.print("[dim]Run 'ai-dev install' or 'ai-dev update' first[/dim]")
        return False

    # 確保目標目錄的父目錄存在
    plugin_dir.parent.mkdir(parents=True, exist_ok=True)

    # 移除舊的 plugin（如果存在）
    if plugin_dir.exists():
        shutil.rmtree(plugin_dir, onerror=handle_remove_readonly)
        console.print(f"[dim]Removed old plugin at {shorten_path(plugin_dir)}[/dim]")

    # 複製新的 plugin
    shutil.copytree(source_dir, plugin_dir)
    console.print(f"[green]✓ Installed ECC Hooks Plugin[/green]")
    console.print(f"  From: {shorten_path(source_dir)}")
    console.print(f"  To:   {shorten_path(plugin_dir)}")

    return True


def uninstall_ecc_hooks_plugin() -> bool:
    """移除 ECC Hooks Plugin。

    Returns:
        bool: True 表示成功，False 表示失敗
    """
    plugin_dir = get_ecc_hooks_plugin_dir()

    if not plugin_dir.exists():
        console.print("[yellow]ECC Hooks Plugin is not installed[/yellow]")
        return True

    try:
        shutil.rmtree(plugin_dir, onerror=handle_remove_readonly)
        console.print(f"[green]✓ Removed ECC Hooks Plugin[/green]")
        console.print(f"  Path: {shorten_path(plugin_dir)}")
        return True
    except Exception as e:
        console.print(f"[red]Error removing plugin: {e}[/red]")
        return False
