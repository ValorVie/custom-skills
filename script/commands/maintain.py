from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from ..utils.paths import get_project_root
from ..utils.shared import integrate_to_dev_project
from ..utils.project_template_manifest import (
    get_project_template_manifest_path,
    load_project_template_manifest,
)
from ..utils.project_template_sync import sync_project_template

app = typer.Typer(help="維護 custom-skills 專案本身")
console = Console()


def _resolve_repo_root() -> Path:
    repo_root = get_project_root().resolve()
    pyproject_path = repo_root / "pyproject.toml"
    if not pyproject_path.exists():
        raise typer.Exit(code=1)

    content = pyproject_path.read_text(encoding="utf-8")
    if 'name = "ai-dev"' not in content:
        raise typer.Exit(code=1)

    return repo_root


@app.command()
def template(
    check: bool = typer.Option(False, "--check", help="僅檢查差異，不實際寫入"),
):
    """同步 project-template 內容。"""
    repo_root = _resolve_repo_root()
    template_dir = repo_root / "project-template"
    manifest_path = get_project_template_manifest_path(repo_root)
    manifest = load_project_template_manifest(manifest_path)

    result = sync_project_template(
        repo_root=repo_root,
        template_dir=template_dir,
        manifest=manifest,
        check=check,
    )

    action = "檢查" if check else "同步"
    console.print(f"[bold blue]project-template {action}完成[/bold blue]")
    console.print(
        f"[dim]copied={result.copied} updated={result.updated} "
        f"skipped={result.skipped} missing={len(result.missing)}[/dim]"
    )


@app.command()
def clone():
    """整合外部來源到 custom-skills 開發目錄。"""
    repo_root = _resolve_repo_root()
    console.print("[bold blue]整合外部來源到開發目錄[/bold blue]")
    integrate_to_dev_project(repo_root)
