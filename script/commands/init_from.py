import subprocess
from pathlib import Path

import typer
from rich.console import Console

from .add_repo import parse_repo_url
from ..utils.custom_repos import add_custom_repo as _add_custom_repo, load_custom_repos
from ..utils.project_tracking import (
    create_tracking_file,
    load_tracking_file,
    update_tracking_file,
)
from ..utils.gitignore_downstream import merge_gitignore_downstream
from ..utils.smart_merge import merge_template

console = Console()


def _clone_template_repo(url: str, target_dir: Path) -> bool:
    """Clone 模板 repo 到指定目錄。"""
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


def _pull_template_repo(local_path: Path, branch: str) -> bool:
    """拉取模板 repo 最新更新。"""
    console.print(f"[cyan]正在拉取最新更新 ({branch})...[/cyan]")

    result = subprocess.run(
        ["git", "fetch", "--all"],
        cwd=str(local_path),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        console.print(f"[yellow]⚠ fetch 失敗: {result.stderr}[/yellow]")

    result = subprocess.run(
        ["git", "reset", "--hard", f"origin/{branch}"],
        cwd=str(local_path),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        console.print(f"[red]拉取失敗: {result.stderr}[/red]")
        return False

    console.print("[green]✓ 已更新到最新版本[/green]")
    return True


def init_from(
    source: str = typer.Argument(
        None,
        help="模板 repo 來源（owner/repo、完整 HTTPS URL、SSH URL）",
    ),
    name: str = typer.Option(
        None, "--name", "-n", help="自訂名稱（預設使用 repo 名稱）"
    ),
    branch: str = typer.Option("main", "--branch", "-b", help="追蹤的分支"),
    update: bool = typer.Option(
        False, "--update", help="更新模式：從現有 .ai-dev-project.yaml 拉取並重新合併"
    ),
    force: bool = typer.Option(
        False, "--force", help="強制覆蓋所有衝突檔案，不提示"
    ),
    skip_conflicts: bool = typer.Option(
        False, "--skip-conflicts", help="跳過所有衝突檔案，不提示"
    ),
):
    """從客製化模板 repo 初始化專案目錄。

    此指令會：
    1. Clone（或更新）模板 repo 到 ~/.config/<name>/
    2. 將模板 repo 記錄到 ~/.config/ai-dev/repos.yaml（type: template）
    3. 智慧合併：逐檔比對內容，讓你選擇附加/覆蓋/跳過
    4. 建立 .ai-dev-project.yaml 追蹤哪些檔案由此模板管理

    範例：
        ai-dev init-from ValorVie/qdm-ai-base
        ai-dev init-from https://github.com/ValorVie/qdm-ai-base
        ai-dev init-from ValorVie/qdm-ai-base --branch develop
        ai-dev init-from --update
        ai-dev init-from ValorVie/qdm-ai-base --force
        ai-dev init-from ValorVie/qdm-ai-base --skip-conflicts
    """
    cwd = Path.cwd()

    # --update 模式
    if update:
        _run_update_mode(cwd=cwd, force=force, skip_conflicts=skip_conflicts)
        return

    # 首次初始化：需要 source
    if not source:
        console.print(
            "[red]錯誤：請提供模板 repo 來源，或使用 --update 更新已初始化的專案[/red]"
        )
        console.print(
            "[dim]  範例：ai-dev init-from ValorVie/qdm-ai-base[/dim]"
        )
        raise typer.Exit(1)

    console.print("[bold blue]初始化模板[/bold blue]")

    # 解析 URL
    try:
        repo_name, repo_path, default_branch = parse_repo_url(source)
    except ValueError as e:
        console.print(f"[red]錯誤: {e}[/red]")
        raise typer.Exit(1)

    final_name = name or repo_name
    final_branch = branch or default_branch

    # 決定 clone URL
    if source.startswith("git@"):
        clone_url = source
    elif source.startswith("http"):
        clone_url = source if source.endswith(".git") else source + ".git"
    else:
        clone_url = f"https://github.com/{repo_path}.git"

    target_dir = Path.home() / ".config" / final_name
    local_path_str = f"~/.config/{final_name}/"

    console.print(f"  模板: {repo_path}")
    console.print(f"  名稱: {final_name}")
    console.print(f"  分支: {final_branch}")
    console.print(f"  目錄: {target_dir}")
    console.print(f"  目標: {cwd}")
    console.print()

    # Clone（若目錄已存在則跳過）
    if target_dir.exists():
        console.print(f"[yellow]⚠ 模板目錄已存在，跳過 clone：{target_dir}[/yellow]")
    else:
        if not _clone_template_repo(clone_url, target_dir):
            raise typer.Exit(1)

    # 寫入 repos.yaml（若尚未存在）
    existing_repos = load_custom_repos().get("repos", {})
    if final_name not in existing_repos:
        _add_custom_repo(
            name=final_name,
            url=clone_url,
            branch=final_branch,
            local_path=local_path_str,
            repo_type="template",
        )
    else:
        console.print(f"[dim]  {final_name} 已存在於 repos.yaml，跳過寫入[/dim]")

    # 智慧合併
    console.print()
    console.print("[bold]開始智慧合併...[/bold]")
    managed_files, stats = merge_template(
        template_dir=target_dir,
        target_dir=cwd,
        force=force,
        skip_conflicts=skip_conflicts,
    )

    # 合併 .gitignore-downstream
    merge_gitignore_downstream(
        template_dir=target_dir,
        target_dir=cwd,
        template_name=final_name,
    )

    # 建立追蹤檔
    create_tracking_file(
        name=final_name,
        url=clone_url,
        branch=final_branch,
        managed_files=managed_files,
        project_dir=cwd,
    )

    stats.print_summary()
    console.print()
    console.print("[bold green]✓ 初始化完成！[/bold green]")
    console.print(
        f"[dim]  已建立 .ai-dev-project.yaml（追蹤 {len(managed_files)} 個檔案）[/dim]"
    )
    console.print()
    console.print("[dim]下一步：[/dim]")
    console.print("[dim]  執行 `ai-dev clone` 分發通用工具到全域目錄[/dim]")
    console.print("[dim]  執行 `ai-dev update` 更新所有儲存庫[/dim]")


def _run_update_mode(
    cwd: Path,
    force: bool,
    skip_conflicts: bool,
) -> None:
    """執行 --update 模式：從現有追蹤檔案拉取並重新合併。"""
    console.print("[bold blue]更新模板（--update 模式）[/bold blue]")

    # 讀取追蹤檔
    tracking = load_tracking_file(cwd)
    if tracking is None:
        console.print(
            "[red]錯誤：找不到 .ai-dev-project.yaml[/red]"
        )
        console.print(
            "[dim]  請先執行 `ai-dev init-from <source>` 初始化專案[/dim]"
        )
        raise typer.Exit(1)

    template_info = tracking.get("template", {})
    template_name = template_info.get("name", "")
    template_branch = template_info.get("branch", "main")
    existing_managed = set(tracking.get("managed_files", []))

    if not template_name:
        console.print("[red]錯誤：.ai-dev-project.yaml 中缺少 template.name[/red]")
        raise typer.Exit(1)

    template_dir = Path.home() / ".config" / template_name

    if not template_dir.exists():
        console.print(f"[red]錯誤：模板目錄不存在：{template_dir}[/red]")
        console.print(
            "[dim]  請重新執行 `ai-dev init-from <source>` 來重新 clone[/dim]"
        )
        raise typer.Exit(1)

    console.print(f"  模板: {template_name}")
    console.print(f"  分支: {template_branch}")
    console.print(f"  目標: {cwd}")
    console.print()

    # 拉取最新
    if not _pull_template_repo(template_dir, template_branch):
        raise typer.Exit(1)

    # 合併所有模板檔案（包含上游新增的）
    console.print()
    console.print("[bold]合併模板檔案...[/bold]")
    managed_files, stats = merge_template(
        template_dir=template_dir,
        target_dir=cwd,
        force=force,
        skip_conflicts=skip_conflicts,
    )

    # 合併 .gitignore-downstream（支援新增/更新/移除）
    merge_gitignore_downstream(
        template_dir=template_dir,
        target_dir=cwd,
        template_name=template_name,
        remove_if_missing=True,
    )

    # 合併既有追蹤清單（保留使用者跳過但先前已管理的檔案）
    all_managed = sorted(set(managed_files) | existing_managed)
    update_tracking_file(managed_files=all_managed, project_dir=cwd)

    stats.print_summary()
    console.print()
    console.print("[bold green]✓ 更新完成！[/bold green]")
