import typer
import subprocess
import shutil
from datetime import datetime
from pathlib import Path
from rich.console import Console
from ..utils.system import (
    run_command,
    check_bun_installed,
)
from ..utils.paths import (
    get_custom_skills_dir,
    get_superpowers_dir,
    get_uds_dir,
    get_opencode_config_dir,
    get_obsidian_skills_dir,
    get_anthropic_skills_dir,
    get_ecc_dir,
)
from ..utils.shared import (
    NPM_PACKAGES,
    BUN_PACKAGES,
    update_claude_code,
    check_uds_initialized,
    sync_opencode_superpowers_repo,
    refresh_opencode_superpowers_symlinks,
)

app = typer.Typer()
console = Console()


def get_current_branch(repo: Path) -> str | None:
    """取得當前分支名稱。"""
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=str(repo),
        capture_output=True,
        text=True,
    )
    if result.returncode == 0 and result.stdout.strip():
        return result.stdout.strip()
    return None


def has_local_changes(repo: Path) -> bool:
    """檢查是否有本地修改（已追蹤檔案的變更）。

    只檢查已追蹤檔案的修改，不包含 untracked 檔案。
    """
    # 檢查 staged 和 unstaged 的已追蹤檔案變更
    result = subprocess.run(
        ["git", "diff", "--name-only", "HEAD"],
        cwd=str(repo),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return False

    # 也檢查 staged changes
    staged = subprocess.run(
        ["git", "diff", "--name-only", "--cached"],
        cwd=str(repo),
        capture_output=True,
        text=True,
    )

    return bool(result.stdout.strip() or staged.stdout.strip())


def check_for_updates(repo: Path, branch: str | None) -> bool:
    """檢查儲存庫是否有可用的更新。

    在 fetch 後比較本地 HEAD 與遠端分支的 commit。
    """
    if not branch:
        return False

    remote_ref = f"origin/{branch}"

    # 取得本地 HEAD commit
    local_result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=str(repo),
        capture_output=True,
        text=True,
    )
    if local_result.returncode != 0:
        return False

    # 取得遠端 commit
    remote_result = subprocess.run(
        ["git", "rev-parse", remote_ref],
        cwd=str(repo),
        capture_output=True,
        text=True,
    )
    if remote_result.returncode != 0:
        return False

    return local_result.stdout.strip() != remote_result.stdout.strip()


def backup_dirty_files(repo: Path, backup_root: Path) -> bool:
    """備份儲存庫中已追蹤但未提交的檔案。

    只備份已追蹤檔案的本地修改，不備份 untracked 檔案。
    如果沒有本地修改，不進行備份。
    """
    # 取得已追蹤但有修改的檔案
    result = subprocess.run(
        ["git", "diff", "--name-only", "HEAD"],
        cwd=str(repo),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return False

    dirty_files = []
    if result.stdout.strip():
        dirty_files.extend(result.stdout.strip().split("\n"))

    # 也取得 staged 的修改
    staged = subprocess.run(
        ["git", "diff", "--name-only", "--cached"],
        cwd=str(repo),
        capture_output=True,
        text=True,
    )
    if staged.stdout.strip():
        for f in staged.stdout.strip().split("\n"):
            if f and f not in dirty_files:
                dirty_files.append(f)

    if not dirty_files:
        return False

    # 建立備份目錄（使用使用者目錄而非安裝目錄）
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = backup_root / repo.name / timestamp
    backup_dir.mkdir(parents=True, exist_ok=True)

    # 複製檔案
    backed_up = 0
    for file_path in dirty_files:
        src = repo / file_path
        if src.exists() and src.is_file():
            dst = backup_dir / file_path
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            backed_up += 1

    if backed_up > 0:
        console.print(
            f"[yellow]已備份 {backed_up} 個已修改檔案到 {backup_dir}[/yellow]"
        )
        return True
    return False


@app.command()
def update(
    skip_npm: bool = typer.Option(False, "--skip-npm", help="跳過 NPM 套件更新"),
    skip_bun: bool = typer.Option(False, "--skip-bun", help="跳過 Bun 套件更新"),
    skip_repos: bool = typer.Option(False, "--skip-repos", help="跳過 Git 儲存庫更新"),
):
    """更新工具與拉取儲存庫。

    此指令負責：
    1. 更新 Claude Code（除非 --skip-npm）
    2. 更新全域 NPM 套件（除非 --skip-npm）
    3. 拉取 ~/.config/ 下的所有 repo（除非 --skip-repos）

    注意：此指令不會分發 Skills 到各工具目錄。
    如需分發，請執行 `ai-dev clone`。
    """
    console.print("[bold blue]開始更新...[/bold blue]")

    # 1. 更新 Claude Code
    if skip_npm:
        console.print("[yellow]跳過 Claude Code 更新[/yellow]")
    else:
        update_claude_code()

    # 2. 更新全域 NPM 工具
    if skip_npm:
        console.print("[yellow]跳過 NPM 套件更新[/yellow]")
    else:
        console.print("[green]正在更新全域 NPM 套件...[/green]")
        total = len(NPM_PACKAGES)
        for i, package in enumerate(NPM_PACKAGES, 1):
            console.print(f"[bold cyan][{i}/{total}] 正在更新 {package}...[/bold cyan]")
            run_command(["npm", "install", "-g", package])

        # 執行 uds update（僅在專案已初始化時）
        if check_uds_initialized():
            console.print("[green]正在更新專案 Standards...[/green]")
            run_command(["uds", "update"], check=False)
        else:
            console.print("[dim]ℹ️  當前目錄未初始化 Standards（跳過 uds update）[/dim]")
            console.print("[dim]   如需在此專案使用，請執行: uds init[/dim]")

        # 執行 npx skills update（更新已安裝的第三方 Skills）
        console.print("[green]正在更新已安裝的 Skills...[/green]")
        run_command(["npx", "skills", "update"], check=False)

    # 2.5 更新 Bun 套件
    if skip_bun:
        console.print("[yellow]跳過 Bun 套件更新[/yellow]")
    else:
        console.print("[green]正在更新 Bun 套件...[/green]")
        if check_bun_installed():
            total = len(BUN_PACKAGES)
            for i, package in enumerate(BUN_PACKAGES, 1):
                console.print(
                    f"[bold cyan][{i}/{total}] 正在更新 {package}...[/bold cyan]"
                )
                run_command(["bun", "install", "-g", package])
        else:
            console.print("[yellow]⚠️  Bun 未安裝，跳過 Bun 套件更新[/yellow]")

    # 3. 更新儲存庫
    if skip_repos:
        console.print("[yellow]跳過 Git 儲存庫更新[/yellow]")
    else:
        console.print("[green]正在更新儲存庫...[/green]")

        # 確保 OpenCode superpowers 存在（git pull，若不存在則 clone）
        opencode_superpowers_repo = sync_opencode_superpowers_repo()

        repos = [
            get_custom_skills_dir(),
            get_superpowers_dir(),
            get_uds_dir(),
            get_opencode_config_dir() / "superpowers",
            get_obsidian_skills_dir(),
            get_anthropic_skills_dir(),
            get_ecc_dir(),
        ]

        # 備份目錄位於使用者目錄
        backup_root = Path.home() / ".cache" / "ai-dev" / "backups"

        # 記錄有更新的儲存庫
        updated_repos: list[str] = []

        for repo in repos:
            if repo.exists() and (repo / ".git").exists():
                # 取得當前分支
                current_branch = get_current_branch(repo)
                branch_info = f" ({current_branch})" if current_branch else ""
                console.print(f"正在更新 {repo}{branch_info}...")
                # 先 fetch 遠端
                run_command(["git", "fetch", "--all"], cwd=str(repo), check=False)
                # 檢查是否有更新
                has_updates = check_for_updates(repo, current_branch)
                if has_updates:
                    updated_repos.append(repo.name)
                # 只有當本地有修改時才備份
                if has_local_changes(repo):
                    backup_dirty_files(repo, backup_root)
                # 強制更新：重置到當前分支對應的遠端分支
                remote_ref = (
                    f"origin/{current_branch}" if current_branch else "origin/HEAD"
                )
                run_command(
                    ["git", "reset", "--hard", remote_ref],
                    cwd=str(repo),
                    check=False,
                )

        # 更新 custom repos
        from ..utils.custom_repos import load_custom_repos

        custom_repos = load_custom_repos().get("repos", {})
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
            run_command(["git", "fetch", "--all"], cwd=str(local_path), check=False)
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

        # 更新完成後刷新 OpenCode symlink（保持冪等）
        refresh_opencode_superpowers_symlinks(opencode_superpowers_repo)

        # 顯示更新摘要
        if updated_repos:
            console.print()
            console.print("[bold cyan]以下儲存庫有新更新：[/bold cyan]")
            for name in updated_repos:
                console.print(f"  • {name}")
        else:
            console.print()
            console.print("[dim]所有儲存庫皆為最新[/dim]")

    console.print("[bold green]更新完成！[/bold green]")
    console.print()
    console.print("[dim]提示：如需分發 Skills 到各工具目錄，請執行：ai-dev clone[/dim]")
