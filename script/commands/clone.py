import typer
from rich.console import Console
from ..cli.command_manifest import build_command_manifest, get_command_spec
from ..cli.phase_selection import build_execution_plan
from ..services.pipeline.clone_pipeline import execute_clone_plan
from ..utils.shared import (
    copy_skills,
    get_custom_skills_dir,
    shorten_path,
)

app = typer.Typer()
console = Console()


def _legacy_clone(
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="強制覆蓋所有衝突檔案（不提示）。",
    ),
    skip_conflicts: bool = typer.Option(
        False,
        "--skip-conflicts",
        "-s",
        help="跳過有衝突的檔案，僅分發無衝突的檔案。",
    ),
    backup: bool = typer.Option(
        False,
        "--backup",
        "-b",
        help="備份衝突檔案後再覆蓋。",
    ),
):
    """分發 Skills 到各工具目錄。

    將 ~/.config/custom-skills 的內容分發到：
    - Claude Code (~/.claude/)
    - OpenCode (~/.config/opencode/)
    - Gemini CLI (~/.gemini/)
    - Codex (~/.codex/)
    - Antigravity (~/.gemini/antigravity/)

    流程說明：
    - ~/.config/custom-skills 的內容由 git repo 控制
    - 此指令只負責分發，不會整合外部來源回 custom-skills 專案
    """
    # 分發 Skills（從 ~/.config/custom-skills 分發到各工具目錄）
    console.print("[bold blue]分發 Skills 到各工具目錄...[/bold blue]")

    # 檢查來源目錄是否存在
    custom_skills_dir = get_custom_skills_dir()
    if not custom_skills_dir.exists():
        console.print(
            f"[bold red]錯誤：來源目錄不存在 ({shorten_path(custom_skills_dir)})[/bold red]"
        )
        console.print("[dim]請先執行 ai-dev install 或 ai-dev update[/dim]")
        raise typer.Exit(code=1)

    # 執行分發（不同步回 custom-skills 專案目錄）
    copy_skills(
        sync_project=False,
        force=force,
        skip_conflicts=skip_conflicts,
        backup=backup,
    )

    console.print("[bold green]分發完成！[/bold green]")


@app.command(name="clone")
def clone(
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="強制覆蓋所有衝突檔案（不提示）。",
    ),
    skip_conflicts: bool = typer.Option(
        False,
        "--skip-conflicts",
        "-s",
        help="跳過有衝突的檔案，僅分發無衝突的檔案。",
    ),
    backup: bool = typer.Option(
        False,
        "--backup",
        "-b",
        help="備份衝突檔案後再覆蓋。",
    ),
    only: str | None = typer.Option(None, "--only", help="僅執行指定 phase"),
    skip: str | None = typer.Option(None, "--skip", help="跳過指定 phase"),
    target: str | None = typer.Option(None, "--target", help="限制分發 target"),
    dry_run: bool = typer.Option(False, "--dry-run", help="只顯示執行計畫，不實際寫入"),
):
    """分發 Skills 到各工具目錄。"""
    manifest = build_command_manifest()
    spec = get_command_spec(manifest, ("clone",))
    plan = build_execution_plan(
        spec,
        only=only,
        skip=skip,
        target=target,
        dry_run=dry_run,
    )
    execute_clone_plan(
        plan,
        force=force,
        skip_conflicts=skip_conflicts,
        backup=backup,
    )
