import typer
import shutil
import subprocess
from pathlib import Path
from rich.console import Console
from rich.table import Table
from ..utils.shared import REPOS
from ..utils.paths import get_project_root

app = typer.Typer()
console = Console()


@app.command()
def status():
    """檢查環境狀態與工具版本。"""
    console.print("[bold blue]AI 開發環境狀態檢查[/bold blue]")

    table = Table(title="核心工具")
    table.add_column("工具", style="cyan")
    table.add_column("狀態", style="green")
    table.add_column("版本/路徑", style="yellow")

    # 檢查 Node.js
    node_path = shutil.which("node")
    if node_path:
        try:
            version = subprocess.check_output(["node", "--version"], text=True).strip()
            table.add_row("Node.js", "已安裝", version)
        except Exception:
            table.add_row("Node.js", "錯誤", "無法取得版本")
    else:
        table.add_row("Node.js", "未安裝", "-")

    # 檢查 Git
    git_path = shutil.which("git")
    if git_path:
        try:
            version = subprocess.check_output(["git", "--version"], text=True).strip()
            table.add_row("Git", "已安裝", version)
        except Exception:
            table.add_row("Git", "錯誤", "無法取得版本")
    else:
        table.add_row("Git", "未安裝", "-")

    console.print(table)
    console.print()

    # 檢查 NPM 套件
    npm_table = Table(title="全域 NPM 套件")
    npm_table.add_column("套件", style="cyan")
    npm_table.add_column("狀態", style="green")

    packages = [
        "@anthropic-ai/claude-code",
        "@fission-ai/openspec",
        "@google/gemini-cli",
        "universal-dev-standards",
        "opencode-ai",
        "skills",
    ]

    for pkg in packages:
        # 使用 npm list -g --depth=0 檢查
        # 這比較慢，但為了準確性
        try:
            # 簡化檢查：shutil.which 對於套件 binary 可能有用，例如 claude, openspec, gemini, uds, opencode
            binary_map = {
                "@anthropic-ai/claude-code": "claude",
                "@fission-ai/openspec": "openspec",
                "@google/gemini-cli": "gemini",
                "universal-dev-standards": "uds",
                "opencode-ai": "opencode",
            }
            bin_name = binary_map.get(pkg, pkg)
            if shutil.which(bin_name):
                npm_table.add_row(pkg, "已安裝")
            else:
                npm_table.add_row(pkg, "未找到指令")
        except Exception:
            npm_table.add_row(pkg, "檢查失敗")

    console.print(npm_table)
    console.print()

    # 檢查設定儲存庫
    repo_table = Table(title="設定儲存庫")
    repo_table.add_column("名稱", style="cyan")
    repo_table.add_column("本地狀態", style="green")

    # REPOS key → 顯示名稱對應（與 update 輸出和 sources.yaml 一致）
    repo_display_names = {
        "custom_skills": "custom-skills",
        "superpowers": "superpowers",
        "uds": "universal-dev-standards",
        "obsidian_skills": "obsidian-skills",
        "anthropic_skills": "anthropic-skills",
        "everything_claude_code": "everything-claude-code",
    }

    for repo_key, (_, path_fn) in REPOS.items():
        display_name = repo_display_names.get(repo_key, repo_key.replace("_", "-"))
        path = path_fn()
        if not path.exists():
            repo_table.add_row(display_name, "[red]未安裝[/red]")
            continue
        if not (path / ".git").exists():
            repo_table.add_row(display_name, "目錄存在 (非 Git)")
            continue
        # 比對本地 HEAD vs origin HEAD
        try:
            local_head = subprocess.check_output(
                ["git", "rev-parse", "HEAD"],
                cwd=str(path), text=True, stderr=subprocess.DEVNULL,
            ).strip()
            remote_head = subprocess.check_output(
                ["git", "rev-parse", "origin/main"],
                cwd=str(path), text=True, stderr=subprocess.DEVNULL,
            ).strip()
            if local_head == remote_head:
                repo_table.add_row(display_name, "[green]✓ 最新[/green]")
            else:
                repo_table.add_row(display_name, "[yellow]↑ 有可用更新[/yellow]")
        except Exception:
            repo_table.add_row(display_name, "Git 儲存庫 (正常)")

    console.print(repo_table)
    console.print()

    # 上游同步狀態
    last_sync_path = get_project_root() / "upstream" / "last-sync.yaml"
    sources_path = get_project_root() / "upstream" / "sources.yaml"
    if last_sync_path.exists():
        import yaml

        try:
            with open(last_sync_path, "r", encoding="utf-8") as f:
                last_sync = yaml.safe_load(f) or {}
        except Exception:
            last_sync = {}

        # 從 sources.yaml 讀取 local_path 對應
        sources_map: dict[str, Path] = {}
        if sources_path.exists():
            try:
                with open(sources_path, "r", encoding="utf-8") as f:
                    sources_data = yaml.safe_load(f) or {}
                for name, info in sources_data.get("sources", {}).items():
                    local_path = info.get("local_path", "")
                    if local_path:
                        sources_map[name] = Path(
                            local_path.replace("~", str(Path.home()))
                        )
            except Exception:
                pass

        if last_sync and sources_map:
            sync_table = Table(title="上游同步狀態")
            sync_table.add_column("名稱", style="cyan")
            sync_table.add_column("同步於", style="dim")
            sync_table.add_column("狀態", style="green")

            for name in sorted(last_sync.keys()):
                entry = last_sync[name]
                sync_commit = entry.get("commit", "")
                synced_at = entry.get("synced_at", "")

                # 格式化日期為 MM-DD
                date_display = ""
                if synced_at:
                    try:
                        date_display = synced_at[5:10]  # YYYY-MM-DD → MM-DD
                    except (IndexError, TypeError):
                        date_display = str(synced_at)[:10]

                repo_path = sources_map.get(name)
                if not repo_path or not repo_path.exists():
                    sync_table.add_row(name, date_display, "[red]未安裝[/red]")
                    continue

                if not sync_commit:
                    sync_table.add_row(name, date_display, "[dim]? 無 commit 記錄[/dim]")
                    continue

                try:
                    current_head = subprocess.check_output(
                        ["git", "rev-parse", "HEAD"],
                        cwd=str(repo_path), text=True, stderr=subprocess.DEVNULL,
                    ).strip()

                    if current_head == sync_commit:
                        sync_table.add_row(name, date_display, "[green]✓ 同步[/green]")
                    else:
                        # 計算落後 commit 數
                        try:
                            count_output = subprocess.check_output(
                                ["git", "rev-list", "--count", f"{sync_commit}..HEAD"],
                                cwd=str(repo_path), text=True, stderr=subprocess.DEVNULL,
                            ).strip()
                            behind_count = int(count_output)
                            sync_table.add_row(
                                name, date_display,
                                f"[yellow]⚠ 落後 {behind_count} 個 commit[/yellow]",
                            )
                        except Exception:
                            sync_table.add_row(
                                name, date_display,
                                "[yellow]⚠ 落後[/yellow]",
                            )
                except Exception:
                    sync_table.add_row(name, date_display, "[dim]? 無法比對[/dim]")

            console.print(sync_table)
