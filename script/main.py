import typer
from .commands.install import install
from .commands.update import update
from .commands.status import status
from .commands.list import list_resources
from .commands.toggle import toggle
from .commands import project

app = typer.Typer(help="AI Development Environment Setup CLI", no_args_is_help=True)

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
