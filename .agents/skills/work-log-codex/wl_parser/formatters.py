"""Format work-log report JSON into Markdown variants."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from collections import defaultdict
from datetime import datetime


WEEKDAYS = ["週一", "週二", "週三", "週四", "週五", "週六", "週日"]


def _format_duration(minutes: int) -> str:
    if minutes >= 60:
        return f"{minutes / 60:.1f} 小時"
    return f"{minutes} 分鐘"


def _format_tokens(n: int) -> str:
    if n >= 1000:
        return f"{n / 1000:.1f}K"
    return str(n)


def _short_project(path: str) -> str:
    if not path:
        return "unknown"
    return path.rstrip("/").split("/")[-1] if "/" in path else path


def _display_project(project: dict) -> str:
    return project.get("display_name") or project.get("short_name") or "unknown"


def _extract_date_str(period: dict) -> str:
    start_str = period.get("start", "")
    end_str = period.get("end", "")
    try:
        start_dt = datetime.fromisoformat(start_str)
        end_dt = datetime.fromisoformat(end_str)
        weekday = WEEKDAYS[start_dt.weekday()]
        if start_dt.date() == end_dt.date():
            return f"{start_dt.strftime('%Y-%m-%d')}（{weekday}）"
        return f"{start_dt.strftime('%Y-%m-%d')} — {end_dt.strftime('%Y-%m-%d')}"
    except (TypeError, ValueError):
        return start_str[:10] if start_str else "unknown date"


def _filter_meaningful_sessions(sessions: list) -> list:
    return [session for session in sessions if session.get("duration_minutes", 0) > 0]


def _group_sessions_by_date(sessions: list) -> list[tuple[str, list]]:
    groups: dict[str, list] = defaultdict(list)
    for session in sessions:
        start = session.get("start")
        if not start:
            continue
        try:
            dt = datetime.fromisoformat(start)
        except (TypeError, ValueError):
            continue
        groups[dt.strftime("%Y-%m-%d")].append(session)
    return sorted(groups.items())


def _format_daily_summary(sessions: list, daily_summary: list[dict] | None = None) -> list[str]:
    if daily_summary is not None:
        if len(daily_summary) < 2:
            return []
        lines = ["### 每日摘要", "| 日期 | Sessions | 時間 | Commits |", "|------|----------|------|---------|"]
        for row in daily_summary:
            display_date = str(row.get("date", ""))[5:]
            total_min = int(row.get("total_duration_minutes", 0) or 0)
            lines.append(
                f"| {display_date} | {row.get('session_count', 0)} | {total_min / 60:.1f}h | {row.get('total_commits', 0)} |"
            )
        lines.append("")
        return lines

    grouped = _group_sessions_by_date(sessions)
    if len(grouped) < 2:
        return []

    lines = ["### 每日摘要", "| 日期 | Sessions | 時間 | Commits |", "|------|----------|------|---------|"]
    for date_str, day_sessions in grouped:
        count = len(day_sessions)
        total_min = sum(session.get("duration_minutes", 0) for session in day_sessions)
        total_commits = sum(len(session.get("commits", [])) for session in day_sessions)
        display_date = date_str[5:]
        lines.append(f"| {display_date} | {count} | {total_min / 60:.1f}h | {total_commits} |")
    lines.append("")
    return lines


def _format_stats_section(summary: dict, projects: dict) -> list[str]:
    return [
        "### 工時統計",
        f"**工作時間：** {_format_duration(summary.get('total_duration_minutes', 0))}，"
        f"{summary.get('active_sessions', 0)} 個 session，"
        f"{summary.get('project_count', len(projects))} 個專案，"
        f"{summary.get('total_commits', 0)} 個 commits",
        "",
    ]


def _format_commit_details(projects: dict) -> list[str]:
    lines = ["### Commit 明細", ""]
    has_commits = False
    for path in sorted(projects.keys()):
        project = projects[path]
        commits = project.get("git_commits", [])
        if not commits:
            continue
        has_commits = True
        lines.append(f"#### {_display_project(project)}")
        for commit in commits:
            suffix = ""
            files = commit.get("files") or []
            if files:
                preview = ", ".join(files[:3])
                if len(files) > 3:
                    preview += ", ..."
                suffix = f" — {preview}"
            lines.append(f"- {commit['hash']} {commit['message']}{suffix}")
        lines.append("")
    if not has_commits:
        return []
    return lines


def _project_status_line(project: dict) -> str:
    commits = project.get("git_commits", [])
    if commits:
        return "已完成"
    if project.get("session_summaries") or project.get("session_hints"):
        return "研究 / 探索"
    return "活動紀錄有限"


def _looks_like_path(value: str) -> bool:
    text = str(value).strip()
    if not text or "\n" in text:
        return False
    if "Generated with" in text or "http" in text:
        return False
    if text.startswith("- ") or text.startswith("### "):
        return False
    if "/" in text:
        return True
    return bool(re.search(r"\.[A-Za-z0-9]{1,8}$", text))


def _project_representative_paths(project: dict) -> list[str]:
    paths: list[str] = []
    for commit in project.get("git_commits", []):
        for path in commit.get("files") or []:
            text = str(path).strip()
            if _looks_like_path(text) and text not in paths:
                paths.append(text)
    for path in project.get("files_touched") or []:
        text = str(path).strip()
        if _looks_like_path(text) and text not in paths:
            paths.append(text)
    return paths[:5]


def _project_evidence_lines(project: dict) -> list[str]:
    lines = [f"- 狀態：{_project_status_line(project)}"]

    commits = project.get("git_commits", [])
    if commits:
        commit_messages = [commit.get("message", "") for commit in commits[:5] if commit.get("message")]
        if commit_messages:
            lines.append(f"- Commit 證據：{'；'.join(commit_messages)}")
    else:
        summaries = project.get("session_summaries") or []
        hints = project.get("session_hints") or []
        fallback = summaries[:2] or hints[:2]
        if fallback:
            lines.append(f"- Session 補充：{'；'.join(fallback)}")
        else:
            lines.append("- Session 補充：本區段沒有明確 commit 證據，僅保留低信心活動紀錄")

    touched = _project_representative_paths(project)
    if touched:
        preview = ", ".join(touched[:5])
        lines.append(f"- 代表檔案：{preview}")

    duration = project.get("duration_minutes", 0)
    session_count = project.get("session_count", 0)
    lines.append(f"- 活動概況：{_format_duration(duration)}，{session_count} 個 session")
    return lines


def format_terminal(report: dict) -> str:
    lines = []
    summary = report.get("summary", {})
    period = report.get("period", {})
    projects = report.get("projects", {})

    lines.append(f"## 工作日誌 {_extract_date_str(period)}")
    lines.append(
        f"**工作時間：** {_format_duration(summary.get('total_duration_minutes', 0))}，"
        f"{summary.get('active_sessions', 0)} 個 session，"
        f"{summary.get('project_count', len(projects))} 個專案，"
        f"{summary.get('total_commits', 0)} 個 commits"
    )
    lines.append("")

    daily = _format_daily_summary(
        _filter_meaningful_sessions(report.get("sessions", [])),
        report.get("daily_summary"),
    )
    if daily:
        lines.extend(daily)

    return "\n".join(lines)


def format_report(report: dict, summary_markdown: str) -> str:
    lines = []
    summary = report.get("summary", {})
    period = report.get("period", {})
    projects = report.get("projects", {})

    lines.append(f"## 工作日誌 {_extract_date_str(period)}")
    lines.append("")
    lines.append(summary_markdown.strip())
    lines.append("")
    lines.extend(_format_stats_section(summary, projects))

    daily = _format_daily_summary(
        _filter_meaningful_sessions(report.get("sessions", [])),
        report.get("daily_summary"),
    )
    if daily:
        lines.extend(daily)

    return "\n".join(lines).rstrip() + "\n"


def format_appendix(report: dict) -> str:
    lines = []
    period = report.get("period", {})
    projects = report.get("projects", {})

    lines.append(f"## 工作日誌附件 {_extract_date_str(period)}")
    lines.append("")
    lines.append("### 專案證據附錄")
    lines.append("")

    ordered = sorted(
        projects.values(),
        key=lambda project: (
            -(1 if project.get("git_commits") else 0),
            -project.get("duration_minutes", 0),
            _display_project(project),
        ),
    )
    for project in ordered:
        lines.append(f"#### {_display_project(project)}")
        for entry in _project_evidence_lines(project):
            lines.append(entry)
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def format_debug(report: dict) -> str:
    lines = []
    summary = report.get("summary", {})
    period = report.get("period", {})
    projects = report.get("projects", {})

    lines.append(f"## 工作日誌偵錯 {_extract_date_str(period)}")
    lines.append("")
    lines.extend(_format_stats_section(summary, projects))

    daily = _format_daily_summary(
        _filter_meaningful_sessions(report.get("sessions", [])),
        report.get("daily_summary"),
    )
    if daily:
        lines.extend(daily)

    token_summary = report.get("token_summary", {})
    if any(token_summary.values()):
        lines.append("### Token 消耗")
        lines.append(
            " | ".join(
                [
                    f"輸入: {_format_tokens(token_summary.get('total_input', 0))}",
                    f"輸出: {_format_tokens(token_summary.get('total_output', 0))}",
                    f"Cache 建立: {_format_tokens(token_summary.get('total_cache_creation', 0))}",
                    f"Cache 讀取: {_format_tokens(token_summary.get('total_cache_read', 0))}",
                ]
            )
        )
        lines.append("")

    tool_summary = report.get("tool_summary", {})
    if tool_summary:
        lines.append("### 工具使用")
        display = [f"{name}: {count}" for name, count in sorted(tool_summary.items(), key=lambda item: -item[1])]
        lines.append(" | ".join(display))
        lines.append("")

    commit_lines = _format_commit_details(projects)
    if commit_lines:
        lines.extend(commit_lines)

    lines.append("### Session 明細")
    lines.append("")
    for session in report.get("sessions", []):
        proj = _short_project(session.get("project", ""))
        status_icon = "V" if session.get("status") == "completed" else "..."
        prompt = session.get("first_prompt") or "（無描述）"
        if len(prompt) > 200:
            prompt = prompt[:200] + "…"
        lines.append(f"#### [{status_icon}] {proj} — {prompt}")
        lines.append(
            f"**時間：** {session.get('start', '?')} → {session.get('end', '?')}（{_format_duration(session.get('duration_minutes', 0))}）"
        )
        commits = session.get("commits", [])
        if commits:
            lines.append(f"**Commits：** {', '.join(commits)}")
        hints = session.get("session_hints", [])
        if hints:
            lines.append(f"**Hints：** {' | '.join(hints[:3])}")
        tools = session.get("tools_used", {})
        if tools:
            parts = [f"{name}: {count}" for name, count in sorted(tools.items(), key=lambda item: -item[1])]
            lines.append(f"**工具：** {' | '.join(parts)}")
        lines.append("")

    codex_sessions = report.get("codex_sessions", [])
    if codex_sessions:
        lines.append("### Codex Sessions")
        lines.append("")
        for session in codex_sessions:
            lines.append(f"- {session.get('thread_name', '')} ({session.get('updated_at', '')})")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def format_full_report(report: dict) -> str:
    return format_debug(report)


def format_obsidian(report: dict, summary_markdown: str | None = None) -> str:
    period = report.get("period", {})
    summary = report.get("summary", {})
    projects = report.get("projects", {})

    start_str = period.get("start", "")
    try:
        dt = datetime.fromisoformat(start_str)
        date_str = dt.strftime("%Y-%m-%d")
    except (TypeError, ValueError):
        date_str = start_str[:10] if start_str else "unknown"

    project_names = [project.get("display_name") or project["short_name"] for project in projects.values()]
    tags = ["work-log", *project_names]
    frontmatter = f"""---
date: {date_str}
type: work-log
tags: [{", ".join(tags)}]
total_hours: {summary.get("total_duration_minutes", 0) / 60:.1f}
sessions: {summary.get("active_sessions", 0)}
commits: {summary.get("total_commits", 0)}
---"""
    body = format_report(report, summary_markdown or "")
    return f"{frontmatter}\n\n{body}"


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Format work log report")
    parser.add_argument("output_format", choices=["terminal", "report", "appendix", "debug", "full_report", "obsidian"])
    parser.add_argument("--summary-file", default=None)
    args = parser.parse_args(argv)
    report = json.load(sys.stdin)
    summary_markdown = None
    if args.summary_file:
        summary_markdown = Path(args.summary_file).read_text(encoding="utf-8")
    formatters = {
        "terminal": format_terminal,
        "report": lambda payload: format_report(payload, summary_markdown or ""),
        "appendix": format_appendix,
        "debug": format_debug,
        "full_report": format_full_report,
        "obsidian": lambda payload: format_obsidian(payload, summary_markdown),
    }
    print(formatters[args.output_format](report))


if __name__ == "__main__":
    main()
