import typer
from importlib.metadata import version as get_version

from .commands.install import install
from .commands.update import update
from .commands.status import status
from .commands.list import list_resources
from .commands.toggle import toggle
from .commands import project


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
app.command()(status)
app.command(name="list")(list_resources)
app.command()(toggle)
app.add_typer(project.app, name="project")


def tui():
    """啟動互動式 TUI 介面。"""
    from .tui.app import SkillManagerApp

    app_tui = SkillManagerApp()
    app_tui.run()


app.command()(tui)

if __name__ == "__main__":
    app()
