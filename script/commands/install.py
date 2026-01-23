import typer
from rich.console import Console
from ..utils.system import run_command, check_command_exists
from ..utils.paths import (
    get_config_dir,
    get_custom_skills_dir,
    get_claude_config_dir,
    get_antigravity_config_dir,
    get_opencode_config_dir,
    get_codex_config_dir,
    get_gemini_cli_config_dir,
    get_superpowers_dir,
    get_uds_dir,
)
from ..utils.shared import (
    NPM_PACKAGES,
    REPOS,
    copy_skills,
    get_all_skill_names,
    show_skills_npm_hint,
    show_claude_status,
    get_npm_package_version,
)

app = typer.Typer()
console = Console()


@app.command()
def install(
    skip_npm: bool = typer.Option(False, "--skip-npm", help="跳過 NPM 套件安裝"),
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
    if not check_command_exists("node"):
        console.print("[bold red]找不到 Node.js，請先安裝 Node.js。[/bold red]")
        raise typer.Exit(code=1)

    if not check_command_exists("git"):
        console.print("[bold red]找不到 Git，請先安裝 Git。[/bold red]")
        raise typer.Exit(code=1)

    # 1.1 檢查 Claude Code 安裝狀態（顯示詳細資訊）
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
                console.print(f"[bold cyan][{i}/{total}] 正在安裝 {package}...[/bold cyan]")
            run_command(["npm", "install", "-g", package])

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
        # Antigravity
        get_antigravity_config_dir() / "global_skills",
        get_antigravity_config_dir() / "global_workflows",
        # OpenCode（新增 skills 和 commands）
        get_opencode_config_dir() / "skills",
        get_opencode_config_dir() / "commands",
        get_opencode_config_dir() / "agent",
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

    # 5. 複製 Skills 與設定（Stage 2 + Stage 3）
    if skip_skills:
        console.print("[yellow]跳過複製 Skills[/yellow]")
    else:
        console.print("[green]正在同步 Skills 與設定...[/green]")
        copy_skills(sync_project=sync_project)

    # 6. 顯示已安裝的 Skills 警告
    console.print()
    console.print("[yellow]⚠️ 已安裝的 Skills（建立自訂 skill 時請避免使用重複名稱）：[/yellow]")
    skill_names = get_all_skill_names()
    for name in skill_names:
        console.print(f"   - {name}")
    console.print()
    console.print("[dim]提示：使用獨特前綴（如 user-、local-、公司名-）來避免名稱衝突[/dim]")

    # 7. 顯示 npx skills 提示
    show_skills_npm_hint()

    console.print()
    console.print("[bold green]安裝完成！[/bold green]")
