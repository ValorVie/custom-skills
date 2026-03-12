# wl_parser/formatters.py
"""Format work log report JSON into Markdown variants."""

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime

WEEKDAYS = ["週一", "週二", "週三", "週四", "週五", "週六", "週日"]


def _format_duration(minutes: int) -> str:
    """Format minutes as '2.5 小時' or '30 分鐘'."""
    if minutes >= 60:
        hours = minutes / 60
        return f"{hours:.1f} 小時"
    return f"{minutes} 分鐘"


def _format_tokens(n: int) -> str:
    """Format token count: 1234 -> '1.2K', 999 -> '999'."""
    if n >= 1000:
        return f"{n / 1000:.1f}K"
    return str(n)


def _short_project(path: str) -> str:
    """Get last path component as project short name."""
    if not path:
        return "unknown"
    return path.rstrip("/").split("/")[-1] if "/" in path else path


def _extract_date_str(period: dict) -> str:
    """Extract formatted date string with weekday."""
    start_str = period.get("start", "")
    end_str = period.get("end", "")
    try:
        dt = datetime.fromisoformat(start_str)
        end_dt = datetime.fromisoformat(end_str)
        weekday = WEEKDAYS[dt.weekday()]
        if dt.date() == end_dt.date():
            return f"{dt.strftime('%Y-%m-%d')}（{weekday}）"
        return f"{dt.strftime('%Y-%m-%d')} — {end_dt.strftime('%Y-%m-%d')}"
    except (ValueError, TypeError):
        return start_str[:10] if start_str else "unknown date"


def _filter_meaningful_sessions(sessions: list) -> list:
    """Filter out sessions with 0 duration (no real work)."""
    return [s for s in sessions if s.get("duration_minutes", 0) > 0]


def _group_sessions_by_date(sessions: list) -> list[tuple[str, list]]:
    """Group sessions by date from start timestamp.

    Returns sorted list of (YYYY-MM-DD, sessions) tuples.
    Note: Spec defines tz_name parameter, but it's unnecessary because
    session start timestamps already contain timezone offset.
    """
    groups: dict[str, list] = defaultdict(list)
    for s in sessions:
        start = s.get("start", "")
        if start:
            try:
                dt = datetime.fromisoformat(start)
                date_key = dt.strftime("%Y-%m-%d")
                groups[date_key].append(s)
            except (ValueError, TypeError):
                pass
    return sorted(groups.items())


def _format_daily_summary(sessions: list) -> list[str]:
    """Generate daily summary table lines. Returns [] if fewer than 2 distinct days."""
    grouped = _group_sessions_by_date(sessions)
    if len(grouped) < 2:
        return []

    lines = ["### 每日摘要", "| 日期 | Sessions | 時間 | Commits |", "|------|----------|------|---------|"]
    for date_str, day_sessions in grouped:
        count = len(day_sessions)
        total_min = sum(s.get("duration_minutes", 0) for s in day_sessions)
        total_commits = sum(len(s.get("commits", [])) for s in day_sessions)
        hours = total_min / 60
        display_date = date_str[5:]  # MM-DD from YYYY-MM-DD
        lines.append(f"| {display_date} | {count} | {hours:.1f}h | {total_commits} |")
    lines.append("")
    return lines


def _format_commit_details(projects: dict) -> list[str]:
    """Format git commits grouped by project."""
    lines = ["### Commit 明細", ""]
    has_commits = False
    for path in sorted(projects.keys()):
        proj = projects[path]
        commits = proj.get("git_commits", [])
        if not commits:
            continue
        has_commits = True
        lines.append(f"#### {proj['short_name']}")
        for c in commits:
            lines.append(f"- {c['hash']} {c['message']}")
        lines.append("")
    if not has_commits:
        return []
    return lines


def format_terminal(report: dict) -> str:
    """Generate concise terminal summary (v2).
    Only outputs: title + stats, daily summary table (multi-day).
    AI summary and detail blocks are handled separately.
    """
    lines = []
    summary = report.get("summary", {})
    period = report.get("period", {})
    projects = report.get("projects", {})

    date_str = _extract_date_str(period)
    duration = _format_duration(summary.get("total_duration_minutes", 0))
    sessions_count = summary.get("active_sessions", 0)
    project_count = summary.get("project_count", len(projects))
    total_commits = summary.get("total_commits", 0)

    lines.append(f"## 工作日誌 {date_str}")
    lines.append(
        f"**工作時間：** {duration}，{sessions_count} 個 session，"
        f"{project_count} 個專案，{total_commits} 個 commits"
    )
    lines.append("")

    meaningful = _filter_meaningful_sessions(report.get("sessions", []))
    daily_lines = _format_daily_summary(meaningful)
    if daily_lines:
        lines.extend(daily_lines)

    return "\n".join(lines)


def format_full_report(report: dict) -> str:
    """Generate full Markdown report with all mechanical blocks (v2).
    Blocks: stats, daily summary, token, tools, commit details, session details, codex.
    AI summary is NOT included — added by Claude Code.
    """
    lines = []
    summary = report.get("summary", {})
    period = report.get("period", {})
    projects = report.get("projects", {})

    date_str = _extract_date_str(period)
    duration = _format_duration(summary.get("total_duration_minutes", 0))
    sessions_count = summary.get("active_sessions", 0)
    project_count = summary.get("project_count", len(projects))
    total_commits = summary.get("total_commits", 0)

    lines.append(f"## 工作日誌 {date_str}")
    lines.append("")
    lines.append("### 工時統計")
    lines.append(
        f"**工作時間：** {duration}，{sessions_count} 個 session，"
        f"{project_count} 個專案，{total_commits} 個 commits"
    )
    lines.append("")

    meaningful = _filter_meaningful_sessions(report.get("sessions", []))
    daily_lines = _format_daily_summary(meaningful)
    if daily_lines:
        lines.extend(daily_lines)

    # Token summary
    ts = report.get("token_summary", {})
    if ts:
        lines.append("### Token 消耗")
        parts = [
            f"輸入: {_format_tokens(ts.get('total_input', 0))}",
            f"輸出: {_format_tokens(ts.get('total_output', 0))}",
            f"Cache 建立: {_format_tokens(ts.get('total_cache_creation', 0))}",
            f"Cache 讀取: {_format_tokens(ts.get('total_cache_read', 0))}",
        ]
        lines.append(" | ".join(parts))
        lines.append("")

    # Tool summary
    tool_summary = report.get("tool_summary", {})
    if tool_summary:
        lines.append("### 工具使用")
        consolidated: dict = {}
        for name, count in tool_summary.items():
            if name.startswith("mcp__"):
                tool_parts = name.split("__")
                server = tool_parts[1].capitalize() if len(tool_parts) > 1 else "MCP"
                key = f"MCP:{server}"
                consolidated[key] = consolidated.get(key, 0) + count
            else:
                consolidated[name] = consolidated.get(name, 0) + count
        display = [f"{k}: {v}" for k, v in sorted(consolidated.items(), key=lambda x: -x[1])]
        lines.append(" | ".join(display))
        lines.append("")

    # Commit details
    commit_lines = _format_commit_details(projects)
    if commit_lines:
        lines.extend(commit_lines)

    # Session details
    lines.append("### Session 明細")
    lines.append("")
    for s in report.get("sessions", []):
        proj = _short_project(s.get("project", ""))
        status_icon = "V" if s.get("status") == "completed" else "..."
        dur = _format_duration(s.get("duration_minutes", 0))
        prompt = s.get("first_prompt") or "（無描述）"
        if len(prompt) > 200:
            prompt = prompt[:200] + "…"
        lines.append(f"#### [{status_icon}] {proj} — {prompt}")
        lines.append(f"**時間：** {s.get('start', '?')} → {s.get('end', '?')}（{dur}）")
        commits = s.get("commits", [])
        if commits:
            lines.append(f"**Commits：** {', '.join(commits)}")
        files = s.get("files_changed", [])
        if files:
            lines.append(f"**檔案變更：** {', '.join(files)}")
        tools = s.get("tools_used", {})
        if tools:
            t_parts = [f"{k}: {v}" for k, v in sorted(tools.items(), key=lambda x: -x[1])]
            lines.append(f"**工具：** {' | '.join(t_parts)}")
        lines.append("")

    codex = report.get("codex_sessions", [])
    if codex:
        lines.append("### Codex Sessions")
        lines.append("")
        for c in codex:
            lines.append(f"- {c.get('thread_name', '')} ({c.get('updated_at', '')})")
        lines.append("")

    return "\n".join(lines)


def format_obsidian(report: dict) -> str:
    """Generate Obsidian note with YAML frontmatter (v2).
    Note: This output does NOT include the AI summary section.
    The AI summary is injected externally by the SKILL.md Step 5 flow.
    """
    period = report.get("period", {})
    summary = report.get("summary", {})
    projects = report.get("projects", {})

    start_str = period.get("start", "")
    try:
        dt = datetime.fromisoformat(start_str)
        date_str = dt.strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        date_str = start_str[:10] if start_str else "unknown"

    project_names = [p["short_name"] for p in projects.values()]
    tags = ["work-log"] + project_names
    tags_str = ", ".join(tags)
    hours = summary.get("total_duration_minutes", 0) / 60

    frontmatter = f"""---
date: {date_str}
type: work-log
tags: [{tags_str}]
total_hours: {hours:.1f}
sessions: {summary.get("active_sessions", 0)}
commits: {summary.get("total_commits", 0)}
---"""

    body = format_full_report(report)
    return f"{frontmatter}\n\n{body}"


def main(argv: list | None = None) -> None:
    """CLI entry point. Reads JSON from stdin, outputs formatted text to stdout."""
    parser = argparse.ArgumentParser(description="Format work log report")
    parser.add_argument("output_format", choices=["terminal", "full_report", "obsidian"])
    args = parser.parse_args(argv)

    report = json.load(sys.stdin)

    format_funcs = {
        "terminal": format_terminal,
        "full_report": format_full_report,
        "obsidian": format_obsidian,
    }
    print(format_funcs[args.output_format](report))


if __name__ == "__main__":
    main()
