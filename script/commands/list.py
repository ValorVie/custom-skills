"""
list 指令：列出已安裝的 skills、commands、agents。
"""

from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from utils.shared import (
    list_installed_resources,
    load_toggle_config,
    is_resource_enabled,
    TargetType,
    ResourceType,
)

app = typer.Typer()
console = Console()

TARGET_DISPLAY_NAMES = {
    "claude": "Claude Code",
    "antigravity": "Antigravity",
    "opencode": "OpenCode",
}

TYPE_DISPLAY_NAMES = {
    "skills": "Skills",
    "commands": "Commands",
    "workflows": "Workflows",
    "agents": "Agents",
}


@app.command()
def list_resources(
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
    show_disabled: bool = typer.Option(
        False,
        "--show-disabled",
        "-d",
        help="顯示已停用的資源",
    ),
):
    """列出已安裝的 Skills、Commands、Agents。"""
    # 驗證參數
    valid_targets = ["claude", "antigravity", "opencode"]
    valid_types = ["skills", "commands", "agents", "workflows"]

    if target and target not in valid_targets:
        console.print(f"[red]無效的目標：{target}[/red]")
        console.print(f"有效選項：{', '.join(valid_targets)}")
        raise typer.Exit(code=1)

    if resource_type and resource_type not in valid_types:
        console.print(f"[red]無效的類型：{resource_type}[/red]")
        console.print(f"有效選項：{', '.join(valid_types)}")
        raise typer.Exit(code=1)

    # 取得資源列表
    resources = list_installed_resources(target, resource_type)
    toggle_config = load_toggle_config()

    # 顯示結果
    for t, types in resources.items():
        for rt, items in types.items():
            if not items:
                continue

            target_name = TARGET_DISPLAY_NAMES.get(t, t)
            type_name = TYPE_DISPLAY_NAMES.get(rt, rt)

            table = Table(title=f"{target_name} - {type_name}")
            table.add_column("名稱", style="cyan")
            table.add_column("來源", style="green")
            table.add_column("狀態", style="yellow")

            for item in items:
                name = item["name"]
                source = item["source"]
                enabled = is_resource_enabled(toggle_config, t, rt, name)

                if not enabled and not show_disabled:
                    continue

                status = "✓ 啟用" if enabled else "✗ 停用"
                status_style = "green" if enabled else "red"

                table.add_row(name, source, f"[{status_style}]{status}[/{status_style}]")

            console.print(table)
            console.print()
