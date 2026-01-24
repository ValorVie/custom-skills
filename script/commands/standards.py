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
    """列出所有可用的 profiles"""
    profiles_dir = get_profiles_dir()
    if not profiles_dir.exists():
        return []
    return [f.stem for f in profiles_dir.glob('*.yaml')]


def get_active_profile() -> str:
    """取得目前啟用的 profile 名稱"""
    active_config = load_yaml(get_active_profile_path())
    return active_config.get('active', 'uds')


@app.command()
def status():
    """顯示目前狀態"""
    profiles_dir = get_profiles_dir()
    if not profiles_dir.exists():
        console.print("[yellow]⚠️  找不到 .standards/profiles/ 目錄[/yellow]")
        console.print("[dim]請確認當前目錄是否為已初始化 UDS 的專案[/dim]")
        return

    active = get_active_profile()
    profiles = list_profiles()

    console.print("[bold]Standards Profile 狀態[/bold]")
    console.print(f"目前啟用: [cyan]{active}[/cyan]")
    console.print(f"可用 profiles: {', '.join(profiles)}")
    console.print()

    # 載入並顯示 active profile 的描述
    profile_path = get_profiles_dir() / f"{active}.yaml"
    profile = load_yaml(profile_path)
    if profile:
        console.print(f"描述: {profile.get('description', '無')}")
        standards = profile.get('standards', [])
        console.print(f"啟用標準數量: {len(standards)}")


@app.command(name="list")
def list_cmd():
    """列出所有可用的 profiles"""
    profiles_dir = get_profiles_dir()
    if not profiles_dir.exists():
        console.print("[yellow]⚠️  找不到 .standards/profiles/ 目錄[/yellow]")
        return

    profiles = list_profiles()
    active = get_active_profile()

    table = Table(title="可用的 Standards Profiles")
    table.add_column("Profile", style="cyan")
    table.add_column("狀態", style="green")
    table.add_column("描述")

    for name in sorted(profiles):
        profile_path = get_profiles_dir() / f"{name}.yaml"
        profile = load_yaml(profile_path)
        desc = profile.get('description', '無描述')
        status_mark = "✓ 啟用中" if name == active else ""
        table.add_row(name, status_mark, desc)

    console.print(table)


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

    console.print(f"[green]✓ 已從 '{old_profile}' 切換到 '{profile_name}'[/green]")
    console.print()

    # 顯示新 profile 資訊
    profile_path = get_profiles_dir() / f"{profile_name}.yaml"
    profile = load_yaml(profile_path)
    console.print(f"描述: {profile.get('description', '無')}")

    standards = profile.get('standards', [])
    console.print(f"啟用標準數量: {len(standards)}")


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

    profile_path = get_profiles_dir() / f"{profile_name}.yaml"
    profile = load_yaml(profile_path)

    active = get_active_profile()
    is_active = "[green](目前啟用)[/green]" if profile_name == active else ""

    console.print(f"[bold]Profile: {profile_name}[/bold] {is_active}")
    console.print(f"版本: {profile.get('version', '未指定')}")
    console.print(f"描述: {profile.get('description', '無')}")
    console.print()

    # 顯示繼承
    if 'extends' in profile:
        console.print(f"繼承自: [cyan]{profile['extends']}[/cyan]")
        console.print()

    # 顯示標準列表
    standards = profile.get('standards', [])
    if standards:
        console.print("[bold]啟用的標準:[/bold]")
        for std in standards:
            console.print(f"  - {std}")
        console.print()

    # 顯示必要資源 (ECC profile)
    required = profile.get('required_resources', {})
    if required:
        console.print("[bold]必要資源:[/bold]")
        for category, items in required.items():
            console.print(f"  [cyan]{category}:[/cyan]")
            for item in items:
                console.print(f"    - {item}")
        console.print()

    # 顯示選用資源
    optional = profile.get('optional_resources', [])
    if optional:
        console.print("[bold]選用資源:[/bold]")
        for item in optional:
            console.print(f"  - {item}")
        console.print()

    # 顯示備註
    notes = profile.get('notes')
    if notes:
        console.print("[bold]備註:[/bold]")
        console.print(notes)
