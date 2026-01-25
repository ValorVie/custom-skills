import typer
from rich.console import Console
from ..utils.shared import copy_skills

app = typer.Typer()
console = Console()


@app.command()
def clone(
    sync_project: bool = typer.Option(
        True,
        "--sync-project/--no-sync-project",
        help="是否同步到專案目錄（預設：是）",
    ),
):
    """分發 Skills 到各工具目錄。

    將 ~/.config/custom-skills 的內容分發到：
    - Claude Code (~/.claude/)
    - OpenCode (~/.config/opencode/)
    - Gemini CLI (~/.gemini/)
    - Codex (~/.codex/)
    - Antigravity (~/.gemini/antigravity/)

    流程：
    1. Stage 2: 整合外部來源（UDS, Obsidian, Anthropic）到 custom-skills
    2. Stage 3: 分發 custom-skills 到各工具目錄

    使用 --no-sync-project 可跳過同步到當前專案目錄。
    """
    console.print("[bold blue]開始分發 Skills...[/bold blue]")
    copy_skills(sync_project=sync_project)
    console.print("[bold green]分發完成！[/bold green]")
