import typer
import subprocess
import shutil
from datetime import datetime
from pathlib import Path
from rich.console import Console
from ..utils.system import run_command
from ..utils.paths import (
    get_custom_skills_dir,
    get_superpowers_dir,
    get_uds_dir,
    get_opencode_config_dir,
    get_obsidian_skills_dir,
    get_anthropic_skills_dir,
)
from ..utils.shared import NPM_PACKAGES, copy_skills

app = typer.Typer()
console = Console()


def backup_dirty_files(repo: Path, backup_root: Path) -> bool:
    """備份儲存庫中未提交的檔案。返回是否有檔案被備份。"""
    # 取得有更改的檔案列表
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=str(repo),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0 or not result.stdout.strip():
        return False

    # 解析檔案列表
    dirty_files = []
    for line in result.stdout.strip().split("\n"):
        if line:
            # git status --porcelain 格式: "XY filename" 或 "XY original -> renamed"
            file_path = line[3:].split(" -> ")[-1]  # 取得最終檔名
            dirty_files.append(file_path)

    if not dirty_files:
        return False

    # 建立備份目錄
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = backup_root / repo.name / timestamp
    backup_dir.mkdir(parents=True, exist_ok=True)

    # 複製檔案
    backed_up = 0
    for file_path in dirty_files:
        src = repo / file_path
        if src.exists():
            dst = backup_dir / file_path
            dst.parent.mkdir(parents=True, exist_ok=True)
            if src.is_file():
                shutil.copy2(src, dst)
                backed_up += 1

    if backed_up > 0:
        console.print(f"[yellow]已備份 {backed_up} 個檔案到 {backup_dir}[/yellow]")
        return True
    return False


@app.command()
def update(
    skip_npm: bool = typer.Option(False, "--skip-npm", help="跳過 NPM 套件更新"),
    skip_repos: bool = typer.Option(False, "--skip-repos", help="跳過 Git 儲存庫更新"),
    skip_skills: bool = typer.Option(False, "--skip-skills", help="跳過複製 Skills"),
    sync_project: bool = typer.Option(
        True,
        "--sync-project/--no-sync-project",
        help="是否同步到專案目錄（預設：是）",
    ),
):
    """每日更新：更新工具並同步設定。"""
    console.print("[bold blue]開始更新...[/bold blue]")

    # 1. 更新全域 NPM 工具
    if skip_npm:
        console.print("[yellow]跳過 NPM 套件更新[/yellow]")
    else:
        console.print("[green]正在更新全域 NPM 套件...[/green]")
        total = len(NPM_PACKAGES)
        for i, package in enumerate(NPM_PACKAGES, 1):
            console.print(f"[bold cyan][{i}/{total}] 正在更新 {package}...[/bold cyan]")
            run_command(["npm", "install", "-g", package])

        # 執行 uds update
        run_command(["uds", "update"], check=False)

    # 2. 更新儲存庫
    if skip_repos:
        console.print("[yellow]跳過 Git 儲存庫更新[/yellow]")
    else:
        console.print("[green]正在更新儲存庫...[/green]")
        repos = [
            get_custom_skills_dir(),
            get_superpowers_dir(),
            get_uds_dir(),
            get_opencode_config_dir() / "superpowers",
            get_obsidian_skills_dir(),
            get_anthropic_skills_dir(),
        ]

        # 備份目錄位於專案根目錄
        backup_root = Path(__file__).resolve().parent.parent.parent / "backups"

        for repo in repos:
            if repo.exists() and (repo / ".git").exists():
                console.print(f"正在更新 {repo}...")
                # 先備份未提交的更改
                backup_dirty_files(repo, backup_root)
                # 強制更新：取得遠端最新並重置本地更改
                run_command(["git", "fetch", "--all"], cwd=str(repo), check=False)
                run_command(
                    ["git", "reset", "--hard", "origin/HEAD"],
                    cwd=str(repo),
                    check=False,
                )

    # 3. 重新同步 Skills（Stage 2 + Stage 3）
    if skip_skills:
        console.print("[yellow]跳過複製 Skills[/yellow]")
    else:
        console.print("[green]正在重新同步 Skills...[/green]")
        copy_skills(sync_project=sync_project)

    console.print("[bold green]更新完成！[/bold green]")
