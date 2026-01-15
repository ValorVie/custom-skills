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
