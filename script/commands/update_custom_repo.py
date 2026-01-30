from pathlib import Path

import typer
from rich.console import Console

from ..utils.custom_repos import load_custom_repos
from ..utils.system import run_command
from .update import (
    get_current_branch,
    check_for_updates,
    has_local_changes,
    backup_dirty_files,
)

console = Console()


def update_custom_repo():
    """更新所有自訂 repo。

    從 ~/.config/ai-dev/repos.yaml 讀取自訂 repo 清單，
    對每個 repo 執行 git fetch + reset 更新。

    注意：此指令不會分發 Skills 到各工具目錄。
    如需分發，請執行 `ai-dev clone`。
    """
    console.print("[bold blue]更新自訂 Repo...[/bold blue]")

    custom_repos = load_custom_repos().get("repos", {})

    if not custom_repos:
        console.print("[yellow]尚未設定任何自訂 repo[/yellow]")
        console.print("[dim]使用 ai-dev add-custom-repo 新增自訂 repo[/dim]")
        return

    backup_root = Path.home() / ".cache" / "ai-dev" / "backups"
    updated_repos: list[str] = []

    for repo_name, repo_info in custom_repos.items():
        local_path = Path(
            repo_info.get("local_path", "").replace("~", str(Path.home()))
        )
        if not local_path.exists() or not (local_path / ".git").exists():
            console.print(
                f"[yellow]⚠ Custom repo 目錄不存在，跳過: {repo_name}[/yellow]"
            )
            continue

        branch = repo_info.get("branch", "main")
        console.print(f"正在更新 {local_path} ({branch})...")

        run_command(
            ["git", "fetch", "--all"], cwd=str(local_path), check=False
        )

        has_updates = check_for_updates(local_path, branch)
        if has_updates:
            updated_repos.append(repo_name)

        if has_local_changes(local_path):
            backup_dirty_files(local_path, backup_root)

        remote_ref = f"origin/{branch}"
        run_command(
            ["git", "reset", "--hard", remote_ref],
            cwd=str(local_path),
            check=False,
        )

    # 顯示更新摘要
    if updated_repos:
        console.print()
        console.print("[bold cyan]以下自訂 repo 有新更新：[/bold cyan]")
        for name in updated_repos:
            console.print(f"  • {name}")
    else:
        console.print()
        console.print("[dim]所有自訂 repo 皆為最新[/dim]")

    console.print("[bold green]自訂 Repo 更新完成！[/bold green]")
    console.print()
    console.print("[dim]提示：如需分發 Skills 到各工具目錄，請執行：ai-dev clone[/dim]")
