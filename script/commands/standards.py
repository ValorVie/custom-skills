"""
ai-dev standards：已隨 UDS 退役。

這個指令過去用來切換 UDS 的 standards profile。保留指令名稱，讓舊用法得到
說明，而不是「No such command」錯誤。
"""

from typing import List, Optional

import typer
from rich.console import Console

console = Console()


def retired(args: Optional[List[str]] = typer.Argument(None, hidden=True)) -> None:
    """（已退役）UDS standards profile 管理。"""
    console.print("[yellow]`ai-dev standards` 已隨 UDS 退役，沒有執行任何動作。[/yellow]")
    console.print(
        "[dim]專案內既有的 .standards/ 保留不動；若曾用 profile 停用資源，"
        "可用 `ai-dev toggle` 重新啟用。[/dim]"
    )
