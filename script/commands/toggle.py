"""
toggle 指令：啟用/停用特定工具的特定資源。
"""

from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from utils.shared import (
    load_toggle_config,
    save_toggle_config,
    copy_skills,
    list_installed_resources,
)

app = typer.Typer()
console = Console()

TARGET_DISPLAY_NAMES = {
    "claude": "Claude Code",
    "antigravity": "Antigravity",
    "opencode": "OpenCode",
}


@app.command()
def toggle(
    target: Optional[str] = typer.Option(
        None,
        "--target",
        "-t",
        help="目標工具：claude, antigravity, opencode",
    ),
    resource_type: Optional[str] = typer.Option(
        None,
        "--type",
        "-T",
        help="資源類型：skills, commands, agents, workflows",
    ),
    name: Optional[str] = typer.Option(
        None,
        "--name",
        "-n",
        help="資源名稱",
    ),
    enable: bool = typer.Option(
        False,
        "--enable",
        "-e",
        help="啟用資源",
    ),
    disable: bool = typer.Option(
        False,
        "--disable",
        "-d",
        help="停用資源",
    ),
    list_status: bool = typer.Option(
        False,
        "--list",
        "-l",
        help="列出目前的開關狀態",
    ),
    sync: bool = typer.Option(
        True,
        "--sync/--no-sync",
        help="操作後是否同步（預設是）",
    ),
):
    """啟用/停用特定工具的特定資源。"""
    config = load_toggle_config()

    # 列出狀態
    if list_status:
        show_toggle_status(config)
        return

    # 驗證參數
    if not target:
        console.print("[red]請指定目標工具（--target）[/red]")
        raise typer.Exit(code=1)

    valid_targets = ["claude", "antigravity", "opencode"]
    if target not in valid_targets:
        console.print(f"[red]無效的目標：{target}[/red]")
        raise typer.Exit(code=1)

    if not resource_type:
        console.print("[red]請指定資源類型（--type）[/red]")
        raise typer.Exit(code=1)

    valid_types_for_target = {
        "claude": ["skills", "commands"],
        "antigravity": ["skills", "workflows"],
        "opencode": ["agents"],
    }

    if resource_type not in valid_types_for_target.get(target, []):
        console.print(f"[red]{target} 不支援 {resource_type} 類型[/red]")
        console.print(f"有效選項：{', '.join(valid_types_for_target[target])}")
        raise typer.Exit(code=1)

    if not name:
        console.print("[red]請指定資源名稱（--name）[/red]")
        raise typer.Exit(code=1)

    if enable == disable:
        console.print("[red]請指定 --enable 或 --disable（二擇一）[/red]")
        raise typer.Exit(code=1)

    # 確保結構存在
    if target not in config:
        config[target] = {}
    if resource_type not in config[target]:
        config[target][resource_type] = {"enabled": True, "disabled": []}

    disabled_list = config[target][resource_type].get("disabled", [])

    if disable:
        if name not in disabled_list:
            disabled_list.append(name)
            console.print(f"[yellow]已停用 {target}/{resource_type}/{name}[/yellow]")
        else:
            console.print(f"[dim]{name} 已經是停用狀態[/dim]")
    else:  # enable
        if name in disabled_list:
            disabled_list.remove(name)
            console.print(f"[green]已啟用 {target}/{resource_type}/{name}[/green]")
        else:
            console.print(f"[dim]{name} 已經是啟用狀態[/dim]")

    config[target][resource_type]["disabled"] = disabled_list
    save_toggle_config(config)

    if sync:
        console.print("[blue]正在同步資源...[/blue]")
        copy_skills()
        console.print("[green]同步完成[/green]")


def show_toggle_status(config: dict):
    """顯示目前的開關狀態。"""
    table = Table(title="Toggle 狀態")
    table.add_column("目標", style="cyan")
    table.add_column("類型", style="green")
    table.add_column("整體啟用", style="yellow")
    table.add_column("停用項目", style="red")

    for target, types in config.items():
        target_name = TARGET_DISPLAY_NAMES.get(target, target)
        for resource_type, settings in types.items():
            enabled = settings.get("enabled", True)
            disabled = settings.get("disabled", [])

            enabled_text = "✓" if enabled else "✗"
            disabled_text = ", ".join(disabled) if disabled else "-"

            table.add_row(target_name, resource_type, enabled_text, disabled_text)

    console.print(table)
