import platform
import subprocess
import shutil
import sys
from typing import List, Optional
from rich.console import Console

console = Console()


def get_os() -> str:
    """Return 'windows', 'macos', or 'linux'."""
    system = platform.system().lower()
    if system == "darwin":
        return "macos"
    elif system == "windows":
        return "windows"
    return "linux"


def run_command(
    command: List[str], cwd: Optional[str] = None, check: bool = True
) -> subprocess.CompletedProcess:
    """Run a shell command."""
    try:
        # On Windows, shell=True is often needed for some commands to be found
        shell = True if get_os() == "windows" else False
        result = subprocess.run(
            command,
            cwd=cwd,
            check=check,
            text=True,
            capture_output=False,  # Let output stream to stdout
            shell=shell,
        )
        return result
    except subprocess.CalledProcessError as e:
        console.print(f"[bold red]Command failed:[/bold red] {' '.join(command)}")
        if check:
            sys.exit(1)
        return e


def check_command_exists(command: str) -> bool:
    """Check if a command exists in the path."""
    return shutil.which(command) is not None


def check_bun_installed() -> bool:
    """檢查 Bun 是否已安裝。"""
    return check_command_exists("bun")


def get_bun_version() -> str | None:
    """取得 Bun 版本號。"""
    try:
        result = subprocess.run(
            ["bun", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return None


def get_bun_package_version(package: str) -> str | None:
    """檢查 Bun 全域套件是否已安裝，並回傳版本號。"""
    try:
        result = subprocess.run(
            ["bun", "pm", "ls", "-g"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            # 解析輸出找尋套件版本
            # 輸出格式類似: "@openai/codex@1.0.0"
            for line in result.stdout.split("\n"):
                if package in line:
                    # 嘗試解析版本號
                    parts = line.strip().split("@")
                    if len(parts) >= 2:
                        # 最後一個 @ 後面的部分通常是版本號
                        version = parts[-1].strip()
                        if version and not version.startswith("/"):
                            return version
    except Exception:
        pass
    return None
