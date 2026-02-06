import subprocess
from pathlib import Path

import typer
from rich.console import Console
from ..utils.system import (
    run_command,
    check_command_exists,
    check_bun_installed,
    get_bun_version,
    get_bun_package_version,
)
from ..utils.paths import (
    get_config_dir,
    get_custom_skills_dir,
    get_claude_config_dir,
    get_claude_agents_dir,
    get_claude_workflows_dir,
    get_antigravity_config_dir,
    get_opencode_config_dir,
    get_codex_config_dir,
    get_gemini_cli_config_dir,
    get_superpowers_dir,
    get_uds_dir,
)
from ..utils.shared import (
    NPM_PACKAGES,
    BUN_PACKAGES,
    REPOS,
    copy_skills,
    get_all_skill_names,
    show_skills_npm_hint,
    show_claude_status,
    get_npm_package_version,
)

app = typer.Typer()
console = Console()


def _is_completion_installed(shell: str) -> bool:
    """檢查指定 shell 的自動補全是否已安裝。"""
    home = Path.home()
    checks = {
        "bash": home / ".bash_completions" / "ai-dev.sh",
        "zsh": home / ".zfunc" / "_ai-dev",
        "fish": home / ".config" / "fish" / "completions" / "ai-dev.fish",
    }
    if shell in checks:
        return checks[shell].exists()
    # PowerShell / pwsh：檢查 profile 中是否已包含 completion 註冊
    if shell in ("powershell", "pwsh"):
        import subprocess as _sp

        try:
            result = _sp.run(
                [shell, "-NoProfile", "-Command", "echo", "$profile"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0 and result.stdout.strip():
                profile_path = Path(result.stdout.strip())
                if profile_path.exists():
                    content = profile_path.read_text(encoding="utf-8", errors="ignore")
                    return "ai-dev" in content
        except Exception:
            pass
        return False
    return False


@app.command()
def install(
    skip_npm: bool = typer.Option(False, "--skip-npm", help="跳過 NPM 套件安裝"),
    skip_bun: bool = typer.Option(False, "--skip-bun", help="跳過 Bun 套件安裝"),
    skip_repos: bool = typer.Option(
        False, "--skip-repos", help="跳過 Git 儲存庫 Clone"
    ),
    skip_skills: bool = typer.Option(False, "--skip-skills", help="跳過複製 Skills"),
    sync_project: bool = typer.Option(
        True,
        "--sync-project/--no-sync-project",
        help="是否同步到專案目錄（預設：是）",
    ),
):
    """首次安裝 AI 開發環境。"""
    console.print("[bold blue]開始安裝...[/bold blue]")

    # 1. 檢查前置需求
    console.print("[bold blue]檢查前置需求...[/bold blue]")

    # 1.1 檢查 Node.js
    if not check_command_exists("node"):
        console.print("[bold red]✗ 找不到 Node.js[/bold red]")
        console.print()
        console.print("請先安裝 Node.js (建議版本 >= 20.19.0)：")
        console.print()
        console.print("[bold]macOS (使用 Homebrew)：[/bold]")
        console.print("  brew install nvm")
        console.print("  nvm install node")
        console.print()
        console.print("[bold]Windows：[/bold]")
        console.print("  下載並安裝：https://nodejs.org/ (選擇 LTS 版本)")
        console.print()
        raise typer.Exit(code=1)
    else:
        # 檢查 Node.js 版本
        try:
            result = subprocess.run(
                ["node", "--version"], capture_output=True, text=True, timeout=5
            )
            node_version = result.stdout.strip().replace("v", "")
            console.print(f"[green]✓[/green] Node.js {node_version}")

            # 簡單版本檢查（主要檢查是否 >= 20.x）
            major_version = int(node_version.split(".")[0])
            if major_version < 20:
                console.print("[yellow]⚠️  Node.js 版本建議 >= 20.19.0[/yellow]")
                console.print("   當前版本可能無法正常使用某些功能")
                console.print()
        except Exception:
            console.print("[green]✓[/green] Node.js 已安裝")

    # 1.2 檢查 Git
    if not check_command_exists("git"):
        console.print("[bold red]✗ 找不到 Git[/bold red]")
        console.print()
        console.print("請先安裝 Git：")
        console.print()
        console.print("[bold]macOS (使用 Homebrew)：[/bold]")
        console.print("  brew install git")
        console.print()
        console.print("[bold]Windows：[/bold]")
        console.print("  下載並安裝：https://git-scm.com/download/win")
        console.print()
        raise typer.Exit(code=1)
    else:
        console.print("[green]✓[/green] Git 已安裝")

    # 1.3 檢查 GitHub CLI (gh) - 選用但推薦
    if not check_command_exists("gh"):
        console.print("[yellow]⚠️  未檢測到 GitHub CLI (gh)[/yellow]")
        console.print("   建議安裝以便使用 PR 管理功能")
        console.print()
        console.print("[dim]安裝方式：[/dim]")
        console.print("[dim]  macOS: brew install gh && gh auth login[/dim]")
        console.print(
            "[dim]  Windows: winget install GitHub.cli && gh auth login[/dim]"
        )
        console.print()
    else:
        console.print("[green]✓[/green] GitHub CLI 已安裝")

    # 1.4 檢查 Bun - 選用（用於 Codex）
    if not check_bun_installed():
        console.print("[yellow]⚠️  未檢測到 Bun[/yellow]")
        console.print("   建議安裝以便自動安裝 Codex CLI")
        console.print()
        console.print("[dim]安裝方式：[/dim]")
        console.print("[dim]  curl -fsSL https://bun.sh/install | bash[/dim]")
        console.print()
    else:
        bun_version = get_bun_version()
        console.print(f"[green]✓[/green] Bun {bun_version}")

    console.print()

    # 1.5 檢查 Claude Code 安裝狀態（顯示詳細資訊）
    show_claude_status()

    # 2. 安裝全域 NPM 套件
    if skip_npm:
        console.print("[yellow]跳過 NPM 套件安裝[/yellow]")
    else:
        console.print("[green]正在安裝全域 NPM 套件...[/green]")
        total = len(NPM_PACKAGES)
        for i, package in enumerate(NPM_PACKAGES, 1):
            # 檢查套件是否已安裝
            existing_version = get_npm_package_version(package)
            if existing_version:
                console.print(
                    f"[bold cyan][{i}/{total}][/bold cyan] {package} "
                    f"[dim](已安裝 v{existing_version}，檢查更新...)[/dim]"
                )
            else:
                console.print(
                    f"[bold cyan][{i}/{total}] 正在安裝 {package}...[/bold cyan]"
                )
            run_command(["npm", "install", "-g", package])

    # 2.5 安裝 Bun 套件
    if skip_bun:
        console.print("[yellow]跳過 Bun 套件安裝[/yellow]")
    else:
        console.print("[green]正在檢查 Bun...[/green]")
        if not check_bun_installed():
            console.print("[yellow]⚠️  未檢測到 Bun。[/yellow]")
            console.print()
            console.print("Codex CLI 需要 Bun 才能安裝。請選擇以下方式之一安裝：")
            console.print()
            console.print("[bold]macOS / Linux：[/bold]")
            console.print("  curl -fsSL https://bun.sh/install | bash")
            console.print()
            console.print("[bold]Windows (PowerShell)：[/bold]")
            console.print('  powershell -c "irm bun.sh/install.ps1 | iex"')
            console.print()
            console.print("安裝完成後，請重新執行 `ai-dev install`")
            console.print()
            console.print("[yellow]跳過 Codex 安裝[/yellow]")
        else:
            bun_version = get_bun_version()
            console.print(f"[dim]✓ Bun 已安裝 ({bun_version})[/dim]")
            console.print("[green]正在安裝 Bun 套件...[/green]")
            total = len(BUN_PACKAGES)
            for i, package in enumerate(BUN_PACKAGES, 1):
                existing_version = get_bun_package_version(package)
                if existing_version:
                    console.print(
                        f"[bold cyan][{i}/{total}][/bold cyan] {package} "
                        f"[dim](已安裝 v{existing_version}，檢查更新...)[/dim]"
                    )
                else:
                    console.print(
                        f"[bold cyan][{i}/{total}] 正在安裝 {package}...[/bold cyan]"
                    )
                run_command(["bun", "install", "-g", package])

    # 3. 建立目錄
    console.print("[green]正在建立目錄...[/green]")
    dirs = [
        # 基礎目錄
        get_config_dir(),
        get_custom_skills_dir(),
        get_superpowers_dir(),
        get_uds_dir(),
        # Claude Code
        get_claude_config_dir() / "skills",
        get_claude_config_dir() / "commands",
        get_claude_agents_dir(),
        get_claude_workflows_dir(),
        # Antigravity
        get_antigravity_config_dir() / "global_skills",
        get_antigravity_config_dir() / "global_workflows",
        # OpenCode（新增 skills 和 commands）
        get_opencode_config_dir() / "skills",
        get_opencode_config_dir() / "commands",
        get_opencode_config_dir() / "agents",
        # Codex
        get_codex_config_dir() / "skills",
        # Gemini CLI
        get_gemini_cli_config_dir() / "skills",
        get_gemini_cli_config_dir() / "commands",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

    # 4. Clone 儲存庫
    if skip_repos:
        console.print("[yellow]跳過 Git 儲存庫 Clone[/yellow]")
    else:
        console.print("[green]正在 Clone 儲存庫...[/green]")
        for name, (url, get_path) in REPOS.items():
            path = get_path()
            if not (path / ".git").exists():
                console.print(f"正在 Clone {url} 到 {path}...")
                run_command(["git", "clone", url, str(path)])
            else:
                console.print(f"{path} 已存在，跳過 Clone。")

    # 4.5 Clone custom repos
    if not skip_repos:
        from ..utils.custom_repos import load_custom_repos

        custom_repos = load_custom_repos().get("repos", {})
        if custom_repos:
            console.print("[green]正在 Clone 自訂儲存庫...[/green]")
            for repo_name, repo_info in custom_repos.items():
                local_path = Path(
                    repo_info.get("local_path", "").replace("~", str(Path.home()))
                )
                if (local_path / ".git").exists():
                    console.print(f"{local_path} 已存在，跳過 Clone。")
                else:
                    url = repo_info.get("url", "")
                    console.print(f"正在 Clone {url} 到 {local_path}...")
                    result = run_command(
                        ["git", "clone", url, str(local_path)], check=False
                    )
                    if result and result.returncode != 0:
                        console.print(
                            f"[yellow]⚠ Clone {repo_name} 失敗，跳過[/yellow]"
                        )

    # 5. 複製 Skills 與設定（Stage 2 + Stage 3）
    if skip_skills:
        console.print("[yellow]跳過複製 Skills[/yellow]")
    else:
        console.print("[green]正在同步 Skills 與設定...[/green]")
        copy_skills(sync_project=sync_project)

    # 6. 顯示已安裝的 Skills 警告
    console.print()
    console.print(
        "[yellow]⚠️ 已安裝的 Skills（建立自訂 skill 時請避免使用重複名稱）：[/yellow]"
    )
    skill_names = get_all_skill_names()
    for name in skill_names:
        console.print(f"   - {name}")
    console.print()
    console.print(
        "[dim]提示：使用獨特前綴（如 user-、local-、公司名-）來避免名稱衝突[/dim]"
    )

    # 7. 顯示 npx skills 提示
    show_skills_npm_hint()

    # 8. 安裝 Shell Completion
    console.print()
    console.print("[green]正在設定 Shell 自動補全...[/green]")
    try:
        from typer._completion_shared import (
            install as _install_completion,
            _get_shell_name,
        )

        shell_name = _get_shell_name()
        if shell_name is None:
            console.print(
                "[yellow]無法偵測 Shell 類型，請手動執行：ai-dev --install-completion[/yellow]"
            )
        elif _is_completion_installed(shell_name):
            console.print(f"[dim]{shell_name} 自動補全已安裝，跳過[/dim]")
        else:
            shell, path = _install_completion(prog_name="ai-dev")
            console.print(
                f"[green]{shell} 自動補全已安裝：{path}（重啟 terminal 後生效）[/green]"
            )
    except Exception:
        console.print(
            "[yellow]Shell 自動補全安裝失敗，請手動執行：ai-dev --install-completion[/yellow]"
        )

    console.print()
    console.print("[bold green]安裝完成！[/bold green]")
