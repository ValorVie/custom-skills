"""
ECC Hooks Plugin CLI management commands.

Provides install, uninstall, and status commands for the hooks plugin.
"""

import typer
from rich.console import Console

from ..utils.shared import (
    install_ecc_hooks_plugin,
    uninstall_ecc_hooks_plugin,
    show_ecc_hooks_status,
    get_ecc_hooks_status,
)

app = typer.Typer(help="ECC Hooks Plugin management commands")
console = Console()


@app.command()
def install():
    """Install or update ECC Hooks Plugin.

    Install the ECC Hooks Plugin to ~/.claude/plugins/ecc-hooks/
    """
    console.print("[bold blue]Installing ECC Hooks Plugin...[/bold blue]")
    success = install_ecc_hooks_plugin()
    if success:
        console.print()
        console.print("[dim]Plugin will be loaded automatically by Claude Code[/dim]")
        console.print("[dim]Restart Claude Code to reload if needed[/dim]")
    else:
        raise typer.Exit(code=1)


@app.command()
def uninstall():
    """Remove ECC Hooks Plugin.

    Delete ~/.claude/plugins/ecc-hooks/ directory
    """
    status = get_ecc_hooks_status()
    if not status["installed"]:
        console.print("[yellow]ECC Hooks Plugin is not installed[/yellow]")
        return

    # Confirm removal
    confirm = typer.confirm("Are you sure you want to remove ECC Hooks Plugin?")
    if not confirm:
        console.print("[dim]Cancelled[/dim]")
        return

    console.print("[bold blue]Removing ECC Hooks Plugin...[/bold blue]")
    success = uninstall_ecc_hooks_plugin()
    if not success:
        raise typer.Exit(code=1)


@app.command()
def status():
    """Display ECC Hooks Plugin installation status."""
    show_ecc_hooks_status()


if __name__ == "__main__":
    app()
