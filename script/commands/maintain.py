import typer
from rich.console import Console
from utils.system import run_command
from utils.paths import (
    get_custom_skills_dir,
    get_superpowers_dir,
    get_uds_dir,
    get_opencode_config_dir,
)
from commands.install import copy_skills

app = typer.Typer()
console = Console()


@app.command()
def maintain():
    """每日維護：更新工具並同步設定。"""
    console.print("[bold blue]開始維護...[/bold blue]")

    # 1. 更新全域 NPM 工具
    console.print("[green]正在更新全域 NPM 套件...[/green]")
    npm_packages = [
        "@anthropic-ai/claude-code",
        "@fission-ai/openspec@latest",
        "@google/gemini-cli",
        "universal-dev-standards",
        "opencode-ai@latest",
    ]
    # npm install -g 若已安裝則視為更新
    total = len(npm_packages)
    for i, package in enumerate(npm_packages, 1):
        console.print(f"[bold cyan][{i}/{total}] 正在更新 {package}...[/bold cyan]")
        run_command(["npm", "install", "-g", package])

    # 執行 uds update
    run_command(["uds", "update"], check=False)  # check=False 防止失敗中斷

    # 2. 更新儲存庫
    console.print("[green]正在更新儲存庫...[/green]")
    repos = [
        get_custom_skills_dir(),
        get_superpowers_dir(),
        get_uds_dir(),
        get_opencode_config_dir() / "superpowers",
    ]

    for repo in repos:
        if repo.exists() and (repo / ".git").exists():
            console.print(f"正在更新 {repo}...")
            run_command(["git", "pull"], cwd=str(repo))

    # 3. 重新同步 Skills
    console.print("[green]正在重新同步 Skills...[/green]")
    copy_skills()

    console.print("[bold green]維護完成！[/bold green]")
