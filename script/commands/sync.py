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
    LFS_THRESHOLD_MB,
    check_lfs_available,
    count_directory_changes,
    detect_local_changes,
    detect_lfs_patterns,
    default_sync_directories,
    generate_sync_commit_message,
    get_claude_subdir,
    get_ignore_patterns,
    git_add_commit,
    git_init_or_clone,
    git_lfs_migrate_existing,
    git_lfs_setup,
    git_pull_rebase,
    git_push,
    git_status_summary,
    load_sync_config,
    make_repo_subdir_name,
    now_iso8601,
    restore_plugins_on_pull,
    save_plugin_manifest,
    save_sync_config,
    sync_directory,
    to_tilde_path,
    write_gitattributes,
    write_gitignore,
)

app = typer.Typer(help="管理跨裝置同步（Git backend）")
console = Console()

SUPPORTED_PROFILES = {"claude", "claude-mem", "custom"}

PULL_CHOICE_PUSH_THEN_PULL = "1"
PULL_CHOICE_FORCE_PULL = "2"
PULL_CHOICE_CANCEL = "3"


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


def _configure_lfs_tracking(repo_dir: Path, migrate_existing: bool) -> list[str]:
    lfs_patterns = detect_lfs_patterns(repo_dir, threshold_mb=LFS_THRESHOLD_MB)

    if not check_lfs_available():
        if lfs_patterns:
            console.print(
                "[yellow]警告：偵測到超過 "
                f"{LFS_THRESHOLD_MB} MB 的大型檔案，但未安裝 git-lfs。"
                "建議安裝後再執行 `ai-dev sync push`。[/yellow]"
            )
        return []

    if not git_lfs_setup(repo_dir):
        console.print("[yellow]警告：git-lfs 初始化失敗，將略過 LFS 設定[/yellow]")
        return []

    if not lfs_patterns:
        return []

    console.print(f"[cyan]Git LFS 自動追蹤：{', '.join(lfs_patterns)}[/cyan]")

    if migrate_existing:
        if git_lfs_migrate_existing(repo_dir, lfs_patterns):
            console.print("[cyan]已完成既有大檔案的 Git LFS migrate[/cyan]")
        else:
            console.print(
                "[yellow]警告：Git LFS migrate 失敗，請手動執行 `git lfs migrate`。[/yellow]"
            )

    return lfs_patterns


def _prompt_pull_safety(changes: dict[str, Any]) -> str:
    total_changes = int(changes.get("total_changes", 0))
    files = list(changes.get("files", []))

    console.print(
        f"[bold yellow]偵測到本機有 {total_changes} 個檔案尚未推送[/bold yellow]"
    )

    type_style = {
        "added": ("+", "green"),
        "modified": ("~", "yellow"),
        "deleted": ("-", "red"),
    }

    max_items = 10
    for item in files[:max_items]:
        rel_path = str(item.get("path", ""))
        change_type = str(item.get("type", "modified"))
        marker, color = type_style.get(change_type, ("~", "yellow"))
        console.print(f"  [{color}]{marker}[/{color}] {rel_path}")

    if total_changes > max_items:
        console.print(f"  [dim]...及其他 {total_changes - max_items} 個檔案[/dim]")

    console.print()
    console.print("1. 先 push 再 pull（推薦）")
    console.print("2. 強制 pull（覆蓋本機變更）")
    console.print("3. 取消")

    while True:
        choice = typer.prompt("請輸入選項 (1/2/3)", default="1").strip()
        if choice in {
            PULL_CHOICE_PUSH_THEN_PULL,
            PULL_CHOICE_FORCE_PULL,
            PULL_CHOICE_CANCEL,
        }:
            return choice
        console.print("[yellow]無效選項，請輸入 1、2 或 3[/yellow]")


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

    summary = {"added": 0, "updated": 0, "deleted": 0}

    # cloned = 遠端已有內容（第二台機器）→ 先 repo→local 還原
    if action == "cloned":
        for item in directories:
            repo_path = repo_dir / item["repo_subdir"]
            local_path = Path(item["path"]).expanduser()
            excludes = get_ignore_patterns(
                item.get("ignore_profile", "custom"), item.get("custom_ignore", [])
            )
            if not repo_path.exists() or not any(repo_path.iterdir()):
                continue
            local_path.mkdir(parents=True, exist_ok=True)
            result = sync_directory(
                repo_path, local_path, excludes=excludes, delete=False
            )
            summary["added"] += int(result.get("added", 0))
            summary["updated"] += int(result.get("updated", 0))

    # 產生 plugin manifest（第一台機器 push 時也會做，這裡確保 init 就有）
    for item in directories:
        if item.get("ignore_profile") == "claude":
            local_path = Path(item["path"]).expanduser()
            if local_path.exists():
                save_plugin_manifest(repo_dir, item["repo_subdir"], local_path)
            break

    # 再做 local→repo（將本機新增檔案同步回 repo）
    local_to_repo_summary = _sync_local_to_repo({"directories": directories})
    for key in summary:
        summary[key] += int(local_to_repo_summary.get(key, 0))

    lfs_patterns = _configure_lfs_tracking(
        repo_dir, migrate_existing=action in {"existing", "cloned"}
    )
    write_gitattributes(repo_dir, lfs_patterns=lfs_patterns)

    committed = git_add_commit(repo_dir, generate_sync_commit_message())

    if not git_pull_rebase(repo_dir):
        console.print("[bold red]git pull --rebase 失敗[/bold red]")
        raise typer.Exit(code=1)

    # init 時一律嘗試 push（確保遠端有內容）
    if not git_push(repo_dir):
        console.print("[bold red]git push 失敗，請確認遠端 URL 與權限[/bold red]")
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

    # 第二台機器：自動安裝 plugin
    if action == "cloned":
        claude_sub = None
        for item in directories:
            if item.get("ignore_profile") == "claude":
                claude_sub = item.get("repo_subdir")
                break
        if claude_sub:
            console.print()
            console.print("[bold]正在還原 Plugin...[/bold]")
            plugin_result = restore_plugins_on_pull(repo_dir, claude_sub)
            installed = plugin_result.get("installed", [])
            skipped = plugin_result.get("skipped", [])

            if installed:
                console.print(f"[green]  已自動安裝 {len(installed)} 個 plugin[/green]")
                for name in installed:
                    console.print(f"  [green]✓[/green] {name}")

            if skipped:
                console.print(
                    f"[yellow]  {len(skipped)} 個 plugin 需手動安裝：[/yellow]"
                )
                for name in skipped:
                    console.print(f"  [yellow]•[/yellow] {name}")

            if not installed and not skipped:
                console.print("[dim]  無 plugin 需要還原[/dim]")


@app.command()
def push() -> None:
    """同步本機變更到遠端。"""
    config = _load_config_or_exit(exit_code=1)
    repo_dir = _ensure_repo_dir()

    write_gitignore(repo_dir, config.get("directories", []))

    summary = _sync_local_to_repo(config)
    lfs_patterns = _configure_lfs_tracking(repo_dir, migrate_existing=False)
    write_gitattributes(repo_dir, lfs_patterns=lfs_patterns)

    # 產生 plugin manifest（可攜帶格式，無絕對路徑）
    claude_subdir = get_claude_subdir(config)
    if claude_subdir:
        save_plugin_manifest(repo_dir, claude_subdir)

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
    force: bool = typer.Option(
        False,
        "--force",
        help="跳過本機變更偵測，直接執行 pull",
    ),
) -> None:
    """從遠端拉取並同步到本機。"""
    config = _load_config_or_exit(exit_code=1)
    repo_dir = _ensure_repo_dir()

    if not force:
        changes = detect_local_changes(config)
        if int(changes.get("total_changes", 0)) > 0:
            choice = _prompt_pull_safety(changes)

            if choice == PULL_CHOICE_CANCEL:
                console.print("[dim]已取消[/dim]")
                return

            if choice == PULL_CHOICE_PUSH_THEN_PULL:
                console.print("[cyan]先執行 sync push，再繼續 pull...[/cyan]")
                push()
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
