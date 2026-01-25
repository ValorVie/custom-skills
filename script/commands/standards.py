"""
Standards Profile Manager
切換與管理標準體系配置

用法:
    ai-dev standards status          # 顯示目前狀態
    ai-dev standards list            # 列出可用 profiles
    ai-dev standards switch <name>   # 切換 profile
    ai-dev standards show <name>     # 顯示 profile 內容
"""

from pathlib import Path
from datetime import datetime

import typer
import yaml
from rich.console import Console
from rich.table import Table

app = typer.Typer(help="管理標準體系配置")
console = Console()


def get_project_root() -> Path:
    """取得專案根目錄（從當前工作目錄尋找 .standards）"""
    current = Path.cwd()
    while current != current.parent:
        if (current / '.standards').is_dir():
            return current
        current = current.parent
    # 如果找不到，使用當前工作目錄
    return Path.cwd()


def get_standards_dir() -> Path:
    """取得 .standards 目錄路徑"""
    return get_project_root() / '.standards'


def get_profiles_dir() -> Path:
    """取得 profiles 目錄路徑"""
    return get_standards_dir() / 'profiles'


def get_active_profile_path() -> Path:
    """取得 active-profile.yaml 路徑"""
    return get_standards_dir() / 'active-profile.yaml'


def is_standards_initialized() -> bool:
    """檢查專案是否已初始化標準體系

    Returns:
        True if .standards/ 目錄與 active-profile.yaml 都存在，否則 False
    """
    standards_dir = get_standards_dir()
    active_file = get_active_profile_path()
    return standards_dir.exists() and active_file.exists()


def load_yaml(path: Path) -> dict:
    """載入 YAML 檔案"""
    if not path.exists():
        return {}
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) or {}


def save_yaml(path: Path, data: dict) -> None:
    """儲存 YAML 檔案"""
    with open(path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


def list_profiles() -> list:
    """列出所有可用的 profiles

    TODO: Phase 2 應改為讀取 profiles/*.yaml 檔案。
    當前實作為臨時方案，從 active-profile.yaml 的 available 欄位讀取清單。
    """
    # 臨時方案：從 active-profile.yaml 讀取 available 清單
    active_config = load_yaml(get_active_profile_path())
    return active_config.get('available', [])


def get_active_profile() -> str:
    """取得目前啟用的 profile 名稱"""
    active_config = load_yaml(get_active_profile_path())
    return active_config.get('active', 'uds')


@app.command()
def status():
    """顯示目前狀態"""
    if not is_standards_initialized():
        console.print("[yellow]⚠️  專案尚未初始化標準體系[/yellow]")
        console.print("[dim]請執行 'ai-dev project init' 初始化專案[/dim]")
        return

    active = get_active_profile()
    profiles = list_profiles()

    console.print("[bold]Standards Profile 狀態[/bold]")
    console.print(f"目前啟用: [cyan]{active}[/cyan]")
    if profiles:
        console.print(f"可用 profiles: {', '.join(profiles)}")
    else:
        console.print("[dim]無可用 profiles[/dim]")
    console.print()
    console.print("[yellow]注意：Profile 切換目前為臨時功能，不會載入不同標準[/yellow]")


@app.command(name="list")
def list_cmd():
    """列出所有可用的 profiles"""
    if not is_standards_initialized():
        console.print("[yellow]⚠️  專案尚未初始化標準體系[/yellow]")
        console.print("[dim]請執行 'ai-dev project init' 初始化專案[/dim]")
        return

    profiles = list_profiles()
    if not profiles:
        console.print("[yellow]無可用的 profiles[/yellow]")
        return

    active = get_active_profile()

    table = Table(title="可用的 Standards Profiles (臨時清單模式)")
    table.add_column("Profile", style="cyan")
    table.add_column("狀態", style="green")

    for name in sorted(profiles):
        status_mark = "✓ 啟用中" if name == active else ""
        table.add_row(name, status_mark)

    console.print(table)
    console.print()
    console.print("[yellow]注意：Profile 切換目前為臨時功能，不會載入不同標準[/yellow]")


@app.command()
def switch(
    profile_name: str = typer.Argument(..., help="要切換的 profile 名稱")
):
    """切換到指定的 profile"""
    profiles = list_profiles()

    if profile_name not in profiles:
        console.print(f"[red]錯誤: Profile '{profile_name}' 不存在[/red]")
        console.print(f"可用的 profiles: {', '.join(profiles)}")
        raise typer.Exit(1)

    active_path = get_active_profile_path()
    active_config = load_yaml(active_path)

    old_profile = active_config.get('active', 'uds')

    if old_profile == profile_name:
        console.print(f"[yellow]已經在使用 '{profile_name}' profile[/yellow]")
        return

    # 更新 active profile
    active_config['active'] = profile_name
    active_config['last_updated'] = datetime.now().strftime('%Y-%m-%d')

    save_yaml(active_path, active_config)

    console.print(f"[green]已從 '{old_profile}' 切換到 '{profile_name}'[/green]")
    console.print()
    console.print("[yellow]注意：當前為臨時實作，切換不會載入不同標準[/yellow]")


@app.command()
def show(
    profile_name: str = typer.Argument(..., help="要顯示的 profile 名稱")
):
    """顯示指定 profile 的詳細內容"""
    profiles = list_profiles()

    if profile_name not in profiles:
        console.print(f"[red]錯誤: Profile '{profile_name}' 不存在[/red]")
        console.print(f"可用的 profiles: {', '.join(profiles)}")
        raise typer.Exit(1)

    active = get_active_profile()
    is_active = "[green](目前啟用)[/green]" if profile_name == active else ""

    console.print(f"[bold]Profile: {profile_name}[/bold] {is_active}")
    console.print()
    console.print("[yellow]當前為臨時清單模式，無法顯示 profile 詳細資訊[/yellow]")
    console.print("[dim]Profile 定義檔案（profiles/*.yaml）尚未實作，詳細資訊將在 Phase 2 提供[/dim]")
