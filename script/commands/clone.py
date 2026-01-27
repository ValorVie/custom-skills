import typer
from pathlib import Path
from rich.console import Console
from ..utils.shared import (
    copy_skills,
    integrate_to_dev_project,
    get_custom_skills_dir,
    shorten_path,
)
from ..utils.paths import get_project_root
from ..utils.git_helpers import detect_metadata_changes, handle_metadata_changes

app = typer.Typer()
console = Console()


def _is_custom_skills_project(project_root: Path) -> bool:
    """檢查是否在 custom-skills 專案目錄中。

    透過檢查 pyproject.toml 中的 name = "ai-dev" 來判斷。
    """
    pyproject_path = project_root / "pyproject.toml"
    if not pyproject_path.exists():
        return False

    try:
        content = pyproject_path.read_text(encoding="utf-8")
        return 'name = "ai-dev"' in content
    except Exception:
        return False


def _is_dev_project_directory() -> tuple[bool, Path | None]:
    """檢查當前目錄是否為開發專案目錄（非 ~/.config/custom-skills）。

    Returns:
        tuple[bool, Path | None]: (是否為開發目錄, 專案根目錄)
    """
    project_root = get_project_root()
    custom_skills_dir = get_custom_skills_dir()

    # 檢查是否為 custom-skills 專案
    if not _is_custom_skills_project(project_root):
        return False, None

    # 確保不是 ~/.config/custom-skills 本身
    if project_root.resolve() == custom_skills_dir.resolve():
        return False, None

    return True, project_root


@app.command()
def clone(
    sync_project: bool = typer.Option(
        True,
        "--sync-project/--no-sync-project",
        help="是否同步到專案目錄（預設：是）。開發者可用此選項整合外部來源到開發目錄。",
    ),
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
    - 此指令只負責分發，不會整合外部來源到 ~/.config/custom-skills

    開發者模式：
    - 在開發目錄執行時，使用 --sync-project 可整合外部來源到開發目錄
    - 使用 --no-sync-project 可跳過整合
    """
    is_dev_dir, dev_project_root = _is_dev_project_directory()

    # 開發者模式：整合外部來源到開發目錄
    if is_dev_dir and sync_project and dev_project_root:
        console.print("[bold blue]開發者模式：整合外部來源到開發目錄[/bold blue]")
        integrate_to_dev_project(dev_project_root)
        console.print()

    # 提示開發者可使用 --sync-project
    if is_dev_dir and not sync_project:
        console.print(
            f"[dim]提示：使用 --sync-project 可整合外部來源到開發目錄 "
            f"({shorten_path(dev_project_root)})[/dim]"
        )
        console.print()

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

    # 執行分發（sync_project=False 因為專案同步已在上面處理）
    copy_skills(
        sync_project=False,
        force=force,
        skip_conflicts=skip_conflicts,
        backup=backup,
    )

    console.print("[bold green]分發完成！[/bold green]")

    # 檢測非內容異動（僅在開發目錄）
    if is_dev_dir and dev_project_root:
        changes = detect_metadata_changes(dev_project_root)
        if changes.has_changes:
            handle_metadata_changes(changes, dev_project_root, console)
