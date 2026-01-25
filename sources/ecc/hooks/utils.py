"""
Cross-platform utility functions for Claude Code hooks.
Works on Windows, macOS, and Linux.

Upstream: everything-claude-code
Source URL: https://github.com/anthropics/everything-claude-code
Synced Date: 2026-01-24
License: MIT
"""

import os
import sys
import json
import re
import shutil
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any, Pattern


# Platform detection
IS_WINDOWS = sys.platform == 'win32'
IS_MACOS = sys.platform == 'darwin'
IS_LINUX = sys.platform.startswith('linux')


def get_home_dir() -> Path:
    """Get the user's home directory (cross-platform)."""
    return Path.home()


def get_claude_dir() -> Path:
    """Get the Claude config directory."""
    return get_home_dir() / '.claude'


def get_sessions_dir() -> Path:
    """Get the sessions directory."""
    return get_claude_dir() / 'sessions'


def get_learned_skills_dir() -> Path:
    """Get the learned skills directory."""
    return get_claude_dir() / 'skills' / 'learned'


def get_temp_dir() -> Path:
    """Get the temp directory (cross-platform)."""
    return Path(tempfile.gettempdir())


def ensure_dir(dir_path: Path) -> Path:
    """Ensure a directory exists (create if not)."""
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def get_date_string() -> str:
    """Get current date in YYYY-MM-DD format."""
    return datetime.now().strftime('%Y-%m-%d')


def get_time_string() -> str:
    """Get current time in HH:MM format."""
    return datetime.now().strftime('%H:%M')


def get_datetime_string() -> str:
    """Get current datetime in YYYY-MM-DD HH:MM:SS format."""
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def find_files(
    dir_path: Path,
    pattern: str,
    max_age: Optional[int] = None,
    recursive: bool = False
) -> List[Dict[str, Any]]:
    """
    Find files matching a pattern in a directory.

    Args:
        dir_path: Directory to search
        pattern: File pattern (e.g., "*.tmp", "*.md")
        max_age: Maximum age in days (None for no limit)
        recursive: Whether to search recursively

    Returns:
        List of dicts with 'path' and 'mtime' keys, sorted by mtime (newest first)
    """
    results = []

    if not dir_path.exists():
        return results

    # Convert glob pattern to regex
    regex_pattern = pattern.replace('.', r'\.').replace('*', '.*').replace('?', '.')
    regex = re.compile(f'^{regex_pattern}$')

    def search_dir(current_dir: Path):
        try:
            for entry in current_dir.iterdir():
                if entry.is_file() and regex.match(entry.name):
                    mtime = entry.stat().st_mtime

                    if max_age is not None:
                        age_days = (datetime.now().timestamp() - mtime) / (60 * 60 * 24)
                        if age_days > max_age:
                            continue

                    results.append({'path': str(entry), 'mtime': mtime})

                elif entry.is_dir() and recursive:
                    search_dir(entry)
        except PermissionError:
            pass

    search_dir(dir_path)

    # Sort by modification time (newest first)
    results.sort(key=lambda x: x['mtime'], reverse=True)

    return results


def read_stdin_json() -> Dict[str, Any]:
    """Read JSON from stdin (for hook input)."""
    try:
        data = sys.stdin.read()
        if data.strip():
            return json.loads(data)
        return {}
    except json.JSONDecodeError:
        return {}


def log(message: str) -> None:
    """Log to stderr (visible to user in Claude Code)."""
    print(message, file=sys.stderr)


def output(data: Any) -> None:
    """Output to stdout (returned to Claude)."""
    if isinstance(data, (dict, list)):
        print(json.dumps(data))
    else:
        print(data)


def read_file(file_path: Path) -> Optional[str]:
    """Read a text file safely."""
    try:
        return file_path.read_text(encoding='utf-8')
    except (FileNotFoundError, PermissionError, UnicodeDecodeError):
        return None


def write_file(file_path: Path, content: str) -> None:
    """Write a text file."""
    ensure_dir(file_path.parent)
    file_path.write_text(content, encoding='utf-8')


def append_file(file_path: Path, content: str) -> None:
    """Append to a text file."""
    ensure_dir(file_path.parent)
    with open(file_path, 'a', encoding='utf-8') as f:
        f.write(content)


def command_exists(cmd: str) -> bool:
    """Check if a command exists in PATH."""
    # Validate command name - only allow alphanumeric, dash, underscore, dot
    if not re.match(r'^[a-zA-Z0-9_.-]+$', cmd):
        return False

    return shutil.which(cmd) is not None


def replace_in_file(file_path: Path, search: Pattern, replace: str) -> bool:
    """Replace text in a file (cross-platform sed alternative)."""
    content = read_file(file_path)
    if content is None:
        return False

    new_content = search.sub(replace, content)
    write_file(file_path, new_content)
    return True


def count_in_file(file_path: Path, pattern: Pattern) -> int:
    """Count occurrences of a pattern in a file."""
    content = read_file(file_path)
    if content is None:
        return 0

    matches = pattern.findall(content)
    return len(matches)


# Package manager definitions
PACKAGE_MANAGERS = {
    'npm': {
        'name': 'npm',
        'lock_file': 'package-lock.json',
        'install_cmd': 'npm install',
        'run_cmd': 'npm run',
        'exec_cmd': 'npx',
        'test_cmd': 'npm test',
        'build_cmd': 'npm run build',
        'dev_cmd': 'npm run dev'
    },
    'pnpm': {
        'name': 'pnpm',
        'lock_file': 'pnpm-lock.yaml',
        'install_cmd': 'pnpm install',
        'run_cmd': 'pnpm',
        'exec_cmd': 'pnpm dlx',
        'test_cmd': 'pnpm test',
        'build_cmd': 'pnpm build',
        'dev_cmd': 'pnpm dev'
    },
    'yarn': {
        'name': 'yarn',
        'lock_file': 'yarn.lock',
        'install_cmd': 'yarn',
        'run_cmd': 'yarn',
        'exec_cmd': 'yarn dlx',
        'test_cmd': 'yarn test',
        'build_cmd': 'yarn build',
        'dev_cmd': 'yarn dev'
    },
    'bun': {
        'name': 'bun',
        'lock_file': 'bun.lockb',
        'install_cmd': 'bun install',
        'run_cmd': 'bun run',
        'exec_cmd': 'bunx',
        'test_cmd': 'bun test',
        'build_cmd': 'bun run build',
        'dev_cmd': 'bun run dev'
    }
}

DETECTION_PRIORITY = ['pnpm', 'bun', 'yarn', 'npm']


def detect_package_manager(project_dir: Optional[Path] = None) -> Dict[str, Any]:
    """
    Detect the package manager for the current project.

    Detection priority:
    1. Environment variable CLAUDE_PACKAGE_MANAGER
    2. Project-specific config (in .claude/package-manager.json)
    3. package.json packageManager field
    4. Lock file detection
    5. Global user preference (in ~/.claude/package-manager.json)
    6. First available package manager (by priority)

    Returns:
        Dict with 'name', 'config', and 'source' keys
    """
    if project_dir is None:
        project_dir = Path.cwd()

    # 1. Check environment variable
    env_pm = os.environ.get('CLAUDE_PACKAGE_MANAGER')
    if env_pm and env_pm in PACKAGE_MANAGERS:
        return {
            'name': env_pm,
            'config': PACKAGE_MANAGERS[env_pm],
            'source': 'environment'
        }

    # 2. Check project-specific config
    project_config_path = project_dir / '.claude' / 'package-manager.json'
    if project_config_path.exists():
        try:
            config = json.loads(project_config_path.read_text())
            pm_name = config.get('packageManager')
            if pm_name and pm_name in PACKAGE_MANAGERS:
                return {
                    'name': pm_name,
                    'config': PACKAGE_MANAGERS[pm_name],
                    'source': 'project-config'
                }
        except (json.JSONDecodeError, KeyError):
            pass

    # 3. Check package.json packageManager field
    package_json_path = project_dir / 'package.json'
    if package_json_path.exists():
        try:
            pkg = json.loads(package_json_path.read_text())
            pm_field = pkg.get('packageManager', '')
            pm_name = pm_field.split('@')[0]
            if pm_name in PACKAGE_MANAGERS:
                return {
                    'name': pm_name,
                    'config': PACKAGE_MANAGERS[pm_name],
                    'source': 'package.json'
                }
        except (json.JSONDecodeError, KeyError):
            pass

    # 4. Check lock file
    for pm_name in DETECTION_PRIORITY:
        lock_file = project_dir / PACKAGE_MANAGERS[pm_name]['lock_file']
        if lock_file.exists():
            return {
                'name': pm_name,
                'config': PACKAGE_MANAGERS[pm_name],
                'source': 'lock-file'
            }

    # 5. Check global user preference
    global_config_path = get_claude_dir() / 'package-manager.json'
    if global_config_path.exists():
        try:
            config = json.loads(global_config_path.read_text())
            pm_name = config.get('packageManager')
            if pm_name and pm_name in PACKAGE_MANAGERS:
                return {
                    'name': pm_name,
                    'config': PACKAGE_MANAGERS[pm_name],
                    'source': 'global-config'
                }
        except (json.JSONDecodeError, KeyError):
            pass

    # 6. Use first available package manager
    for pm_name in DETECTION_PRIORITY:
        if command_exists(pm_name):
            return {
                'name': pm_name,
                'config': PACKAGE_MANAGERS[pm_name],
                'source': 'fallback'
            }

    # Default to npm
    return {
        'name': 'npm',
        'config': PACKAGE_MANAGERS['npm'],
        'source': 'default'
    }


def get_selection_prompt() -> str:
    """Get interactive prompt for package manager selection."""
    available = [pm for pm in PACKAGE_MANAGERS if command_exists(pm)]
    current = detect_package_manager()

    lines = ['[PackageManager] Available package managers:']

    for pm_name in available:
        indicator = ' (current)' if pm_name == current['name'] else ''
        lines.append(f'  - {pm_name}{indicator}')

    lines.append('')
    lines.append('To set your preferred package manager:')
    lines.append('  - Global: Set CLAUDE_PACKAGE_MANAGER environment variable')
    lines.append('  - Or add to ~/.claude/package-manager.json: {"packageManager": "pnpm"}')
    lines.append('  - Or add to package.json: {"packageManager": "pnpm@8"}')

    return '\n'.join(lines)
