from __future__ import annotations

import shutil
import subprocess
from datetime import datetime
from pathlib import Path

from rich.console import Console

from script.models.execution_plan import ExecutionPlan
from script.utils.custom_repos import load_custom_repos
from script.utils.paths import (
    get_antigravity_config_dir,
    get_claude_agents_dir,
    get_claude_config_dir,
    get_claude_workflows_dir,
    get_codex_config_dir,
    get_codex_superpowers_dir,
    get_config_dir,
    get_custom_skills_dir,
    get_gemini_cli_config_dir,
    get_obsidian_skills_dir,
    get_anthropic_skills_dir,
    get_ecc_dir,
    get_auto_skill_repo_dir,
    get_opencode_config_dir,
    get_superpowers_dir,
    get_uds_dir,
)
from script.utils.shared import (
    REPOS,
    migrate_opencode_superpowers,
    sync_codex_superpowers_repo,
    refresh_codex_superpowers_symlinks,
)
from script.utils.system import check_command_exists, run_command

console = Console()

def get_current_branch(repo: Path) -> str | None:
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
    result = subprocess.run(
        ["git", "diff", "--name-only", "HEAD"],
        cwd=str(repo),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return False

    staged = subprocess.run(
        ["git", "diff", "--name-only", "--cached"],
        cwd=str(repo),
        capture_output=True,
        text=True,
    )

    return bool(result.stdout.strip() or staged.stdout.strip())


def check_for_updates(repo: Path, branch: str | None) -> bool:
    if not branch:
        return False

    remote_ref = f"origin/{branch}"
    local_result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=str(repo),
        capture_output=True,
        text=True,
    )
    if local_result.returncode != 0:
        return False

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
    result = subprocess.run(
        ["git", "diff", "--name-only", "HEAD"],
        cwd=str(repo),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return False

    dirty_files: list[str] = []
    if result.stdout.strip():
        dirty_files.extend(result.stdout.strip().split("\n"))

    staged = subprocess.run(
        ["git", "diff", "--name-only", "--cached"],
        cwd=str(repo),
        capture_output=True,
        text=True,
    )
    if staged.stdout.strip():
        for file_path in staged.stdout.strip().split("\n"):
            if file_path and file_path not in dirty_files:
                dirty_files.append(file_path)

    if not dirty_files:
        return False

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = backup_root / repo.name / timestamp
    backup_dir.mkdir(parents=True, exist_ok=True)

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


def _ensure_install_directories() -> None:
    console.print("[green]正在建立目錄...[/green]")
    dirs = [
        get_config_dir(),
        get_custom_skills_dir(),
        get_superpowers_dir(),
        get_uds_dir(),
        get_claude_config_dir() / "skills",
        get_claude_config_dir() / "commands",
        get_claude_agents_dir(),
        get_claude_workflows_dir(),
        get_antigravity_config_dir() / "global_skills",
        get_antigravity_config_dir() / "global_workflows",
        get_opencode_config_dir() / "skills",
        get_opencode_config_dir() / "commands",
        get_opencode_config_dir() / "agents",
        get_codex_config_dir() / "skills",
        get_gemini_cli_config_dir() / "skills",
        get_gemini_cli_config_dir() / "commands",
    ]
    for path in dirs:
        path.mkdir(parents=True, exist_ok=True)


def _run_install_repos_phase() -> None:
    if not check_command_exists("git"):
        console.print("[bold red]✗ 找不到 Git[/bold red]")
        raise SystemExit(1)

    _ensure_install_directories()

    console.print("[green]正在 Clone 儲存庫...[/green]")
    for _, (url, get_path) in REPOS.items():
        path = get_path()
        if not (path / ".git").exists():
            console.print(f"正在 Clone {url} 到 {path}...")
            run_command(["git", "clone", url, str(path)])
        else:
            console.print(f"{path} 已存在，跳過 Clone。")

    # OpenCode superpowers：遷移至 plugin 機制
    migrate_opencode_superpowers()

    # Codex superpowers：clone + symlink
    codex_sp_repo = sync_codex_superpowers_repo()
    refresh_codex_superpowers_symlinks(codex_sp_repo)

    custom_repos = load_custom_repos().get("repos", {})
    if custom_repos:
        console.print("[green]正在 Clone 自訂儲存庫...[/green]")
        for repo_name, repo_info in custom_repos.items():
            local_path = Path(
                repo_info.get("local_path", "").replace("~", str(Path.home()))
            )
            if (local_path / ".git").exists():
                console.print(f"{local_path} 已存在，跳過 Clone。")
                continue

            url = repo_info.get("url", "")
            console.print(f"正在 Clone {url} 到 {local_path}...")
            result = run_command(["git", "clone", url, str(local_path)], check=False)
            if result and result.returncode != 0:
                console.print(f"[yellow]⚠ Clone {repo_name} 失敗，跳過[/yellow]")


def _run_update_repos_phase() -> None:
    console.print("[green]正在更新儲存庫...[/green]")
    # OpenCode superpowers：遷移至 plugin 機制
    migrate_opencode_superpowers()

    repos = [
        get_custom_skills_dir(),
        get_superpowers_dir(),
        get_uds_dir(),
        get_codex_superpowers_dir(),
        get_obsidian_skills_dir(),
        get_anthropic_skills_dir(),
        get_ecc_dir(),
        get_auto_skill_repo_dir(),
    ]

    backup_root = Path.home() / ".cache" / "ai-dev" / "backups"
    updated_repos: list[str] = []
    missing_repos: list[str] = []

    for repo in repos:
        if not repo.exists() or not (repo / ".git").exists():
            missing_repos.append(str(repo))
            continue

        branch = get_current_branch(repo)
        branch_info = f" ({branch})" if branch else ""
        console.print(f"正在更新 {repo}{branch_info}...")
        run_command(["git", "fetch", "--all"], cwd=str(repo), check=False)
        if check_for_updates(repo, branch):
            updated_repos.append(repo.name)
        if has_local_changes(repo):
            backup_dirty_files(repo, backup_root)
        remote_ref = f"origin/{branch}" if branch else "origin/HEAD"
        run_command(["git", "reset", "--hard", remote_ref], cwd=str(repo), check=False)

    # Codex superpowers symlink 刷新
    codex_sp = get_codex_superpowers_dir()
    if codex_sp.exists() and (codex_sp / ".git").exists():
        refresh_codex_superpowers_symlinks(codex_sp)

    if missing_repos:
        console.print()
        console.print("[yellow]⚠ 以下儲存庫尚未 clone，已跳過更新：[/yellow]")
        for repo_path in missing_repos:
            console.print(f"  • {repo_path}")
        console.print(
            "[dim]   請執行 `ai-dev install --only repos,state,targets` 來補齊缺失的儲存庫[/dim]"
        )

    custom_repos = load_custom_repos().get("repos", {})
    template_repos_with_updates: list[str] = []

    for repo_name, repo_info in custom_repos.items():
        local_path = Path(
            repo_info.get("local_path", "").replace("~", str(Path.home()))
        )
        if not local_path.exists() or not (local_path / ".git").exists():
            console.print(f"[yellow]⚠ Custom repo 目錄不存在，跳過: {repo_name}[/yellow]")
            continue

        branch = repo_info.get("branch", "main")
        repo_type = repo_info.get("type", "tool")
        console.print(f"正在更新 {local_path} ({branch})...")
        run_command(["git", "fetch", "--all"], cwd=str(local_path), check=False)
        if check_for_updates(local_path, branch):
            updated_repos.append(repo_name)
            if repo_type == "template":
                template_repos_with_updates.append(repo_name)
        if has_local_changes(local_path):
            backup_dirty_files(local_path, backup_root)
        run_command(
            ["git", "reset", "--hard", f"origin/{branch}"],
            cwd=str(local_path),
            check=False,
        )

    if template_repos_with_updates:
        console.print()
        console.print("[bold cyan]模板 repo 有新更新：[/bold cyan]")
        for repo_name in template_repos_with_updates:
            console.print(f"  • {repo_name}")
        console.print("[dim]  在需要更新的專案目錄中執行：ai-dev init-from update[/dim]")

    console.print()
    if updated_repos:
        console.print("[bold cyan]以下儲存庫有新更新：[/bold cyan]")
        for name in updated_repos:
            console.print(f"  • {name}")
    else:
        console.print("[dim]所有儲存庫皆為最新[/dim]")


def run_repos_phase(*, plan: ExecutionPlan) -> None:
    """Run repo refresh work for a pipeline plan."""
    if plan.dry_run:
        console.print(f"[dim][dry-run] {plan.command_name}: repos[/dim]")
        return

    if plan.command_name == "install":
        _run_install_repos_phase()
        return
    if plan.command_name == "update":
        _run_update_repos_phase()
        return
    raise ValueError(f"Unsupported repos phase for {plan.command_name}")
