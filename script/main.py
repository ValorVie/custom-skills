import typer
from importlib.metadata import version as get_version

from .commands.install import install
from .commands.update import update
from .commands.clone import clone
from .commands.status import status
from .commands.list import list_resources
from .commands.toggle import toggle
from .commands.add_repo import add_repo
from .commands.add_custom_repo import add_custom_repo
from .commands.update_custom_repo import update_custom_repo
from .commands.init_from import init_from
from .commands.test import test
from .commands.coverage import coverage
from .commands.derive_tests import derive_tests
from .commands import project
from .commands import standards
from .commands import hooks
from .commands import maintain
from .commands import sync
from .commands import mem


def get_app_version() -> str:
    """取得應用程式版本。"""
    try:
        return get_version("ai-dev")
    except Exception:
        return "unknown"


def version_callback(value: bool) -> None:
    """顯示版本資訊並退出。"""
    if value:
        ver = get_app_version()
        typer.echo(f"ai-dev {ver}")
        raise typer.Exit()


app = typer.Typer(help="AI Development Environment Setup CLI", no_args_is_help=True)


@app.callback()
def main_callback(
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        help="顯示版本資訊",
        callback=version_callback,
        is_eager=True,
    ),
) -> None:
    """AI Development Environment Setup CLI"""
    pass


app.command()(install)
app.command()(update)
app.command()(clone)


@app.command("install-npx-skills")
def install_npx_skills_cmd(
    dry_run: bool = typer.Option(False, "--dry-run", help="顯示將執行的命令但不實際執行"),
) -> None:
    """安裝 upstream/npx-skills.yaml 列出的 skill（等同 install --only npx-skills）。"""
    from script.services.npx_skills import run_npx_skills_phase
    from script.utils.paths import get_npx_skills_project_yaml, get_npx_skills_user_yaml

    run_npx_skills_phase(
        mode="add",
        project_yaml=get_npx_skills_project_yaml(),
        user_yaml=get_npx_skills_user_yaml(),
        dry_run=dry_run,
    )

app.command()(status)
app.command(name="list")(list_resources)
app.command()(toggle)
app.command(name="add-repo")(add_repo)
app.command(name="add-custom-repo")(add_custom_repo)
app.command(name="update-custom-repo")(update_custom_repo)
app.command(name="init-from")(init_from)
app.command()(test)
app.command()(coverage)
app.command(name="derive-tests")(derive_tests)
app.add_typer(project.app, name="project")
app.add_typer(standards.app, name="standards")
app.add_typer(hooks.app, name="hooks")
app.add_typer(maintain.app, name="maintain")
app.add_typer(sync.app, name="sync")
app.add_typer(mem.app, name="mem")


def tui():
    """啟動互動式 TUI 介面。"""
    from .tui.app import SkillManagerApp

    app_tui = SkillManagerApp()
    app_tui.run()


app.command()(tui)

if __name__ == "__main__":
    app()
