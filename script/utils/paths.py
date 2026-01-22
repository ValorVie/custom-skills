from pathlib import Path
from .system import get_os


def get_home_dir() -> Path:
    return Path.home()


def get_config_dir() -> Path:
    return get_home_dir() / ".config"


def get_custom_skills_dir() -> Path:
    return get_config_dir() / "custom-skills"


def get_claude_config_dir() -> Path:
    return get_home_dir() / ".claude"


def get_antigravity_config_dir() -> Path:
    if get_os() == "windows":
        return get_home_dir() / ".gemini" / "antigravity"
    return get_home_dir() / ".gemini" / "antigravity"


def get_opencode_config_dir() -> Path:
    return get_config_dir() / "opencode"


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


def get_project_root() -> Path:
    """Find the project root by looking for pyproject.toml."""
    # Assuming the script is run from near the root or we find the root marker
    # The file is in root/script/utils/paths.py
    # So .parent.parent.parent is root.
    return Path(__file__).parent.parent.parent
