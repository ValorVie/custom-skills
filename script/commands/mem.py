"""ai-dev mem — claude-mem sync server 客戶端指令。"""
from __future__ import annotations

import json
import platform
import shutil
import subprocess
import textwrap
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.table import Table

from ..utils.mem_sync import (
    api_request,
    load_server_config,
    query_local_db,
    save_server_config,
)

app = typer.Typer(help="管理 claude-mem 跨裝置同步（HTTP API backend）")
console = Console()


@app.command()
def register(
    server: str = typer.Option(..., "--server", help="Sync server URL"),
    name: str = typer.Option(..., "--name", help="裝置名稱"),
    admin_secret: str = typer.Option(..., "--admin-secret", help="Admin secret"),
) -> None:
    """向 sync server 註冊本裝置。"""
    config: dict[str, Any] = {"server_url": server}
    result = api_request(
        config,
        "POST",
        "/api/auth/register",
        body={"name": name},
        extra_headers={"X-Admin-Secret": admin_secret},
    )
    config.update({
        "api_key": result["api_key"],
        "device_name": name,
        "device_id": result["device_id"],
        "last_push_epoch": 0,
        "last_pull_epoch": 0,
        "auto_sync": False,
        "auto_sync_interval_minutes": 10,
    })
    save_server_config(config)
    console.print(f"[bold green]註冊成功[/bold green] device_id={result['device_id']}")


@app.command()
def push() -> None:
    """推送本地 claude-mem 新資料到 sync server。"""
    config = load_server_config()
    last_epoch = config.get("last_push_epoch", 0)

    sessions = query_local_db(
        "SELECT * FROM sdk_sessions WHERE started_at_epoch > ?", (last_epoch,)
    )
    observations = query_local_db(
        "SELECT * FROM observations WHERE created_at_epoch > ?", (last_epoch,)
    )
    summaries = query_local_db(
        "SELECT * FROM session_summaries WHERE created_at_epoch > ?", (last_epoch,)
    )
    prompts = query_local_db(
        "SELECT * FROM user_prompts WHERE created_at_epoch > ?", (last_epoch,)
    )

    total = len(sessions) + len(observations) + len(summaries) + len(prompts)
    if total == 0:
        console.print("[green]無新資料需要推送[/green]")
        return

    console.print(
        f"[cyan]推送中：{len(sessions)} sessions, {len(observations)} observations, "
        f"{len(summaries)} summaries, {len(prompts)} prompts[/cyan]"
    )

    result = api_request(config, "POST", "/api/sync/push", body={
        "sessions": sessions,
        "observations": observations,
        "summaries": summaries,
        "prompts": prompts,
    })

    config["last_push_epoch"] = result["server_epoch"]
    save_server_config(config)

    stats = result.get("stats", {})
    console.print(
        f"[bold green]Push 完成[/bold green] "
        f"imported: {stats.get('sessionsImported', 0)}s "
        f"{stats.get('observationsImported', 0)}o "
        f"{stats.get('summariesImported', 0)}sm "
        f"{stats.get('promptsImported', 0)}p | "
        f"skipped: {stats.get('sessionsSkipped', 0)}s "
        f"{stats.get('observationsSkipped', 0)}o "
        f"{stats.get('summariesSkipped', 0)}sm "
        f"{stats.get('promptsSkipped', 0)}p"
    )


@app.command()
def pull() -> None:
    """從 sync server 拉取其他裝置的新資料。"""
    config = load_server_config()
    last_epoch = config.get("last_pull_epoch", 0)

    all_data: dict[str, list] = {
        "sessions": [], "observations": [], "summaries": [], "prompts": []
    }
    since = last_epoch
    server_epoch = since

    while True:
        result = api_request(config, "GET", f"/api/sync/pull?since={since}&limit=500")
        for key in all_data:
            all_data[key].extend(result.get(key, []))
        server_epoch = result.get("server_epoch", server_epoch)
        if not result.get("has_more"):
            break
        since = result.get("next_since", since)

    total = sum(len(v) for v in all_data.values())
    if total == 0:
        console.print("[green]無新資料需要拉取[/green]")
        return

    console.print(
        f"[cyan]拉取到：{len(all_data['sessions'])} sessions, "
        f"{len(all_data['observations'])} observations, "
        f"{len(all_data['summaries'])} summaries, "
        f"{len(all_data['prompts'])} prompts[/cyan]"
    )

    # 透過 claude-mem 的 /api/import 匯入（含 dedup）
    import_payload = {
        "sessions": all_data["sessions"],
        "summaries": all_data["summaries"],
        "observations": all_data["observations"],
        "prompts": all_data["prompts"],
    }

    try:
        req = urllib.request.Request(
            "http://localhost:37777/api/import",
            data=json.dumps(import_payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            import_result = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError:
        console.print(
            "[bold red]claude-mem worker 未啟動（localhost:37777）。"
            "請先啟動 Claude Code。[/bold red]"
        )
        raise typer.Exit(code=1)

    config["last_pull_epoch"] = server_epoch
    save_server_config(config)

    stats = import_result.get("stats", {})
    console.print(
        f"[bold green]Pull 完成[/bold green] "
        f"imported: {stats.get('sessionsImported', 0)}s "
        f"{stats.get('observationsImported', 0)}o "
        f"{stats.get('summariesImported', 0)}sm "
        f"{stats.get('promptsImported', 0)}p | "
        f"skipped: {stats.get('sessionsSkipped', 0)}s "
        f"{stats.get('observationsSkipped', 0)}o "
        f"{stats.get('summariesSkipped', 0)}sm "
        f"{stats.get('promptsSkipped', 0)}p"
    )


@app.command()
def status() -> None:
    """顯示 sync server 同步狀態。"""
    config = load_server_config()
    result = api_request(config, "GET", "/api/sync/status")

    table = Table(title="claude-mem Sync Status")
    table.add_column("項目", style="cyan")
    table.add_column("Server 數量", style="green")
    table.add_row("Sessions", str(result.get("sessions", 0)))
    table.add_row("Observations", str(result.get("observations", 0)))
    table.add_row("Summaries", str(result.get("summaries", 0)))
    table.add_row("Prompts", str(result.get("prompts", 0)))
    table.add_row("Devices", str(result.get("devices", 0)))
    console.print(table)

    console.print(f"[dim]Last push epoch: {config.get('last_push_epoch', 0)}[/dim]")
    console.print(f"[dim]Last pull epoch: {config.get('last_pull_epoch', 0)}[/dim]")


# ---------------------------------------------------------------------------
# auto sync scheduling (launchd / cron)
# ---------------------------------------------------------------------------

LAUNCHD_LABEL = "com.ai-dev.mem-sync"
LAUNCHD_PLIST_PATH = Path("~/Library/LaunchAgents").expanduser() / f"{LAUNCHD_LABEL}.plist"
CRON_MARKER = "# ai-dev-mem-sync"


def _find_ai_dev() -> str:
    return shutil.which("ai-dev") or "ai-dev"


def _install_launchd(interval_minutes: int) -> None:
    ai_dev = _find_ai_dev()
    plist = textwrap.dedent(f"""\
        <?xml version="1.0" encoding="UTF-8"?>
        <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
          "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
        <plist version="1.0">
        <dict>
            <key>Label</key>
            <string>{LAUNCHD_LABEL}</string>
            <key>ProgramArguments</key>
            <array>
                <string>/bin/sh</string>
                <string>-c</string>
                <string>{ai_dev} mem push &amp;&amp; {ai_dev} mem pull</string>
            </array>
            <key>StartInterval</key>
            <integer>{interval_minutes * 60}</integer>
            <key>StandardOutPath</key>
            <string>/tmp/ai-dev-mem-sync.log</string>
            <key>StandardErrorPath</key>
            <string>/tmp/ai-dev-mem-sync.log</string>
        </dict>
        </plist>
    """)
    LAUNCHD_PLIST_PATH.parent.mkdir(parents=True, exist_ok=True)
    LAUNCHD_PLIST_PATH.write_text(plist, encoding="utf-8")
    subprocess.run(["launchctl", "unload", str(LAUNCHD_PLIST_PATH)],
                   capture_output=True, check=False)
    subprocess.run(["launchctl", "load", str(LAUNCHD_PLIST_PATH)],
                   capture_output=True, check=False)


def _remove_launchd() -> None:
    subprocess.run(["launchctl", "unload", str(LAUNCHD_PLIST_PATH)],
                   capture_output=True, check=False)
    LAUNCHD_PLIST_PATH.unlink(missing_ok=True)


def _install_cron(interval_minutes: int) -> None:
    ai_dev = _find_ai_dev()
    job = f"*/{interval_minutes} * * * * {ai_dev} mem push && {ai_dev} mem pull {CRON_MARKER}"
    result = subprocess.run(["crontab", "-l"], capture_output=True, text=True, check=False)
    existing = result.stdout if result.returncode == 0 else ""
    lines = [l for l in existing.splitlines() if CRON_MARKER not in l]
    lines.append(job)
    subprocess.run(["crontab", "-"], input="\n".join(lines) + "\n",
                   text=True, check=True)


def _remove_cron() -> None:
    result = subprocess.run(["crontab", "-l"], capture_output=True, text=True, check=False)
    if result.returncode != 0:
        return
    lines = [l for l in result.stdout.splitlines() if CRON_MARKER not in l]
    subprocess.run(["crontab", "-"], input="\n".join(lines) + "\n",
                   text=True, check=True)


@app.command()
def auto(
    enable: bool = typer.Option(None, "--on/--off", help="啟用或停用自動同步"),
) -> None:
    """切換 claude-mem 自動同步排程。"""
    config = load_server_config()

    if enable is None:
        status_text = "啟用" if config.get("auto_sync") else "停用"
        interval = config.get("auto_sync_interval_minutes", 10)
        console.print(f"自動同步：[bold]{status_text}[/bold]（每 {interval} 分鐘）")
        return

    system = platform.system()
    interval = config.get("auto_sync_interval_minutes", 10)

    if enable:
        if system == "Darwin":
            _install_launchd(interval)
        else:
            _install_cron(interval)
        config["auto_sync"] = True
        save_server_config(config)
        console.print(f"[bold green]自動同步已啟用[/bold green]（每 {interval} 分鐘）")
    else:
        if system == "Darwin":
            _remove_launchd()
        else:
            _remove_cron()
        config["auto_sync"] = False
        save_server_config(config)
        console.print("[bold yellow]自動同步已停用[/bold yellow]")
