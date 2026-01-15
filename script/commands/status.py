import typer
import shutil
import subprocess
from rich.console import Console
from rich.table import Table
from utils.paths import (
    get_custom_skills_dir,
    get_superpowers_dir,
    get_uds_dir,
    get_opencode_config_dir,
)

app = typer.Typer()
console = Console()


@app.command()
def status():
    """檢查環境狀態與工具版本。"""
    console.print("[bold blue]AI 開發環境狀態檢查[/bold blue]")

    table = Table(title="核心工具")
    table.add_column("工具", style="cyan")
    table.add_column("狀態", style="green")
    table.add_column("版本/路徑", style="yellow")

    # 檢查 Node.js
    node_path = shutil.which("node")
    if node_path:
        try:
            version = subprocess.check_output(["node", "--version"], text=True).strip()
            table.add_row("Node.js", "已安裝", version)
        except Exception:
            table.add_row("Node.js", "錯誤", "無法取得版本")
    else:
        table.add_row("Node.js", "未安裝", "-")

    # 檢查 Git
    git_path = shutil.which("git")
    if git_path:
        try:
            version = subprocess.check_output(["git", "--version"], text=True).strip()
            table.add_row("Git", "已安裝", version)
        except Exception:
            table.add_row("Git", "錯誤", "無法取得版本")
    else:
        table.add_row("Git", "未安裝", "-")

    console.print(table)
    console.print()

    # 檢查 NPM 套件
    npm_table = Table(title="全域 NPM 套件")
    npm_table.add_column("套件", style="cyan")
    npm_table.add_column("狀態", style="green")

    packages = [
        "@anthropic-ai/claude-code",
        "@fission-ai/openspec",
        "@google/gemini-cli",
        "universal-dev-standards",
        "opencode-ai",
    ]

    for pkg in packages:
        # 使用 npm list -g --depth=0 檢查
        # 這比較慢，但為了準確性
        try:
            # 簡化檢查：shutil.which 對於套件 binary 可能有用，例如 claude, openspec, gemini, uds, opencode
            binary_map = {
                "@anthropic-ai/claude-code": "claude",
                "@fission-ai/openspec": "openspec",
                "@google/gemini-cli": "gemini",
                "universal-dev-standards": "uds",
                "opencode-ai": "opencode",
            }
            bin_name = binary_map.get(pkg, pkg)
            if shutil.which(bin_name):
                npm_table.add_row(pkg, "已安裝")
            else:
                npm_table.add_row(pkg, "未找到指令")
        except Exception:
            npm_table.add_row(pkg, "檢查失敗")

    console.print(npm_table)
    console.print()

    # 檢查設定儲存庫
    repo_table = Table(title="設定儲存庫")
    repo_table.add_column("路徑", style="cyan")
    repo_table.add_column("狀態", style="green")

    repos = {
        "Custom Skills": get_custom_skills_dir(),
        "Superpowers": get_superpowers_dir(),
        "Universal Dev Standards": get_uds_dir(),
        "OpenCode Superpowers": get_opencode_config_dir() / "superpowers",
    }

    for name, path in repos.items():
        status_text = "未找到"
        if path.exists():
            if (path / ".git").exists():
                status_text = "Git 儲存庫 (正常)"
            else:
                status_text = "目錄存在 (非 Git)"
        repo_table.add_row(name, status_text)

    console.print(repo_table)
