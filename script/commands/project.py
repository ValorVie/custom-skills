"""
project 指令群組：專案級別的初始化與更新操作。

採用薄包裝模式，底層呼叫 openspec 和 uds CLI。
"""

import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional, List

import typer
from rich.console import Console

app = typer.Typer(help="專案級別的初始化與更新操作")
console = Console()


# 支援的工具
TOOLS = {
    "openspec": {
        "check_dir": "openspec",
        "install_hint": "npm install -g @fission-ai/openspec@latest",
    },
    "uds": {
        "check_dir": ".standards",
        "install_hint": "npm install -g universal-dev-standards",
    },
}


def check_tool_installed(tool: str) -> bool:
    """檢查工具是否已安裝。"""
    return shutil.which(tool) is not None


def run_tool_command(tool: str, command: str) -> bool:
    """執行工具命令，即時顯示輸出。返回是否成功。"""
    console.print(f"[bold cyan]執行 {tool} {command}...[/bold cyan]")
    try:
        result = subprocess.run(
            [tool, command],
            check=False,
        )
        return result.returncode == 0
    except FileNotFoundError:
        console.print(f"[bold red]找不到 {tool} 命令[/bold red]")
        return False


def check_project_initialized(tool: str) -> bool:
    """檢查專案是否已初始化特定工具。"""
    check_dir = TOOLS[tool]["check_dir"]
    return Path(check_dir).exists()


def get_missing_tools(tools: List[str]) -> List[str]:
    """取得未安裝的工具列表。"""
    return [t for t in tools if not check_tool_installed(t)]


@app.command()
def init(
    only: Optional[str] = typer.Option(
        None,
        "--only",
        "-o",
        help="只初始化特定工具：openspec, uds",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="強制重新初始化（即使已存在）",
    ),
):
    """初始化專案（整合 openspec init + uds init）。"""
    # 決定要初始化的工具
    if only:
        if only not in TOOLS:
            console.print(f"[red]無效的工具：{only}[/red]")
            console.print(f"有效選項：{', '.join(TOOLS.keys())}")
            raise typer.Exit(code=1)
        tools_to_init = [only]
    else:
        tools_to_init = list(TOOLS.keys())

    # 檢查工具是否已安裝
    missing = get_missing_tools(tools_to_init)
    if missing:
        console.print("[bold red]以下工具尚未安裝：[/bold red]")
        for tool in missing:
            hint = TOOLS[tool]["install_hint"]
            console.print(f"  - {tool}: [dim]{hint}[/dim]")
        console.print()
        console.print("[yellow]請先安裝所需工具後再執行此命令。[/yellow]")
        raise typer.Exit(code=1)

    # 檢查是否已初始化
    if not force:
        already_init = [t for t in tools_to_init if check_project_initialized(t)]
        if already_init:
            console.print("[yellow]以下工具已初始化：[/yellow]")
            for tool in already_init:
                check_dir = TOOLS[tool]["check_dir"]
                console.print(f"  - {tool}: {check_dir}/ 已存在")
            console.print()
            console.print("[dim]使用 --force 強制重新初始化[/dim]")

            # 移除已初始化的工具
            tools_to_init = [t for t in tools_to_init if t not in already_init]
            if not tools_to_init:
                console.print("[green]專案已完全初始化。[/green]")
                return

    console.print("[bold blue]開始初始化專案...[/bold blue]")
    console.print()

    # 執行初始化（uds 先，openspec 後）
    init_order = ["uds", "openspec"]
    success = True

    for tool in init_order:
        if tool not in tools_to_init:
            continue

        if not run_tool_command(tool, "init"):
            console.print(f"[bold red]{tool} init 失敗[/bold red]")
            success = False
            break

        console.print(f"[green]✓ {tool} init 完成[/green]")
        console.print()

    if success:
        console.print("[bold green]專案初始化完成！[/bold green]")
    else:
        raise typer.Exit(code=1)


@app.command()
def update(
    only: Optional[str] = typer.Option(
        None,
        "--only",
        "-o",
        help="只更新特定工具：openspec, uds",
    ),
):
    """更新專案配置（整合 openspec update + uds update）。"""
    # 決定要更新的工具
    if only:
        if only not in TOOLS:
            console.print(f"[red]無效的工具：{only}[/red]")
            console.print(f"有效選項：{', '.join(TOOLS.keys())}")
            raise typer.Exit(code=1)
        tools_to_update = [only]
    else:
        tools_to_update = list(TOOLS.keys())

    # 檢查工具是否已安裝
    missing = get_missing_tools(tools_to_update)
    if missing:
        console.print("[bold red]以下工具尚未安裝：[/bold red]")
        for tool in missing:
            hint = TOOLS[tool]["install_hint"]
            console.print(f"  - {tool}: [dim]{hint}[/dim]")
        console.print()
        console.print("[yellow]請先安裝所需工具後再執行此命令。[/yellow]")
        raise typer.Exit(code=1)

    # 檢查是否已初始化
    not_init = [t for t in tools_to_update if not check_project_initialized(t)]
    if not_init:
        if len(not_init) == len(tools_to_update):
            # 全部都沒初始化
            console.print("[bold red]專案尚未初始化。[/bold red]")
            console.print("[yellow]請先執行 `ai-dev project init`[/yellow]")
            raise typer.Exit(code=1)
        else:
            # 部分初始化
            console.print("[yellow]以下工具尚未初始化：[/yellow]")
            for tool in not_init:
                check_dir = TOOLS[tool]["check_dir"]
                console.print(f"  - {tool}: {check_dir}/ 不存在")
            console.print()
            console.print(f"[dim]建議執行 `ai-dev project init --only {not_init[0]}`[/dim]")
            console.print()

            # 只更新已初始化的工具
            tools_to_update = [t for t in tools_to_update if t not in not_init]

    console.print("[bold blue]開始更新專案配置...[/bold blue]")
    console.print()

    # 執行更新（uds 先，openspec 後）
    update_order = ["uds", "openspec"]
    success = True

    for tool in update_order:
        if tool not in tools_to_update:
            continue

        if not run_tool_command(tool, "update"):
            console.print(f"[bold red]{tool} update 失敗[/bold red]")
            success = False
            break

        console.print(f"[green]✓ {tool} update 完成[/green]")
        console.print()

    if success:
        console.print("[bold green]專案配置更新完成！[/bold green]")
    else:
        raise typer.Exit(code=1)
