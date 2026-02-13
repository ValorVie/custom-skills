from pathlib import Path
from .system import get_os


def get_home_dir() -> Path:
    return Path.home()


def get_config_dir() -> Path:
    return get_home_dir() / ".config"


def get_custom_skills_dir() -> Path:
    return get_config_dir() / "custom-skills"


def get_ai_dev_config_dir() -> Path:
    """回傳 ai-dev 設定目錄。"""
    return get_config_dir() / "ai-dev"


def get_sync_config_path() -> Path:
    """回傳 sync 設定檔路徑。"""
    return get_ai_dev_config_dir() / "sync.yaml"


def get_sync_repo_dir() -> Path:
    """回傳 sync repo 目錄路徑。"""
    return get_ai_dev_config_dir() / "sync-repo"


def get_claude_config_dir() -> Path:
    return get_home_dir() / ".claude"


def get_claude_agents_dir() -> Path:
    """回傳 Claude Code agents 目錄路徑。"""
    return get_claude_config_dir() / "agents"


def get_claude_workflows_dir() -> Path:
    """回傳 Claude Code workflows 目錄路徑。"""
    return get_claude_config_dir() / "workflows"


def get_antigravity_config_dir() -> Path:
    if get_os() == "windows":
        return get_home_dir() / ".gemini" / "antigravity"
    return get_home_dir() / ".gemini" / "antigravity"


def get_opencode_config_dir() -> Path:
    return get_config_dir() / "opencode"


def get_opencode_plugin_dir() -> Path:
    """回傳 OpenCode plugin 目錄路徑。"""
    return get_opencode_config_dir() / "plugins"


def get_opencode_superpowers_dir() -> Path:
    """回傳 OpenCode 專用的 superpowers 目錄。"""
    return get_opencode_config_dir() / "superpowers"


def get_codex_config_dir() -> Path:
    """回傳 OpenAI Codex CLI 的配置目錄路徑。"""
    return get_home_dir() / ".codex"


def get_gemini_cli_config_dir() -> Path:
    """回傳 Gemini CLI 的配置目錄路徑。"""
    return get_home_dir() / ".gemini"


def get_superpowers_dir() -> Path:
    return get_config_dir() / "superpowers"


def get_uds_dir() -> Path:
    return get_config_dir() / "universal-dev-standards"


def get_obsidian_skills_dir() -> Path:
    """回傳 obsidian-skills 儲存庫的本地路徑。"""
    return get_config_dir() / "obsidian-skills"


def get_anthropic_skills_dir() -> Path:
    """回傳 anthropic-skills 儲存庫的本地路徑。"""
    return get_config_dir() / "anthropic-skills"


def get_ecc_dir() -> Path:
    """回傳 everything-claude-code 儲存庫的本地路徑。"""
    return get_config_dir() / "everything-claude-code"


def get_auto_skill_dir() -> Path:
    """回傳 auto-skill 儲存庫的本地路徑。"""
    return get_config_dir() / "auto-skill"


def get_project_root() -> Path:
    """取得用戶當前工作目錄作為專案根目錄。

    Returns:
        Path: 當前工作目錄
    """
    return Path.cwd()
