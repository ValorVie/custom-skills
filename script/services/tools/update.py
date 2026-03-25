from __future__ import annotations

import subprocess
from pathlib import Path

from rich.console import Console

from script.models.execution_plan import ExecutionPlan
from script.utils.paths import get_claude_config_dir
from script.utils.shared import (
    BUN_PACKAGES,
    NPM_PACKAGES,
    check_uds_initialized,
    get_all_skill_names,
    get_npm_package_version,
    show_claude_status,
    show_skills_npm_hint,
    update_claude_code,
)
from script.utils.system import (
    check_bun_installed,
    check_command_exists,
    get_bun_package_version,
    get_bun_version,
    run_command,
)

console = Console()

def _is_completion_installed(shell: str) -> bool:
    home = Path.home()
    checks = {
        "bash": home / ".bash_completions" / "ai-dev.sh",
        "zsh": home / ".zfunc" / "_ai-dev",
        "fish": home / ".config" / "fish" / "completions" / "ai-dev.fish",
    }
    if shell in checks:
        return checks[shell].exists()
    if shell in ("powershell", "pwsh"):
        try:
            result = subprocess.run(
                [shell, "-NoProfile", "-Command", "echo", "$profile"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0 and result.stdout.strip():
                profile_path = Path(result.stdout.strip())
                if profile_path.exists():
                    content = profile_path.read_text(encoding="utf-8", errors="ignore")
                    return "ai-dev" in content
        except Exception:
            pass
        return False
    return False


def _run_install_tools_phase() -> None:
    console.print("[bold blue]檢查前置需求...[/bold blue]")

    if not check_command_exists("node"):
        console.print("[bold red]✗ 找不到 Node.js[/bold red]")
        raise SystemExit(1)

    try:
        result = subprocess.run(
            ["node", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        node_version = result.stdout.strip().replace("v", "")
        console.print(f"[green]✓[/green] Node.js {node_version}")
        major_version = int(node_version.split(".")[0])
        if major_version < 20:
            console.print("[yellow]⚠️  Node.js 版本建議 >= 20.19.0[/yellow]")
            console.print("   當前版本可能無法正常使用某些功能")
            console.print()
    except Exception:
        console.print("[green]✓[/green] Node.js 已安裝")

    if not check_command_exists("gh"):
        console.print("[yellow]⚠️  未檢測到 GitHub CLI (gh)[/yellow]")
        console.print("   建議安裝以便使用 PR 管理功能")
        console.print()
    else:
        console.print("[green]✓[/green] GitHub CLI 已安裝")

    if not check_bun_installed():
        console.print("[yellow]⚠️  未檢測到 Bun[/yellow]")
        console.print("   建議安裝以便自動安裝 Codex CLI")
        console.print()
    else:
        console.print(f"[green]✓[/green] Bun {get_bun_version()}")

    console.print()
    show_claude_status()

    console.print("[green]正在安裝全域 NPM 套件...[/green]")
    total = len(NPM_PACKAGES)
    for i, package in enumerate(NPM_PACKAGES, 1):
        existing_version = get_npm_package_version(package)
        if existing_version:
            console.print(
                f"[bold cyan][{i}/{total}][/bold cyan] {package} "
                f"[dim](已安裝 v{existing_version}，檢查更新...)[/dim]"
            )
        else:
            console.print(f"[bold cyan][{i}/{total}] 正在安裝 {package}...[/bold cyan]")
        run_command(["npm", "install", "-g", package])

    console.print("[green]正在檢查 Bun...[/green]")
    if not check_bun_installed():
        console.print("[yellow]⚠️  未檢測到 Bun，跳過 Codex 安裝[/yellow]")
    else:
        bun_version = get_bun_version()
        console.print(f"[dim]✓ Bun 已安裝 ({bun_version})[/dim]")
        console.print("[green]正在安裝 Bun 套件...[/green]")
        total = len(BUN_PACKAGES)
        for i, package in enumerate(BUN_PACKAGES, 1):
            existing_version = get_bun_package_version(package)
            if existing_version:
                console.print(
                    f"[bold cyan][{i}/{total}][/bold cyan] {package} "
                    f"[dim](已安裝 v{existing_version}，檢查更新...)[/dim]"
                )
            else:
                console.print(f"[bold cyan][{i}/{total}] 正在安裝 {package}...[/bold cyan]")
            run_command(["bun", "install", "-g", package])

    console.print()
    console.print("[green]正在設定 Shell 自動補全...[/green]")
    try:
        from typer._completion_shared import _get_shell_name, install as install_completion

        shell_name = _get_shell_name()
        if shell_name is None:
            console.print(
                "[yellow]無法偵測 Shell 類型，請手動執行：ai-dev --install-completion[/yellow]"
            )
        elif _is_completion_installed(shell_name):
            console.print(f"[dim]{shell_name} 自動補全已安裝，跳過[/dim]")
        else:
            shell, path = install_completion(prog_name="ai-dev")
            console.print(
                f"[green]{shell} 自動補全已安裝：{path}（重啟 terminal 後生效）[/green]"
            )
    except Exception:
        console.print(
            "[yellow]Shell 自動補全安裝失敗，請手動執行：ai-dev --install-completion[/yellow]"
        )


def _run_update_tools_phase() -> None:
    update_claude_code()

    console.print("[green]正在更新全域 NPM 套件...[/green]")
    total = len(NPM_PACKAGES)
    for i, package in enumerate(NPM_PACKAGES, 1):
        console.print(f"[bold cyan][{i}/{total}] 正在更新 {package}...[/bold cyan]")
        run_command(["npm", "install", "-g", package])

    if check_uds_initialized():
        console.print()
        console.print("[bold red]══════════════════════════════════════════════════════[/bold red]")
        console.print("[bold red]  ⬇ 以下為 uds (Universal Dev Standards) 指令輸出[/bold red]")
        console.print("[bold red]══════════════════════════════════════════════════════[/bold red]")
        run_command(["uds", "update"], check=False)
        console.print("[bold red]══════════════════════════════════════════════════════[/bold red]")
        console.print("[bold red]  ⬆ uds 指令執行完畢，以下回到 ai-dev 流程[/bold red]")
        console.print("[bold red]══════════════════════════════════════════════════════[/bold red]")
        console.print()
    else:
        console.print("[dim]ℹ️  當前目錄未初始化 Standards（跳過 uds update）[/dim]")
        console.print("[dim]   如需在此專案使用，請執行: uds init[/dim]")

    console.print()
    console.print("[bold red]══════════════════════════════════════════════════════[/bold red]")
    console.print("[bold red]  ⬇ 以下為 npx skills (Skills CLI) 指令輸出[/bold red]")
    console.print("[bold red]══════════════════════════════════════════════════════[/bold red]")
    run_command(["npx", "skills", "update"], check=False)
    console.print("[bold red]══════════════════════════════════════════════════════[/bold red]")
    console.print("[bold red]  ⬆ npx skills 指令執行完畢，以下回到 ai-dev 流程[/bold red]")
    console.print("[bold red]══════════════════════════════════════════════════════[/bold red]")
    console.print()

    console.print("[green]正在更新 Bun 套件...[/green]")
    if check_bun_installed():
        total = len(BUN_PACKAGES)
        for i, package in enumerate(BUN_PACKAGES, 1):
            console.print(f"[bold cyan][{i}/{total}] 正在更新 {package}...[/bold cyan]")
            run_command(["bun", "install", "-g", package])
    else:
        console.print("[yellow]⚠️  Bun 未安裝，跳過 Bun 套件更新[/yellow]")

    marketplace_dir = get_claude_config_dir() / "plugins" / "marketplaces"
    if marketplace_dir.exists():
        marketplaces = [
            path.name
            for path in marketplace_dir.iterdir()
            if path.is_dir() and not path.name.startswith(".")
        ]
        if marketplaces:
            console.print(
                f"[green]正在更新 {len(marketplaces)} 個 Plugin Marketplace...[/green]"
            )
            for marketplace in marketplaces:
                console.print(f"  正在更新 {marketplace}...")
                run_command(
                    ["claude", "plugin", "marketplace", "update", marketplace],
                    check=False,
                )
            console.print(f"[bold cyan]已更新 {len(marketplaces)} 個 Marketplace[/bold cyan]")
        else:
            console.print("[dim]未偵測到已安裝的 Plugin Marketplace[/dim]")
    else:
        console.print("[dim]未偵測到 Claude Code Plugin 目錄[/dim]")


def _show_install_skill_hints() -> None:
    console.print()
    console.print(
        "[yellow]⚠️ 已安裝的 Skills（建立自訂 skill 時請避免使用重複名稱）：[/yellow]"
    )
    for name in get_all_skill_names():
        console.print(f"   - {name}")
    console.print()
    console.print(
        "[dim]提示：使用獨特前綴（如 user-、local-、公司名-）來避免名稱衝突[/dim]"
    )
    show_skills_npm_hint()


def run_tools_phase(*, plan: ExecutionPlan) -> None:
    """Run tools-related work for a pipeline plan."""
    if plan.dry_run:
        console.print(f"[dim][dry-run] {plan.command_name}: tools[/dim]")
        return

    if plan.command_name == "install":
        _run_install_tools_phase()
        return
    if plan.command_name == "update":
        _run_update_tools_phase()
        return
    raise ValueError(f"Unsupported tools phase for {plan.command_name}")


def run_install_postflight() -> None:
    _show_install_skill_hints()
