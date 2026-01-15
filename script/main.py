import typer
from commands.install import install
from commands.maintain import maintain
from commands.status import status

app = typer.Typer(help="AI Development Environment Setup Script", no_args_is_help=True)

app.command()(install)
app.command()(maintain)
app.command()(status)

if __name__ == "__main__":
    app()
