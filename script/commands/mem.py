"""ai-dev mem — claude-mem sync server 客戶端指令。"""

from __future__ import annotations

import json
import platform
import shutil
import sqlite3
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
    CLAUDE_MEM_DB_PATH,
    api_request,
    append_pulled_hashes,
    compute_content_hash,
    get_indexed_observation_ids,
    import_to_local_db,
    load_pulled_hashes,
    load_server_config,
    push_preflight,
    query_local_db,
    reindex_observations,
    save_server_config,
    worker_available,
)

app = typer.Typer(help="管理 claude-mem 跨裝置同步（HTTP API backend）")
console = Console()


def _normalize_summaries_for_push(
    summaries: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], int]:
    """兼容本地 schema：將 memory_session_id 映射到 session_id。"""
    normalized: list[dict[str, Any]] = []
    skipped = 0

    for summary in summaries:
        payload = dict(summary)
        if not payload.get("session_id"):
            payload["session_id"] = payload.get("memory_session_id")

        if not payload.get("session_id"):
            skipped += 1
            continue

        normalized.append(payload)

    return normalized, skipped


def _api_request_or_exit(
    config: dict[str, Any],
    method: str,
    path: str,
    body: dict | None = None,
    extra_headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    try:
        return api_request(config, method, path, body=body, extra_headers=extra_headers)
    except RuntimeError as e:
        message = str(e)
        if "HTTP 401" in message and "Invalid API key" in message:
            server_url = config.get("server_url", "<server-url>")
            device_name = config.get("device_name", "<device-name>")
            console.print("[bold red]API key 無效或已失效[/bold red]")
            console.print(
                "[yellow]請重新註冊：[/yellow]"
                f"ai-dev mem register --server {server_url} --name {device_name} "
                "--admin-secret <ADMIN_SECRET>"
            )
        else:
            console.print(f"[bold red]{message}[/bold red]")
        raise typer.Exit(code=1)


def _load_server_config_or_exit(
    *,
    allow_missing_preview: bool = False,
) -> dict[str, Any]:
    try:
        return load_server_config()
    except FileNotFoundError as e:
        if allow_missing_preview:
            console.print(
                "[yellow]未設定 sync server；dry-run 將使用預設 10 分鐘預覽，不會實際套用。[/yellow]"
            )
            console.print(f"[dim]{e}[/dim]")
            return {"auto_sync": False, "auto_sync_interval_minutes": 10}

        console.print(f"[yellow]{e}[/yellow]")
        raise typer.Exit(code=1)


@app.command()
def register(
    server: str = typer.Option(..., "--server", help="Sync server URL"),
    name: str = typer.Option(..., "--name", help="裝置名稱"),
    admin_secret: str = typer.Option(..., "--admin-secret", help="Admin secret"),
) -> None:
    """向 sync server 註冊本裝置。"""
    config: dict[str, Any] = {"server_url": server}
    result = _api_request_or_exit(
        config,
        "POST",
        "/api/auth/register",
        body={"name": name},
        extra_headers={"X-Admin-Secret": admin_secret},
    )
    config.update(
        {
            "api_key": result["api_key"],
            "device_name": name,
            "device_id": result["device_id"],
            "last_push_epoch": 0,
            "last_pull_epoch": 0,
            "auto_sync": False,
            "auto_sync_interval_minutes": 10,
        }
    )
    save_server_config(config)
    if result.get("rotated"):
        console.print(
            f"[bold green]重新註冊成功[/bold green] device_id={result['device_id']}（已更新 API key）"
        )
    else:
        console.print(
            f"[bold green]註冊成功[/bold green] device_id={result['device_id']}"
        )


@app.command()
def push() -> None:
    """推送本地 claude-mem 新資料到 sync server。"""
    config = _load_server_config_or_exit()
    last_epoch = config.get("last_push_epoch", 0)

    sessions = query_local_db(
        "SELECT * FROM sdk_sessions WHERE started_at_epoch > ?", (last_epoch,)
    )
    observations = query_local_db(
        "SELECT * FROM observations WHERE created_at_epoch > ?", (last_epoch,)
    )

    # 補齊 observations 引用但不在本次 push 範圍內的 sessions（避免 FK 違規）
    pushed_session_ids = {
        s["memory_session_id"] for s in sessions if s.get("memory_session_id")
    }
    missing_session_ids = {
        o["memory_session_id"]
        for o in observations
        if o.get("memory_session_id")
        and o["memory_session_id"] not in pushed_session_ids
    }
    if missing_session_ids:
        placeholders = ",".join("?" for _ in missing_session_ids)
        dep_sessions = query_local_db(
            f"SELECT * FROM sdk_sessions WHERE memory_session_id IN ({placeholders})",
            tuple(missing_session_ids),
        )
        sessions.extend(dep_sessions)

    raw_summaries = query_local_db(
        "SELECT * FROM session_summaries WHERE created_at_epoch > ?", (last_epoch,)
    )
    summaries, skipped_summaries = _normalize_summaries_for_push(raw_summaries)
    prompts = query_local_db(
        "SELECT * FROM user_prompts WHERE created_at_epoch > ?", (last_epoch,)
    )

    pulled_hashes = load_pulled_hashes()
    for obs in observations:
        obs["sync_content_hash"] = compute_content_hash(obs)

    observations_before_dedup = len(observations)
    observations = [
        o for o in observations if o["sync_content_hash"] not in pulled_hashes
    ]
    pulled_excluded = observations_before_dedup - len(observations)

    preflight_skipped = 0
    if observations:
        observation_hashes = [o["sync_content_hash"] for o in observations]
        try:
            missing_hashes = set(push_preflight(config, observation_hashes))
            before_preflight = len(observations)
            observations = [
                o for o in observations if o["sync_content_hash"] in missing_hashes
            ]
            preflight_skipped = before_preflight - len(observations)
        except RuntimeError:
            console.print(
                "[yellow]Preflight 不可用，改為全量推送 observations[/yellow]"
            )

    total = len(sessions) + len(observations) + len(summaries) + len(prompts)
    if total == 0:
        dedup_msg = ""
        if pulled_excluded > 0 or preflight_skipped > 0:
            dedup_msg = f"（去重排除：{pulled_excluded} pulled + {preflight_skipped} preflight）"
        if skipped_summaries > 0:
            console.print(
                f"[yellow]無可推送資料{dedup_msg}"
                f"（已略過 {skipped_summaries} 筆 summaries，缺少 session_id）[/yellow]"
            )
        else:
            console.print(f"[green]無新資料需要推送{dedup_msg}[/green]")
        return

    console.print(
        f"[cyan]推送中：{len(sessions)} sessions, {len(observations)} observations, "
        f"{len(summaries)} summaries, {len(prompts)} prompts[/cyan]"
    )
    if pulled_excluded > 0 or preflight_skipped > 0:
        console.print(
            f"[dim]去重排除：{pulled_excluded} pulled + {preflight_skipped} preflight[/dim]"
        )
    if skipped_summaries > 0:
        console.print(
            f"[yellow]略過 {skipped_summaries} 筆 summaries（缺少 session_id）[/yellow]"
        )

    result = _api_request_or_exit(
        config,
        "POST",
        "/api/sync/push",
        body={
            "sessions": sessions,
            "observations": observations,
            "summaries": summaries,
            "prompts": prompts,
        },
    )

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
def pull(
    reindex: bool = typer.Option(
        False,
        "--reindex",
        help="拉取完成後重建搜尋索引",
    ),
    cleanup: bool = typer.Option(
        False,
        "--cleanup",
        help="拉取完成後清理本地重複 observations",
    ),
) -> None:
    """從 sync server 拉取其他裝置的新資料。"""
    config = _load_server_config_or_exit()
    last_epoch = config.get("last_pull_epoch", 0)

    all_data: dict[str, list] = {
        "sessions": [],
        "observations": [],
        "summaries": [],
        "prompts": [],
    }
    since = last_epoch
    server_epoch = since

    while True:
        result = _api_request_or_exit(
            config,
            "GET",
            f"/api/sync/pull?since={since}&limit=500",
        )
        for key in all_data:
            all_data[key].extend(result.get(key, []))
        server_epoch = result.get("server_epoch", server_epoch)
        if not result.get("has_more"):
            break
        since = result.get("next_since", since)

    fetched_total = sum(len(v) for v in all_data.values())

    local_obs = query_local_db(
        "SELECT title, narrative, facts, project, type FROM observations"
    )
    local_hashes = {compute_content_hash(o) for o in local_obs}

    observations_before_dedup = len(all_data["observations"])
    filtered_observations: list[dict[str, Any]] = []
    for obs in all_data["observations"]:
        sync_hash = obs.get("sync_content_hash")
        if not sync_hash:
            sync_hash = compute_content_hash(obs)
            obs["sync_content_hash"] = sync_hash

        if sync_hash in local_hashes:
            continue

        local_hashes.add(sync_hash)
        filtered_observations.append(obs)

    hash_excluded = observations_before_dedup - len(filtered_observations)
    all_data["observations"] = filtered_observations

    total = sum(len(v) for v in all_data.values())
    if total == 0:
        if fetched_total > 0:
            config["last_pull_epoch"] = server_epoch
            save_server_config(config)

        if hash_excluded > 0:
            console.print(
                f"[green]無新資料需要拉取[/green] "
                f"[dim]（hash 去重排除 {hash_excluded} observations）[/dim]"
            )
        else:
            console.print("[green]無新資料需要拉取[/green]")
        return

    console.print(
        f"[cyan]拉取到：{len(all_data['sessions'])} sessions, "
        f"{len(all_data['observations'])} observations, "
        f"{len(all_data['summaries'])} summaries, "
        f"{len(all_data['prompts'])} prompts[/cyan]"
    )
    if hash_excluded > 0:
        console.print(f"[dim]hash 去重排除 {hash_excluded} observations[/dim]")

    # 匯入到本地 claude-mem（優先 HTTP API，fallback 直接寫 SQLite）
    import_payload = {
        "sessions": all_data["sessions"],
        "summaries": all_data["summaries"],
        "observations": all_data["observations"],
        "prompts": all_data["prompts"],
    }

    import_result: dict[str, Any] = {}
    import_method = "api"

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
            "[yellow]claude-mem worker 未啟動，改用直接寫入 SQLite...[/yellow]"
        )
        import_method = "sqlite"
        try:
            import_result = import_to_local_db(import_payload)
        except FileNotFoundError as e:
            console.print(f"[bold red]{e}[/bold red]")
            raise typer.Exit(code=1)

    config["last_pull_epoch"] = server_epoch
    save_server_config(config)

    stats = import_result.get("stats", {})
    method_label = "SQLite" if import_method == "sqlite" else "API"
    console.print(
        f"[bold green]Pull 完成[/bold green] ({method_label}) "
        f"imported: {stats.get('sessionsImported', 0)}s "
        f"{stats.get('observationsImported', 0)}o "
        f"{stats.get('summariesImported', 0)}sm "
        f"{stats.get('promptsImported', 0)}p | "
        f"skipped: {stats.get('sessionsSkipped', 0)}s "
        f"{stats.get('observationsSkipped', 0)}o "
        f"{stats.get('summariesSkipped', 0)}sm "
        f"{stats.get('promptsSkipped', 0)}p"
    )

    # 匯入成功後才記錄 pulled-hashes（避免失敗時誤記）
    append_pulled_hashes(
        [
            o["sync_content_hash"]
            for o in all_data["observations"]
            if o.get("sync_content_hash")
        ]
    )

    # 顯式 post-process：reindex / cleanup 不再隱含執行
    obs_imported = stats.get("observationsImported", 0)
    did_cleanup = False
    if reindex and obs_imported > 0 and worker_available():
        console.print("[cyan]正在同步 ChromaDB 搜尋索引...[/cyan]")
        try:
            reindex_stats = reindex_observations()
            synced = reindex_stats["synced"]
            errors = reindex_stats["errors"]
            if synced > 0 or errors > 0:
                console.print(
                    f"[green]索引同步完成[/green] synced={synced} errors={errors}"
                )
            # reindex 透過 worker /api/memory/save 會建立副本，自動清理
            if synced > 0:
                removed = _cleanup_duplicates()
                did_cleanup = True
                if removed > 0:
                    console.print(
                        f"[dim]自動清理 {removed} 筆重複 observations[/dim]"
                    )
        except (FileNotFoundError, RuntimeError):
            console.print(
                "[yellow]ChromaDB 索引同步失敗，稍後可執行 ai-dev mem reindex 補建[/yellow]"
            )
    elif reindex and obs_imported > 0:
        console.print(
            "[yellow]claude-mem worker 未啟動，略過 reindex；稍後可執行 ai-dev mem reindex[/yellow]"
        )

    if cleanup and not did_cleanup:
        removed = _cleanup_duplicates()
        if removed == 0:
            console.print("[dim]cleanup 完成，沒有重複 observations[/dim]")
        else:
            console.print(f"[dim]cleanup 完成，移除 {removed} 筆重複 observations[/dim]")


@app.command()
def status() -> None:
    """顯示 sync server 同步狀態。"""
    config = _load_server_config_or_exit()
    result = _api_request_or_exit(config, "GET", "/api/sync/status")

    local_obs = query_local_db(
        "SELECT id, title, narrative, facts, project, type FROM observations"
    )
    hash_counts: dict[str, int] = {}
    for obs in local_obs:
        content_hash = compute_content_hash(obs)
        hash_counts[content_hash] = hash_counts.get(content_hash, 0) + 1

    local_duplicates = sum(count - 1 for count in hash_counts.values() if count > 1)
    pulled_count = len(load_pulled_hashes())

    table = Table(title="claude-mem Sync Status")
    table.add_column("項目", style="cyan")
    table.add_column("值", style="green")
    table.add_row("Server sessions", str(result.get("sessions", 0)))
    table.add_row("Server observations", str(result.get("observations", 0)))
    table.add_row("Server summaries", str(result.get("summaries", 0)))
    table.add_row("Server prompts", str(result.get("prompts", 0)))
    table.add_row("Server devices", str(result.get("devices", 0)))
    table.add_row("───", "───")
    table.add_row("Local observations", str(len(local_obs)))
    table.add_row("Local duplicates", str(local_duplicates))
    table.add_row("Pulled hashes tracked", str(pulled_count))
    console.print(table)

    console.print(f"[dim]Last push epoch: {config.get('last_push_epoch', 0)}[/dim]")
    console.print(f"[dim]Last pull epoch: {config.get('last_pull_epoch', 0)}[/dim]")


def _cleanup_duplicates() -> int:
    """掃描並刪除本地 claude-mem 中的重複 observations，回傳移除數量。

    兩輪去重：
    1. content hash 分組（精確重複）
    2. text+project 分組（抓原始 vs worker 副本，因副本缺少 facts/type 導致 hash 不同）

    優先保留已被 ChromaDB 索引的記錄；若都未索引則保留最小 ID。
    """
    observations = query_local_db(
        "SELECT id, title, narrative, text, facts, project, type FROM observations ORDER BY id"
    )
    if not observations:
        return 0

    indexed_ids = get_indexed_observation_ids()

    # Phase 1: content hash 分組（精確重複）
    hash_groups: dict[str, list[int]] = {}
    for obs in observations:
        content_hash = compute_content_hash(obs)
        hash_groups.setdefault(content_hash, []).append(obs["id"])

    duplicate_ids: list[int] = []
    for ids in hash_groups.values():
        if len(ids) <= 1:
            continue
        indexed_in_group = [i for i in ids if i in indexed_ids]
        keep = indexed_in_group[0] if indexed_in_group else ids[0]
        duplicate_ids.extend(i for i in ids if i != keep)

    # Phase 2: text+project 分組（原始 vs worker 副本）
    # Worker save 建立的副本只有 text/title/project，缺少 facts/type，
    # 導致 content hash 不同。用主文字內容 + project 做二次分組。
    delete_set = set(duplicate_ids)
    obs_by_id = {obs["id"]: obs for obs in observations}
    text_groups: dict[tuple[str, str], list[int]] = {}
    for obs in observations:
        if obs["id"] in delete_set:
            continue
        text = (
            obs.get("narrative") or obs.get("text") or obs.get("title") or ""
        ).strip()
        if not text:
            continue
        key = (text, obs.get("project") or "")
        text_groups.setdefault(key, []).append(obs["id"])

    for ids in text_groups.values():
        if len(ids) <= 1:
            continue
        indexed_in_group = [i for i in ids if i in indexed_ids]
        keep = indexed_in_group[0] if indexed_in_group else ids[0]
        duplicate_ids.extend(i for i in ids if i != keep)

    if not duplicate_ids:
        return 0

    conn = sqlite3.connect(str(CLAUDE_MEM_DB_PATH))
    try:
        placeholders = ",".join("?" for _ in duplicate_ids)
        conn.execute(
            f"DELETE FROM observations WHERE id IN ({placeholders})",
            duplicate_ids,
        )
        conn.commit()
    finally:
        conn.close()

    return len(duplicate_ids)


@app.command()
def cleanup() -> None:
    """掃描並刪除本地 claude-mem 中的重複 observations。"""
    removed = _cleanup_duplicates()
    if removed == 0:
        console.print("[green]無重複 observations[/green]")
    else:
        console.print(
            f"[bold green]Cleanup 完成[/bold green] 移除 {removed} 筆重複"
        )


@app.command()
def reindex() -> None:
    """重建 ChromaDB 搜尋索引（修復 pull 匯入後搜尋不到的問題）。"""
    if not worker_available():
        console.print(
            "[bold red]claude-mem worker 未啟動，無法重建索引[/bold red]\n"
            "[yellow]請先啟動 Claude Code 讓 worker 自動啟動後再試[/yellow]"
        )
        raise typer.Exit(code=1)

    console.print("[cyan]正在掃描缺失的 ChromaDB 索引...[/cyan]")
    try:
        stats = reindex_observations()
    except FileNotFoundError as e:
        console.print(f"[bold red]{e}[/bold red]")
        raise typer.Exit(code=1)

    if stats["missing"] == 0:
        console.print(
            f"[green]索引已完整[/green]（共 {stats['total']} 筆 observations）"
        )
        return

    console.print(
        f"[bold green]Reindex 完成[/bold green] "
        f"synced={stats['synced']} errors={stats['errors']} "
        f"（共 {stats['total']} 筆，原缺 {stats['missing']} 筆）"
    )
    if stats["errors"] > 0:
        console.print(
            "[yellow]部分 observations 索引失敗，請確認 worker 正常運作後重試[/yellow]"
        )

    # reindex 透過 worker /api/memory/save 會建立副本，自動清理
    removed = _cleanup_duplicates()
    if removed > 0:
        console.print(
            f"[dim]自動清理 {removed} 筆重複 observations[/dim]"
        )


# ---------------------------------------------------------------------------
# auto sync scheduling (launchd / cron)
# ---------------------------------------------------------------------------

LAUNCHD_LABEL = "com.ai-dev.mem-sync"
LAUNCHD_PLIST_PATH = (
    Path("~/Library/LaunchAgents").expanduser() / f"{LAUNCHD_LABEL}.plist"
)
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
    subprocess.run(
        ["launchctl", "unload", str(LAUNCHD_PLIST_PATH)],
        capture_output=True,
        check=False,
    )
    subprocess.run(
        ["launchctl", "load", str(LAUNCHD_PLIST_PATH)], capture_output=True, check=False
    )


def _remove_launchd() -> None:
    subprocess.run(
        ["launchctl", "unload", str(LAUNCHD_PLIST_PATH)],
        capture_output=True,
        check=False,
    )
    LAUNCHD_PLIST_PATH.unlink(missing_ok=True)


def _install_cron(interval_minutes: int) -> None:
    ai_dev = _find_ai_dev()
    job = f"*/{interval_minutes} * * * * {ai_dev} mem push && {ai_dev} mem pull {CRON_MARKER}"
    result = subprocess.run(
        ["crontab", "-l"], capture_output=True, text=True, check=False
    )
    existing = result.stdout if result.returncode == 0 else ""
    lines = [l for l in existing.splitlines() if CRON_MARKER not in l]
    lines.append(job)
    subprocess.run(
        ["crontab", "-"], input="\n".join(lines) + "\n", text=True, check=True
    )


def _remove_cron() -> None:
    result = subprocess.run(
        ["crontab", "-l"], capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        return
    lines = [l for l in result.stdout.splitlines() if CRON_MARKER not in l]
    subprocess.run(
        ["crontab", "-"], input="\n".join(lines) + "\n", text=True, check=True
    )


@app.command()
def auto(
    enable: bool = typer.Option(None, "--on/--off", help="啟用或停用自動同步"),
    dry_run: bool = typer.Option(False, "--dry-run", help="預覽排程變更但不實際套用"),
) -> None:
    """切換 claude-mem 自動同步排程。"""
    config = _load_server_config_or_exit(
        allow_missing_preview=dry_run and enable is not None
    )

    if enable is None:
        status_text = "啟用" if config.get("auto_sync") else "停用"
        interval = config.get("auto_sync_interval_minutes", 10)
        console.print(f"自動同步：[bold]{status_text}[/bold]（每 {interval} 分鐘）")
        return

    system = platform.system()
    interval = config.get("auto_sync_interval_minutes", 10)
    scheduler_name = "launchd" if system == "Darwin" else "cron"

    if dry_run:
        action = "install" if enable else "remove"
        console.print(
            f"[yellow]Dry-run: would {action} {scheduler_name} scheduler for mem sync (every {interval} minutes)[/yellow]"
        )
        return

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
