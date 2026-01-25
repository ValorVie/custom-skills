"""
Standards Profile Manager
基於重疊檢測的標準體系配置管理

用法:
    ai-dev standards status              # 顯示目前狀態
    ai-dev standards list                # 列出可用 profiles
    ai-dev standards switch <name>       # 切換 profile
    ai-dev standards switch <name> --dry-run  # 預覽切換影響
    ai-dev standards show <name>         # 顯示 profile 內容
    ai-dev standards overlaps            # 顯示重疊定義
"""

from pathlib import Path
from datetime import datetime
from typing import Any

import typer
import yaml
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree

from ..utils.shared import (
    disable_resource,
    enable_resource,
    get_target_path,
    list_disabled_resources,
)

app = typer.Typer(help="管理標準體系配置（基於重疊檢測）")
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


def get_claude_disabled_path() -> Path:
    """取得 .claude/disabled.yaml 路徑"""
    return get_project_root() / '.claude' / 'disabled.yaml'


def get_overlaps_path() -> Path:
    """取得 overlaps.yaml 路徑"""
    return get_profiles_dir() / 'overlaps.yaml'


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

    從 profiles 目錄讀取 *.yaml 檔案（排除 overlaps.yaml）。
    """
    profiles_dir = get_profiles_dir()
    if not profiles_dir.exists():
        return []

    profiles = []
    for f in profiles_dir.glob('*.yaml'):
        if f.name != 'overlaps.yaml':
            profiles.append(f.stem)
    return sorted(profiles)


def load_overlaps() -> dict:
    """載入重疊定義"""
    overlaps_path = get_overlaps_path()
    if not overlaps_path.exists():
        raise FileNotFoundError(
            "overlaps.yaml not found. "
            "Please ensure profiles/overlaps.yaml exists."
        )
    return load_yaml(overlaps_path)


def load_profile(profile_name: str) -> dict:
    """載入指定的 profile 定義"""
    profile_path = get_profiles_dir() / f'{profile_name}.yaml'
    if not profile_path.exists():
        raise FileNotFoundError(f"Profile '{profile_name}' not found")
    return load_yaml(profile_path)


def load_disabled_yaml() -> dict:
    """載入 disabled.yaml"""
    disabled_path = get_claude_disabled_path()
    if not disabled_path.exists():
        return {}
    return load_yaml(disabled_path)


def save_disabled_yaml(data: dict) -> None:
    """儲存 disabled.yaml"""
    disabled_path = get_claude_disabled_path()
    disabled_path.parent.mkdir(parents=True, exist_ok=True)
    save_yaml(disabled_path, data)


def collect_items(items_def: dict) -> set:
    """從項目定義收集所有項目名稱（含類型前綴）

    Args:
        items_def: 項目定義字典，如 {"skills": ["a", "b"], "standards": ["c"]}

    Returns:
        set: 項目名稱集合（格式：類型:名稱）
    """
    result = set()
    for item_type, items in items_def.items():
        if item_type in ('description', 'mutual_exclusive'):
            continue
        if isinstance(items, list):
            for item in items:
                result.add(f"{item_type}:{item}")
    return result


def get_items_by_type(items: set, item_type: str) -> list:
    """從項目集合中提取指定類型的項目名稱"""
    prefix = f"{item_type}:"
    return sorted([
        item[len(prefix):] for item in items
        if item.startswith(prefix)
    ])


def compute_disabled_items(overlaps: dict, profile: dict) -> set:
    """計算需要停用的項目

    新邏輯（v1.2.0）：
    - shared: 永遠不停用
    - groups: 只啟用偏好體系的項目，停用其他體系獨有的項目
    - exclusive: 根據 enable_exclusive 設定決定是否停用

    Args:
        overlaps: 重疊定義
        profile: Profile 定義

    Returns:
        set: 需停用的項目集合（格式：類型:名稱）
    """
    to_disable = set()
    pref = profile.get('overlap_preference', 'uds')
    enabled_groups = profile.get('enabled_groups', list(overlaps.get('groups', {}).keys()))

    # 1. 處理功能群組
    # 特殊處理：當 pref 為 'all' 時，不停用任何 groups 項目
    if pref != 'all':
        for group_name, group_def in overlaps.get('groups', {}).items():
            if group_name not in enabled_groups:
                # 停用整個群組的所有項目
                for system_name, items in group_def.items():
                    if system_name not in ('description', 'mutual_exclusive'):
                        to_disable.update(collect_items(items if isinstance(items, dict) else {}))
            else:
                # 群組已啟用：只啟用偏好體系的項目，停用其他體系獨有的項目
                pref_items = collect_items(group_def.get(pref, {}))

                for system_name, items in group_def.items():
                    if system_name not in ('description', 'mutual_exclusive'):
                        if system_name != pref:
                            other_items = collect_items(items if isinstance(items, dict) else {})
                            # 停用「其他體系有但偏好體系沒有」的項目
                            to_disable.update(other_items - pref_items)

    # 2. 處理獨有項目
    for system_name, system_def in overlaps.get('exclusive', {}).items():
        # 預設：啟用偏好體系的獨有功能，停用其他體系的獨有功能
        should_enable = profile.get('enable_exclusive', {}).get(system_name, system_name == pref)
        if not should_enable:
            to_disable.update(collect_items(system_def if isinstance(system_def, dict) else {}))

    # 3. 處理共用項目（永遠不停用）
    shared_items = collect_items(overlaps.get('shared', {}))
    to_disable -= shared_items

    # 4. 處理例外（從停用清單中移除）
    exceptions = profile.get('exceptions', {})
    for item in exceptions.get('enable', []):
        # 例外項目可能不含類型前綴，需要嘗試各種類型
        for item_type in ('skills', 'standards', 'commands', 'agents', 'hooks'):
            to_disable.discard(f"{item_type}:{item}")

    return to_disable


def sync_resources(disabled: dict, target: str = "claude", dry_run: bool = False) -> dict:
    """根據 disabled.yaml 同步實際的檔案狀態

    Args:
        disabled: disabled.yaml 的內容
        target: 目標工具 (claude, opencode, etc.)
        dry_run: 是否僅預覽變更

    Returns:
        dict: 同步結果 {success, disabled_count, enabled_count, warnings}
    """
    result = {
        "success": False,
        "disabled_count": 0,
        "enabled_count": 0,
        "warnings": []
    }

    try:
        # 要停用的 skills 和 commands
        skills_to_disable = set(disabled.get('skills', []))
        commands_to_disable = set(disabled.get('commands', []))
        agents_to_disable = set(disabled.get('agents', []))

        # 目前已停用的項目（在 disabled 目錄中）
        currently_disabled_skills = set(list_disabled_resources(target, 'skills'))
        currently_disabled_commands = set(list_disabled_resources(target, 'commands'))
        currently_disabled_agents = set(list_disabled_resources(target, 'agents'))

        # 計算需要的操作
        skills_to_actually_disable = skills_to_disable - currently_disabled_skills
        skills_to_enable = currently_disabled_skills - skills_to_disable

        commands_to_actually_disable = commands_to_disable - currently_disabled_commands
        commands_to_enable = currently_disabled_commands - commands_to_disable

        agents_to_actually_disable = agents_to_disable - currently_disabled_agents
        agents_to_enable = currently_disabled_agents - agents_to_disable

        # standards 警告
        standards_to_disable = disabled.get('standards', [])
        if standards_to_disable:
            result['warnings'].append(
                f"有 {len(standards_to_disable)} 個 standards (*.ai.yaml) 無法自動同步"
            )

        if dry_run:
            result['success'] = True
            result['to_disable'] = {
                'skills': sorted(skills_to_actually_disable),
                'commands': sorted(commands_to_actually_disable),
                'agents': sorted(agents_to_actually_disable)
            }
            result['to_enable'] = {
                'skills': sorted(skills_to_enable),
                'commands': sorted(commands_to_enable),
                'agents': sorted(agents_to_enable)
            }
            return result

        # 執行操作（靜默模式，避免每個操作都印出訊息）
        success_count = 0
        fail_count = 0

        # 停用 skills
        for name in skills_to_actually_disable:
            if disable_resource(target, 'skills', name, quiet=True):
                success_count += 1
            else:
                fail_count += 1

        # 啟用 skills
        for name in skills_to_enable:
            if enable_resource(target, 'skills', name, quiet=True):
                success_count += 1
            else:
                fail_count += 1

        # 停用 commands
        for name in commands_to_actually_disable:
            if disable_resource(target, 'commands', name, quiet=True):
                success_count += 1
            else:
                fail_count += 1

        # 啟用 commands
        for name in commands_to_enable:
            if enable_resource(target, 'commands', name, quiet=True):
                success_count += 1
            else:
                fail_count += 1

        # 停用 agents
        for name in agents_to_actually_disable:
            if disable_resource(target, 'agents', name, quiet=True):
                success_count += 1
            else:
                fail_count += 1

        # 啟用 agents
        for name in agents_to_enable:
            if enable_resource(target, 'agents', name, quiet=True):
                success_count += 1
            else:
                fail_count += 1

        result['success'] = True
        result['disabled_count'] = len(skills_to_actually_disable) + len(commands_to_actually_disable) + len(agents_to_actually_disable)
        result['enabled_count'] = len(skills_to_enable) + len(commands_to_enable) + len(agents_to_enable)
        result['failed_count'] = fail_count

    except Exception as e:
        result['error'] = str(e)

    return result


def switch_profile(target_profile: str, dry_run: bool = False, auto_sync: bool = True) -> dict:
    """切換到指定的 Profile

    Args:
        target_profile: 目標 profile 名稱
        dry_run: 是否僅預覽變更
        auto_sync: 是否自動同步檔案狀態

    Returns:
        dict: 切換結果
    """
    result = {
        "success": False,
        "profile": target_profile,
        "disabled_items": [],
        "enabled_items": [],
        "warnings": [],
        "sync_result": None
    }

    try:
        # 1. 載入配置
        overlaps = load_overlaps()
        profile = load_profile(target_profile)
        current_disabled = load_disabled_yaml()

        # 2. 計算需停用的項目
        to_disable = compute_disabled_items(overlaps, profile)

        # 3. 保留手動停用的項目
        manual_disabled = set(current_disabled.get('_manual', []))

        if dry_run:
            # 只回傳預覽結果
            result['success'] = True
            result['disabled_items'] = sorted(to_disable)
            result['manual_items'] = sorted(manual_disabled)
            return result

        # 4. 更新 disabled.yaml
        merged_disabled = to_disable.union(manual_disabled)
        new_disabled = {
            '_profile': target_profile,
            '_profile_disabled': sorted(to_disable),
            '_manual': sorted(manual_disabled),
            # 合併為扁平結構供其他工具讀取
            'skills': get_items_by_type(merged_disabled, 'skills'),
            'commands': get_items_by_type(merged_disabled, 'commands'),
            'agents': get_items_by_type(merged_disabled, 'agents'),
            'standards': get_items_by_type(merged_disabled, 'standards'),
            'hooks': get_items_by_type(merged_disabled, 'hooks'),
        }
        save_disabled_yaml(new_disabled)

        # 5. 更新 active-profile.yaml
        active_path = get_active_profile_path()
        active_config = load_yaml(active_path)
        active_config['active'] = target_profile
        active_config['last_updated'] = datetime.now().strftime('%Y-%m-%d')
        save_yaml(active_path, active_config)

        result['success'] = True
        result['disabled_items'] = sorted(to_disable)

        # 6. 自動同步檔案狀態（如果啟用）
        if auto_sync and not dry_run:
            sync_result = sync_resources(new_disabled, target="claude", dry_run=False)
            result['sync_result'] = sync_result
            if sync_result.get('warnings'):
                result['warnings'].extend(sync_result['warnings'])

    except Exception as e:
        result['error'] = str(e)

    return result


def get_active_profile() -> str:
    """取得目前啟用的 profile 名稱"""
    active_config = load_yaml(get_active_profile_path())
    return active_config.get('active', 'uds')


@app.command()
def status():
    """顯示目前狀態（含停用項目統計）"""
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

    # 顯示停用項目統計
    disabled = load_disabled_yaml()
    if disabled:
        console.print()
        console.print("[bold]停用項目統計：[/bold]")
        profile_disabled = disabled.get('_profile_disabled', [])
        manual_disabled = disabled.get('_manual', [])
        console.print(f"  Profile 停用: {len(profile_disabled)} 項")
        console.print(f"  手動停用: {len(manual_disabled)} 項")

        # 各類型統計
        for item_type in ('skills', 'commands', 'agents', 'standards', 'hooks'):
            items = disabled.get(item_type, [])
            if items:
                console.print(f"  {item_type}: {len(items)} 項停用")


@app.command(name="list")
def list_cmd():
    """列出所有可用的 profiles（含重疊偏好）"""
    if not is_standards_initialized():
        console.print("[yellow]⚠️  專案尚未初始化標準體系[/yellow]")
        console.print("[dim]請執行 'ai-dev project init' 初始化專案[/dim]")
        return

    profiles = list_profiles()
    if not profiles:
        console.print("[yellow]無可用的 profiles[/yellow]")
        return

    active = get_active_profile()

    table = Table(title="可用的 Standards Profiles")
    table.add_column("Profile", style="cyan")
    table.add_column("顯示名稱", style="white")
    table.add_column("偏好", style="dim")
    table.add_column("狀態", style="green")

    for name in sorted(profiles):
        try:
            profile = load_profile(name)
            display_name = profile.get('display_name', name)
            pref = profile.get('overlap_preference', 'uds')
            status_mark = "✓ 啟用中" if name == active else ""
            table.add_row(name, display_name, pref, status_mark)
        except Exception:
            table.add_row(name, name, "?", "")

    console.print(table)


@app.command()
def switch(
    profile_name: str = typer.Argument(..., help="要切換的 profile 名稱"),
    dry_run: bool = typer.Option(False, "--dry-run", "-n", help="只顯示變更，不實際執行"),
):
    """切換到指定的 profile（基於重疊檢測）"""
    profiles = list_profiles()

    if profile_name not in profiles:
        console.print(f"[red]錯誤: Profile '{profile_name}' 不存在[/red]")
        console.print(f"可用的 profiles: {', '.join(profiles)}")
        raise typer.Exit(1)

    old_profile = get_active_profile()

    if old_profile == profile_name and not dry_run:
        console.print(f"[yellow]已經在使用 '{profile_name}' profile[/yellow]")
        return

    # 執行切換
    result = switch_profile(profile_name, dry_run=dry_run)

    if dry_run:
        console.print(f"[cyan]預覽切換到 {profile_name}[/cyan]")
        console.print()
        disabled_items = result.get('disabled_items', [])
        console.print(f"[bold]將停用的項目 ({len(disabled_items)}):[/bold]")
        for item in disabled_items[:20]:  # 只顯示前 20 項
            console.print(f"  [red]- {item}[/red]")
        if len(disabled_items) > 20:
            console.print(f"  [dim]... 還有 {len(disabled_items) - 20} 項[/dim]")
        console.print()
        console.print("[dim]使用 'ai-dev standards switch {profile_name}' 執行切換[/dim]")
        return

    if result.get('success'):
        console.print(f"[green]✓ 成功從 '{old_profile}' 切換到 '{profile_name}'[/green]")
        disabled_items = result.get('disabled_items', [])
        console.print(f"  設定檔更新: 停用 {len(disabled_items)} 個項目")

        # 顯示同步結果
        sync_result = result.get('sync_result')
        if sync_result:
            disabled_count = sync_result.get('disabled_count', 0)
            enabled_count = sync_result.get('enabled_count', 0)
            if disabled_count > 0 or enabled_count > 0:
                console.print(f"  檔案同步: 停用 {disabled_count} 個, 啟用 {enabled_count} 個")
            else:
                console.print(f"  檔案同步: 無需變更")

        if result.get('warnings'):
            console.print()
            for warning in result['warnings']:
                console.print(f"[yellow]⚠️  {warning}[/yellow]")

        console.print()
        console.print("[yellow]⚠️  請重啟 Claude Code 以套用變更[/yellow]")
    else:
        console.print(f"[red]✗ 切換失敗: {result.get('error')}[/red]")
        raise typer.Exit(1)


@app.command()
def show(
    profile_name: str = typer.Argument(..., help="要顯示的 profile 名稱")
):
    """顯示指定 profile 的詳細內容（含重疊分析）"""
    profiles = list_profiles()

    if profile_name not in profiles:
        console.print(f"[red]錯誤: Profile '{profile_name}' 不存在[/red]")
        console.print(f"可用的 profiles: {', '.join(profiles)}")
        raise typer.Exit(1)

    try:
        profile = load_profile(profile_name)
        overlaps = load_overlaps()
    except Exception as e:
        console.print(f"[red]載入失敗: {e}[/red]")
        raise typer.Exit(1)

    active = get_active_profile()
    is_active = "[green](目前啟用)[/green]" if profile_name == active else ""

    # 標題
    console.print(Panel(
        f"[bold cyan]{profile.get('display_name', profile_name)}[/bold cyan]\n"
        f"[dim]{profile.get('description', '')}[/dim]",
        title=f"Profile: {profile_name} {is_active}",
    ))

    # 重疊偏好
    pref = profile.get('overlap_preference', 'uds')
    console.print(f"\n[bold]重疊偏好:[/bold] {pref}")

    # 顯示各群組的選擇
    console.print(f"\n[bold]重疊群組選擇:[/bold]")
    enabled_groups = profile.get('enabled_groups', list(overlaps.get('groups', {}).keys()))

    for group_name, group_def in overlaps.get('groups', {}).items():
        if group_name not in enabled_groups:
            console.print(f"  [dim]{group_name}: 已停用[/dim]")
            continue

        items = group_def.get(pref, {})
        desc = group_def.get('description', '')
        console.print(f"  [cyan]{group_name}[/cyan]: 使用 {pref} 版本 [dim]({desc})[/dim]")
        for item_type, item_list in items.items():
            if item_type not in ('description', 'mutual_exclusive') and item_list:
                console.print(f"    {item_type}: {', '.join(item_list)}")

    # 顯示獨有功能啟用狀態
    console.print(f"\n[bold]獨有功能啟用狀態:[/bold]")
    for system, enabled in profile.get('enable_exclusive', {}).items():
        status_str = "[green]啟用[/green]" if enabled else "[red]停用[/red]"
        console.print(f"  {system}: {status_str}")

    # 顯示例外
    exceptions = profile.get('exceptions', {})
    if exceptions.get('enable'):
        console.print(f"\n[bold]例外啟用項目:[/bold]")
        for item in exceptions.get('enable', []):
            console.print(f"  [green]+ {item}[/green]")


@app.command()
def overlaps():
    """顯示重疊定義摘要"""
    try:
        overlaps_data = load_overlaps()
    except FileNotFoundError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)

    console.print(Panel(
        f"版本: {overlaps_data.get('version', 'unknown')}\n"
        f"{overlaps_data.get('description', '')}",
        title="重疊定義 (overlaps.yaml)",
    ))

    # 群組
    console.print(f"\n[bold]重疊群組 ({len(overlaps_data.get('groups', {}))}):[/bold]")
    for group_name, group_def in overlaps_data.get('groups', {}).items():
        desc = group_def.get('description', '')
        systems = [k for k in group_def.keys() if k not in ('description', 'mutual_exclusive')]
        console.print(f"  [cyan]{group_name}[/cyan]: {desc}")
        console.print(f"    體系: {', '.join(systems)}")

    # 獨有項目
    console.print(f"\n[bold]獨有項目:[/bold]")
    for system_name, system_def in overlaps_data.get('exclusive', {}).items():
        if isinstance(system_def, dict):
            total = sum(len(v) for k, v in system_def.items() if isinstance(v, list))
            console.print(f"  [cyan]{system_name}[/cyan]: {total} 個項目")
            for item_type, items in system_def.items():
                if isinstance(items, list) and items:
                    console.print(f"    {item_type}: {len(items)} 個")


@app.command()
def sync(
    dry_run: bool = typer.Option(False, "--dry-run", "-n", help="只顯示變更，不實際執行"),
    target: str = typer.Option("claude", "--target", "-t", help="目標工具 (claude, opencode, etc.)"),
):
    """根據 disabled.yaml 同步實際的檔案狀態

    此命令會：
    1. 讀取 disabled.yaml 中的停用項目
    2. 將對應的 skills/commands 移動到 disabled 目錄
    3. 將不在停用列表中的項目從 disabled 目錄還原

    注意：standards (*.ai.yaml) 是專案內檔案，無法透過此命令同步。
    """
    disabled = load_disabled_yaml()
    if not disabled:
        console.print("[yellow]disabled.yaml 不存在或為空[/yellow]")
        return

    profile = disabled.get('_profile', 'unknown')
    console.print(f"[bold]同步 Profile: {profile}[/bold]")
    console.print(f"目標工具: {target}")

    # 要停用的 skills 和 commands
    skills_to_disable = set(disabled.get('skills', []))
    commands_to_disable = set(disabled.get('commands', []))
    agents_to_disable = set(disabled.get('agents', []))

    # 目前已停用的項目（在 disabled 目錄中）
    currently_disabled_skills = set(list_disabled_resources(target, 'skills'))
    currently_disabled_commands = set(list_disabled_resources(target, 'commands'))
    currently_disabled_agents = set(list_disabled_resources(target, 'agents'))

    # 計算需要的操作
    skills_to_actually_disable = skills_to_disable - currently_disabled_skills
    skills_to_enable = currently_disabled_skills - skills_to_disable

    commands_to_actually_disable = commands_to_disable - currently_disabled_commands
    commands_to_enable = currently_disabled_commands - commands_to_disable

    agents_to_actually_disable = agents_to_disable - currently_disabled_agents
    agents_to_enable = currently_disabled_agents - agents_to_disable

    # 顯示計畫
    console.print()
    console.print("[bold]Skills:[/bold]")
    for name in sorted(skills_to_actually_disable):
        console.print(f"  [red]- 停用: {name}[/red]")
    for name in sorted(skills_to_enable):
        console.print(f"  [green]+ 啟用: {name}[/green]")
    if not skills_to_actually_disable and not skills_to_enable:
        console.print("  [dim]無變更[/dim]")

    console.print()
    console.print("[bold]Commands:[/bold]")
    for name in sorted(commands_to_actually_disable):
        console.print(f"  [red]- 停用: {name}[/red]")
    for name in sorted(commands_to_enable):
        console.print(f"  [green]+ 啟用: {name}[/green]")
    if not commands_to_actually_disable and not commands_to_enable:
        console.print("  [dim]無變更[/dim]")

    console.print()
    console.print("[bold]Agents:[/bold]")
    for name in sorted(agents_to_actually_disable):
        console.print(f"  [red]- 停用: {name}[/red]")
    for name in sorted(agents_to_enable):
        console.print(f"  [green]+ 啟用: {name}[/green]")
    if not agents_to_actually_disable and not agents_to_enable:
        console.print("  [dim]無變更[/dim]")

    # standards 警告
    standards_to_disable = disabled.get('standards', [])
    if standards_to_disable:
        console.print()
        console.print("[yellow]⚠️  Standards (*.ai.yaml) 無法透過此命令同步[/yellow]")
        console.print(f"[dim]  有 {len(standards_to_disable)} 個 standards 在停用列表中[/dim]")
        console.print("[dim]  這些檔案在專案目錄中，需手動處理或修改 CLAUDE.md[/dim]")

    if dry_run:
        console.print()
        console.print("[dim]Dry-run 模式，未執行任何變更[/dim]")
        return

    # 執行操作（靜默模式，避免每個操作都印出訊息）
    console.print()
    console.print("[bold]執行同步...[/bold]")

    success_count = 0
    fail_count = 0

    # 停用 skills
    for name in skills_to_actually_disable:
        if disable_resource(target, 'skills', name, quiet=True):
            success_count += 1
        else:
            fail_count += 1

    # 啟用 skills
    for name in skills_to_enable:
        if enable_resource(target, 'skills', name, quiet=True):
            success_count += 1
        else:
            fail_count += 1

    # 停用 commands
    for name in commands_to_actually_disable:
        if disable_resource(target, 'commands', name, quiet=True):
            success_count += 1
        else:
            fail_count += 1

    # 啟用 commands
    for name in commands_to_enable:
        if enable_resource(target, 'commands', name, quiet=True):
            success_count += 1
        else:
            fail_count += 1

    # 停用 agents
    for name in agents_to_actually_disable:
        if disable_resource(target, 'agents', name, quiet=True):
            success_count += 1
        else:
            fail_count += 1

    # 啟用 agents
    for name in agents_to_enable:
        if enable_resource(target, 'agents', name, quiet=True):
            success_count += 1
        else:
            fail_count += 1

    console.print()
    console.print(f"[green]✓ 同步完成: {success_count} 成功, {fail_count} 失敗[/green]")

    if success_count > 0:
        console.print()
        console.print("[yellow]⚠️  請重啟 Claude Code 以套用變更[/yellow]")
