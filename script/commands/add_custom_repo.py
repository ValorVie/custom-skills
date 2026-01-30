import subprocess
from pathlib import Path

import typer
from rich.console import Console

from .add_repo import parse_repo_url
from ..utils.custom_repos import (
    add_custom_repo as _add_custom_repo,
    validate_repo_structure,
)

console = Console()


def clone_repo(url: str, target_dir: Path) -> bool:
    """Clone repo 到指定目錄。"""
    console.print(f"[cyan]正在 clone {url}...[/cyan]")

    result = subprocess.run(
        ["git", "clone", url, str(target_dir)],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        console.print(f"[red]Clone 失敗: {result.stderr}[/red]")
        return False

    console.print(f"[green]✓ Clone 完成: {target_dir}[/green]")
    return True


def add_custom_repo(
    remote_path: str = typer.Argument(
        ..., help="遠端 repo 路徑 (例如: owner/repo 或完整 URL)"
    ),
    name: str = typer.Option(
        None, "--name", "-n", help="自訂名稱（預設使用 repo 名稱）"
    ),
    branch: str = typer.Option("main", "--branch", "-b", help="追蹤的分支"),
    fix: bool = typer.Option(
        False, "--fix", help="自動建立缺少的目錄（含 .gitkeep）"
    ),
):
    """新增自訂 repo 並開始追蹤。

    此指令會：
    1. Clone repo 到 ~/.config/<repo-name>/
    2. 驗證 repo 目錄結構
    3. 將 repo 資訊寫入 ~/.config/ai-dev/repos.yaml

    範例：
        ai-dev add-custom-repo owner/repo
        ai-dev add-custom-repo https://github.com/owner/repo
        ai-dev add-custom-repo git@github.com:owner/repo.git
        ai-dev add-custom-repo owner/repo --name my-custom-name
        ai-dev add-custom-repo owner/repo --branch develop
        ai-dev add-custom-repo owner/repo --fix
    """
    console.print("[bold blue]新增自訂 Repo[/bold blue]")

    # 解析 URL
    try:
        repo_name, repo_path, default_branch = parse_repo_url(remote_path)
    except ValueError as e:
        console.print(f"[red]錯誤: {e}[/red]")
        raise typer.Exit(1)

    # 使用自訂名稱或 repo 名稱
    name = name or repo_name
    branch = branch or default_branch

    # 判斷 clone URL：SSH 格式保留原始 URL，否則用 HTTPS
    if remote_path.startswith("git@"):
        clone_url = remote_path
    else:
        clone_url = f"https://github.com/{repo_path}.git"

    # 目標目錄
    target_dir = Path.home() / ".config" / name
    local_path = f"~/.config/{name}/"

    console.print(f"  Repo: {repo_path}")
    console.print(f"  名稱: {name}")
    console.print(f"  分支: {branch}")
    console.print(f"  目錄: {target_dir}")

    # Clone repo
    if target_dir.exists():
        console.print(f"[yellow]⚠ 目錄已存在: {target_dir}[/yellow]")
        console.print("[yellow]  跳過 clone，繼續執行後續步驟[/yellow]")
    else:
        if not clone_repo(clone_url, target_dir):
            raise typer.Exit(1)

    # 驗證 repo 結構
    console.print()
    console.print("[cyan]驗證目錄結構...[/cyan]")
    validate_repo_structure(target_dir, auto_fix=fix)

    # 寫入設定檔
    console.print()
    _add_custom_repo(name, clone_url, branch, local_path)

    console.print()
    console.print("[bold green]✓ 完成！[/bold green]")
    console.print()
    console.print("[dim]下一步：[/dim]")
    console.print("[dim]  1. 分發資源到各工具: ai-dev clone[/dim]")
    console.print("[dim]  2. 更新所有儲存庫: ai-dev update[/dim]")
