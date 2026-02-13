from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.table import Table

from ..utils.paths import get_sync_config_path, get_sync_repo_dir
from ..utils.system import check_command_exists
from ..utils.sync_config import (
    count_directory_changes,
    default_sync_directories,
    generate_sync_commit_message,
    get_ignore_patterns,
    git_add_commit,
    git_init_or_clone,
    git_pull_rebase,
    git_push,
    git_status_summary,
    load_sync_config,
    make_repo_subdir_name,
    now_iso8601,
    save_sync_config,
    sync_directory,
    to_tilde_path,
    write_gitattributes,
    write_gitignore,
)

app = typer.Typer(help="管理跨裝置同步（Git backend）")
console = Console()

SUPPORTED_PROFILES = {"claude", "claude-mem", "custom"}


def _ensure_repo_dir() -> Path:
    repo_dir = get_sync_repo_dir()
    repo_dir.mkdir(parents=True, exist_ok=True)
    return repo_dir


def _load_config_or_exit(exit_code: int = 1) -> dict[str, Any]:
    try:
        return load_sync_config()
    except FileNotFoundError:
        console.print(
            "[yellow]尚未初始化，請先執行 `ai-dev sync init --remote <url>`[/yellow]"
        )
        raise typer.Exit(code=exit_code)


def _resolve_path(raw_path: str) -> Path:
    return Path(raw_path).expanduser().resolve()


def _sync_local_to_repo(config: dict[str, Any]) -> dict[str, int]:
    repo_dir = _ensure_repo_dir()
    summary = {"added": 0, "updated": 0, "deleted": 0}

    for item in config.get("directories", []):
        local_path = Path(item["path"]).expanduser()
        repo_path = repo_dir / item["repo_subdir"]
        excludes = get_ignore_patterns(
            item.get("ignore_profile", "custom"), item.get("custom_ignore", [])
        )

        if not local_path.exists():
            console.print(f"[yellow]跳過不存在目錄：{local_path}[/yellow]")
            continue

        repo_path.mkdir(parents=True, exist_ok=True)
        result = sync_directory(local_path, repo_path, excludes=excludes, delete=True)
        summary["added"] += int(result.get("added", 0))
        summary["updated"] += int(result.get("updated", 0))
        summary["deleted"] += int(result.get("deleted", 0))

    return summary


def _sync_repo_to_local(config: dict[str, Any], delete: bool) -> dict[str, int]:
    repo_dir = _ensure_repo_dir()
    summary = {"added": 0, "updated": 0, "deleted": 0}

    for item in config.get("directories", []):
        repo_path = repo_dir / item["repo_subdir"]
        local_path = Path(item["path"]).expanduser()
        excludes = get_ignore_patterns(
            item.get("ignore_profile", "custom"), item.get("custom_ignore", [])
        )

        if not repo_path.exists():
            console.print(f"[yellow]跳過不存在子目錄：{repo_path}[/yellow]")
            continue

        local_path.mkdir(parents=True, exist_ok=True)
        result = sync_directory(repo_path, local_path, excludes=excludes, delete=delete)
        summary["added"] += int(result.get("added", 0))
        summary["updated"] += int(result.get("updated", 0))
        summary["deleted"] += int(result.get("deleted", 0))

    return summary


@app.command()
def init(
    remote: str = typer.Option(..., "--remote", help="Git remote URL"),
) -> None:
    """初始化 sync repo 與 sync.yaml 設定。"""
    if not check_command_exists("git"):
        console.print("[bold red]錯誤：找不到 Git，請先安裝 Git[/bold red]")
        raise typer.Exit(code=1)

    config_path = get_sync_config_path()
    if config_path.exists():
        confirmed = typer.confirm(
            "已存在 sync.yaml，是否重新初始化（覆蓋設定）？",
            default=False,
        )
        if not confirmed:
            console.print("[dim]已取消[/dim]")
            return

    repo_dir = _ensure_repo_dir()
    action = git_init_or_clone(repo_dir, remote)

    directories = default_sync_directories()
    for item in directories:
        (repo_dir / item["repo_subdir"]).mkdir(parents=True, exist_ok=True)

    write_gitignore(repo_dir, directories)
    write_gitattributes(repo_dir)

    summary = {"added": 0, "updated": 0, "deleted": 0}
    for item in directories:
        local_path = Path(item["path"]).expanduser()
        repo_path = repo_dir / item["repo_subdir"]
        excludes = get_ignore_patterns(
            item.get("ignore_profile", "custom"), item.get("custom_ignore", [])
        )

        if not local_path.exists():
            console.print(f"[yellow]跳過不存在目錄：{local_path}[/yellow]")
            continue

        result = sync_directory(local_path, repo_path, excludes=excludes, delete=True)
        summary["added"] += int(result.get("added", 0))
        summary["updated"] += int(result.get("updated", 0))
        summary["deleted"] += int(result.get("deleted", 0))

    committed = git_add_commit(repo_dir, generate_sync_commit_message())
    if committed:
        if not git_pull_rebase(repo_dir):
            raise typer.Exit(code=1)
        if not git_push(repo_dir):
            raise typer.Exit(code=1)

    config = {
        "version": "1",
        "remote": remote,
        "last_sync": now_iso8601(),
        "directories": directories,
    }
    save_sync_config(config)

    console.print("[bold green]sync 初始化完成[/bold green]")
    console.print(f"[dim]repo 狀態：{action}[/dim]")
    console.print(
        f"[dim]同步摘要：+{summary['added']} ~{summary['updated']} -{summary['deleted']}[/dim]"
    )


@app.command()
def push() -> None:
    """同步本機變更到遠端。"""
    config = _load_config_or_exit(exit_code=1)
    repo_dir = _ensure_repo_dir()

    write_gitignore(repo_dir, config.get("directories", []))
    write_gitattributes(repo_dir)

    summary = _sync_local_to_repo(config)
    committed = git_add_commit(repo_dir, generate_sync_commit_message())

    if not committed:
        console.print("[green]無變更需要同步[/green]")
        return

    if not git_pull_rebase(repo_dir):
        console.print("[bold red]git pull --rebase 失敗[/bold red]")
        raise typer.Exit(code=1)

    if not git_push(repo_dir):
        console.print("[bold red]git push 失敗[/bold red]")
        raise typer.Exit(code=1)

    config["last_sync"] = now_iso8601()
    save_sync_config(config)

    console.print("[bold green]sync push 完成[/bold green]")
    console.print(
        f"[dim]同步摘要：+{summary['added']} ~{summary['updated']} -{summary['deleted']}[/dim]"
    )


@app.command()
def pull(
    no_delete: bool = typer.Option(
        False,
        "--no-delete",
        help="拉取後同步到本機時，不刪除本機多出的檔案",
    ),
) -> None:
    """從遠端拉取並同步到本機。"""
    config = _load_config_or_exit(exit_code=1)
    repo_dir = _ensure_repo_dir()

    if not git_pull_rebase(repo_dir):
        console.print("[bold red]git pull --rebase 失敗[/bold red]")
        raise typer.Exit(code=1)

    summary = _sync_repo_to_local(config, delete=not no_delete)
    config["last_sync"] = now_iso8601()
    save_sync_config(config)

    console.print("[bold green]sync pull 完成[/bold green]")
    console.print(
        f"[dim]同步摘要：+{summary['added']} ~{summary['updated']} -{summary['deleted']}[/dim]"
    )


@app.command()
def status() -> None:
    """顯示同步狀態。"""
    try:
        config = load_sync_config()
    except FileNotFoundError:
        console.print(
            "[yellow]尚未初始化，請先執行 ai-dev sync init --remote <url>[/yellow]"
        )
        return

    repo_dir = get_sync_repo_dir()
    git_summary = (
        git_status_summary(repo_dir)
        if repo_dir.exists()
        else {
            "local_changes": 0,
            "behind_count": 0,
        }
    )

    remote_status = (
        "最新"
        if git_summary["behind_count"] == 0
        else f"落後 {git_summary['behind_count']} commits"
    )
    last_sync = str(config.get("last_sync") or "-")

    table = Table(title="Sync Status")
    table.add_column("Path", style="cyan")
    table.add_column("Local Changes", style="yellow")
    table.add_column("Remote", style="green")
    table.add_column("Last Sync", style="dim")

    for item in config.get("directories", []):
        local_path = Path(item["path"]).expanduser()
        repo_path = repo_dir / item["repo_subdir"]
        excludes = get_ignore_patterns(
            item.get("ignore_profile", "custom"), item.get("custom_ignore", [])
        )
        local_changes = count_directory_changes(local_path, repo_path, excludes)
        table.add_row(item["path"], str(local_changes), remote_status, last_sync)

    console.print(table)


@app.command()
def add(
    path: str = typer.Argument(..., help="要加入同步的目錄路徑"),
    profile: str = typer.Option("custom", "--profile", help="ignore profile"),
    ignore: list[str] = typer.Option(
        [],
        "--ignore",
        help="自訂排除規則，可重複指定",
    ),
) -> None:
    """新增同步目錄。"""
    if profile not in SUPPORTED_PROFILES:
        console.print(f"[bold red]錯誤：不支援的 profile：{profile}[/bold red]")
        raise typer.Exit(code=1)

    config = _load_config_or_exit(exit_code=1)
    target_path = _resolve_path(path)

    if not target_path.exists() or not target_path.is_dir():
        console.print(f"[bold red]錯誤：目錄不存在：{target_path}[/bold red]")
        raise typer.Exit(code=1)

    for item in config.get("directories", []):
        existing = _resolve_path(item["path"])
        if existing == target_path:
            console.print("[yellow]該目錄已在同步清單中[/yellow]")
            return

    existing_subdirs = {
        str(item.get("repo_subdir", "")) for item in config.get("directories", [])
    }
    repo_subdir = make_repo_subdir_name(target_path, existing_subdirs)

    entry = {
        "path": to_tilde_path(target_path),
        "repo_subdir": repo_subdir,
        "ignore_profile": profile,
        "custom_ignore": list(ignore),
    }
    config.setdefault("directories", []).append(entry)

    repo_dir = _ensure_repo_dir()
    (repo_dir / repo_subdir).mkdir(parents=True, exist_ok=True)
    write_gitignore(repo_dir, config.get("directories", []))
    save_sync_config(config)

    console.print(f"[green]已加入同步目錄：{entry['path']} -> {repo_subdir}/[/green]")


@app.command()
def remove(path: str = typer.Argument(..., help="要從同步清單移除的目錄路徑")) -> None:
    """移除同步目錄。"""
    config = _load_config_or_exit(exit_code=1)
    directories = config.get("directories", [])

    if len(directories) <= 1:
        console.print("[bold red]錯誤：至少保留一個同步目錄[/bold red]")
        raise typer.Exit(code=1)

    target_path = _resolve_path(path)
    target_index = None
    for index, item in enumerate(directories):
        if _resolve_path(item["path"]) == target_path:
            target_index = index
            break

    if target_index is None:
        console.print("[bold red]錯誤：該目錄不在同步清單中[/bold red]")
        raise typer.Exit(code=1)

    removed = directories.pop(target_index)
    repo_dir = _ensure_repo_dir()
    repo_subdir_path = repo_dir / removed["repo_subdir"]

    if repo_subdir_path.exists():
        should_delete = typer.confirm(
            f"是否刪除 repo 子目錄 {removed['repo_subdir']}/ ?",
            default=False,
        )
        if should_delete:
            shutil.rmtree(repo_subdir_path)

    write_gitignore(repo_dir, directories)
    save_sync_config(config)

    console.print(f"[green]已移除同步目錄：{removed['path']}[/green]")


if __name__ == "__main__":
    app()
