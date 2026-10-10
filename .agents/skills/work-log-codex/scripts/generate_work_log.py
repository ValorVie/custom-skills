from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
import re
import sys


SKILL_ROOT = Path(__file__).resolve().parents[1]
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))

from wl_parser.formatters import format_appendix, format_debug, format_obsidian, format_report, format_terminal  # noqa: E402
from wl_parser.work_log_parser import build_report, parse_time_shortcut  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="work-log-codex")
    parser.add_argument("--range", dest="time_range", default="today")
    parser.add_argument("--end-date", default=None)
    parser.add_argument("--timezone", default="Asia/Taipei")
    parser.add_argument("--project", default=None)
    parser.add_argument("--claude-home", default=str(Path.home() / ".claude"))
    parser.add_argument("--codex-home", default=str(Path.home() / ".codex"))
    parser.add_argument(
        "--output-mode",
        choices=("report-only", "write-only", "report-and-write", "terminal-only"),
        default="report-and-write",
    )
    parser.add_argument("--output-root", default="docs/work-logs")
    parser.add_argument("--summary-file", default=None)
    parser.add_argument("--emit-json", default=None)
    parser.add_argument("--emit-project-dir", default=None)
    parser.add_argument(
        "--mode",
        choices=("report", "report+appendix", "debug", "all"),
        default="report+appendix",
    )
    parser.add_argument(
        "--format",
        dest="report_format",
        choices=("full_report", "obsidian"),
        default="full_report",
    )
    return parser


def _is_multi_day(report: dict) -> bool:
    period = report.get("period", {})
    start = period.get("start", "")
    end = period.get("end", "")
    return start[:10] != end[:10]


def _build_base_filename(report: dict) -> str:
    period = report.get("period", {})
    start = period.get("start", "")[:10]
    end = period.get("end", "")[:10]
    if not start:
        start = datetime.now().strftime("%Y-%m-%d")
    filename = f"{start}.md"
    if end and end != start:
        filename = f"{start}--{end}.md"
    return filename


def _build_report_path(report: dict, root: Path) -> Path:
    return root / _build_base_filename(report)


def _build_appendix_path(report: dict, root: Path) -> Path:
    base = _build_base_filename(report)
    return root / base.replace(".md", ".appendix.md")


def _build_debug_path(report: dict, root: Path) -> Path:
    base = _build_base_filename(report)
    return root / base.replace(".md", ".debug.md")


def _limit_context(value: str, limit: int = 300) -> str:
    normalized = " ".join(value.split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 1] + "…"


def _fallback_project_tasks(project_path: str, project: dict) -> list[dict[str, str]]:
    commits = project.get("git_commits", [])
    hints = project.get("session_summaries") or project.get("session_hints", [])
    if commits:
        tasks: list[dict[str, str]] = []
        for commit in _representative_commits(commits):
            message = _clean_commit_message(commit.get("message", ""))
            if not message:
                continue
            files = [str(path) for path in (commit.get("files") or [])[:3]]
            files_text = "、".join(files) if files else "未列代表檔案"
            commit_hash = commit.get("full_hash") or commit.get("hash") or "unknown"
            tasks.append(
                {
                    "one_line": message,
                    "context": _limit_context(
                        f"此項以 Git commit 為完成證據，代表檔案為 {files_text}。"
                        "工作日誌只確認版本庫中的交付；部署、執行期與外部狀態仍需另行驗證。"
                    ),
                    "source": f"{project_path}@{commit_hash}",
                }
            )
        return tasks

    if hints:
        cleaned_hints = _clean_research_hints(hints)
        if cleaned_hints:
            return [
                {
                    "one_line": hint,
                    "context": _limit_context(
                        "此項只有工作階段摘要，沒有 Git commit 可證明已交付。"
                        "因此保留為研究、規劃或進行中脈絡，不宣稱完成。"
                    ),
                    "source": "工作階段摘要（無 Git commit）",
                }
                for hint in cleaned_hints[:2]
            ]

    return [
        {
            "one_line": f"研究／探索活動（{project.get('duration_minutes', 0)} 分鐘）",
            "context": "現有資料不足以辨識更具體主題，因此只保留活動紀錄，不宣稱完成或交付。",
            "source": "工作階段統計（無 Git commit）",
        }
    ]


def build_fallback_summary(report: dict) -> str:
    summary = report.get("summary", {})
    projects = report.get("projects", {})
    ordered = sorted(
        projects.items(),
        key=lambda item: (
            -item[1].get("duration_minutes", 0),
            item[1].get("display_name") or item[1].get("short_name", ""),
        ),
    )
    names = [
        project.get("display_name") or project.get("short_name", "unknown")
        for _path, project in ordered[:4]
    ]
    names_text = "、".join(names) if names else "各專案"
    total_hours = summary.get("total_duration_minutes", 0) / 60

    lines = [
        "### 當日總結",
        "",
        f"這段期間主要投入 {names_text} 等專案，共累積 {total_hours:.1f} 小時、{summary.get('total_commits', 0)} 筆 commits，以下按專案整理主要工作脈絡。",
        "",
        "### 逐專案摘要",
        "",
    ]

    for project_path, project in ordered:
        lines.append(
            f"#### {project.get('display_name') or project.get('short_name', 'unknown')}"
        )
        for task in _fallback_project_tasks(project_path, project):
            lines.append(f"- **一行重點：** {task['one_line']}")
            lines.append(f"  - **重點脈絡：** {task['context']}")
            lines.append(f"  - **來源：** {task['source']}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _clean_commit_message(message: str) -> str:
    text = " ".join(str(message).split())
    text = re.sub(r"Generated with .*", "", text, flags=re.IGNORECASE).strip(" -;|")
    return text


def _representative_commit_messages(commits: list[dict]) -> list[str]:
    return [
        message
        for commit in _representative_commits(commits)
        if (message := _clean_commit_message(commit.get("message", "")))
    ]


def _representative_commits(commits: list[dict]) -> list[dict]:
    if not commits:
        return []

    if len(commits) <= 4:
        indices = list(range(len(commits)))
    else:
        last_index = len(commits) - 1
        indices = sorted({0, last_index // 3, (2 * last_index) // 3, last_index})

    selected: list[dict] = []
    seen: set[str] = set()
    for index in indices:
        commit = commits[index]
        message = _clean_commit_message(commit.get("message", ""))
        if not message or message in seen:
            continue
        seen.add(message)
        selected.append(commit)
    return selected[:4]


def _clean_hint_text(text: str) -> str | None:
    cleaned = " ".join(str(text).split())
    if not cleaned:
        return None

    disallowed_patterns = [
        r"^Help turn ideas into fully formed designs",
        r"^I'm using ",
        r"^Paste your URL",
        r"^Asks ",
        r"^@/Users/",
        r"^### ",
        r"^```",
    ]
    if any(re.search(pattern, cleaned, flags=re.IGNORECASE) for pattern in disallowed_patterns):
        return None
    if "Generated with" in cleaned:
        return None
    if len(cleaned) > 160:
        return None
    return cleaned


def _clean_research_hints(hints: list[str]) -> list[str]:
    cleaned_hints: list[str] = []
    for hint in hints:
        if isinstance(hint, dict):
            hint = hint.get("first_prompt") or hint.get("closing_note") or ""
        cleaned = _clean_hint_text(str(hint))
        if cleaned and cleaned not in cleaned_hints:
            cleaned_hints.append(cleaned)
    return cleaned_hints


def _read_summary(path_text: str | None, report: dict) -> str:
    if path_text:
        path = Path(path_text).expanduser()
        if path.exists():
            return path.read_text(encoding="utf-8")
    return build_fallback_summary(report)


def _selected_documents(mode: str, report_markdown: str, appendix_markdown: str, debug_markdown: str) -> list[tuple[str, str]]:
    if mode == "report":
        return [("report", report_markdown)]
    if mode == "report+appendix":
        return [("report", report_markdown), ("appendix", appendix_markdown)]
    if mode == "debug":
        return [("debug", debug_markdown)]
    return [
        ("report", report_markdown),
        ("appendix", appendix_markdown),
        ("debug", debug_markdown),
    ]


def _output_path_for(kind: str, report: dict, root: Path) -> Path:
    if kind == "report":
        return _build_report_path(report, root)
    if kind == "appendix":
        return _build_appendix_path(report, root)
    if kind == "debug":
        return _build_debug_path(report, root)
    raise ValueError(f"Unknown output kind: {kind}")


def main() -> int:
    args = build_parser().parse_args()
    start, end = parse_time_shortcut(args.time_range, args.timezone, args.end_date)
    report = build_report(
        start=start,
        end=end,
        timezone_name=args.timezone,
        claude_home=Path(args.claude_home).expanduser(),
        codex_home=Path(args.codex_home).expanduser(),
        project_filter=args.project,
        progress=lambda message: print(message, file=sys.stderr, flush=True),
    )

    if args.emit_json:
        json_path = Path(args.emit_json).expanduser()
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if args.emit_project_dir:
        # Reuse parser CLI contract without shelling out.
        from wl_parser.work_log_parser import _emit_project_bundles  # noqa: PLC0415

        _emit_project_bundles(report, Path(args.emit_project_dir).expanduser())

    summary_markdown = _read_summary(args.summary_file, report)

    if args.report_format == "obsidian":
        report_markdown = format_obsidian(report, summary_markdown)
    else:
        report_markdown = format_report(report, summary_markdown)
    appendix_markdown = format_appendix(report)
    debug_markdown = format_debug(report)
    terminal = format_terminal(report)
    selected_documents = _selected_documents(args.mode, report_markdown, appendix_markdown, debug_markdown)
    primary_markdown = selected_documents[0][1]

    if args.output_mode in {"report-only", "report-and-write", "terminal-only"}:
        print(terminal if args.output_mode == "terminal-only" else primary_markdown, end="")

    if args.output_mode in {"write-only", "report-and-write"}:
        output_root = Path(args.output_root).expanduser()
        written_paths: list[Path] = []
        for kind, content in selected_documents:
            output_path = _output_path_for(kind, report, output_root)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(content, encoding="utf-8")
            written_paths.append(output_path)
        if args.output_mode == "write-only":
            print("\n".join(str(path) for path in written_paths))
        else:
            print("")
            for path in written_paths:
                print(f"已寫入：{path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
