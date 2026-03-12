from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re
from typing import Any


MANUAL_NOTES_HEADING = "## Manual Notes"
SUMMARY_SKIP_PATTERNS = (
    re.compile(r"^<subagent_notification>", re.IGNORECASE),
    re.compile(r"\bI'?m using the\b", re.IGNORECASE),
    re.compile(r"我已讀完"),
    re.compile(r"我已讀取"),
    re.compile(r"^請做 review", re.IGNORECASE),
    re.compile(r"^請 review", re.IGNORECASE),
    re.compile(r"工作樹目前乾淨"),
    re.compile(r"推送完成"),
)

SUMMARY_SCORE_RULES: dict[str, dict[str, tuple[re.Pattern[str], ...]]] = {
    "completed": {
        "positive": (
            re.compile(r"commit", re.IGNORECASE),
            re.compile(r"提交", re.IGNORECASE),
            re.compile(r"已完成", re.IGNORECASE),
            re.compile(r"完成", re.IGNORECASE),
            re.compile(r"修復", re.IGNORECASE),
            re.compile(r"修正", re.IGNORECASE),
            re.compile(r"新增", re.IGNORECASE),
            re.compile(r"建立", re.IGNORECASE),
            re.compile(r"更新", re.IGNORECASE),
            re.compile(r"補上", re.IGNORECASE),
            re.compile(r"通過", re.IGNORECASE),
            re.compile(r"全綠", re.IGNORECASE),
            re.compile(r"排除", re.IGNORECASE),
            re.compile(r"同步", re.IGNORECASE),
            re.compile(r"archive", re.IGNORECASE),
            re.compile(r"封存", re.IGNORECASE),
            re.compile(r"安裝", re.IGNORECASE),
        ),
        "negative": (
            re.compile(r"^(我正在|我現在|我在|我會|我先|我接著|我直接|我再|會|先|再|然後|完成後)", re.IGNORECASE),
            re.compile(r"^(這一節|重點是|原因是|目前其實有|資料模型與環境變數|UI、API、搜尋、錯誤處理與測試)", re.IGNORECASE),
            re.compile(r"^(如果|若|等)", re.IGNORECASE),
            re.compile(r"(你希望|哪一種|[?？])", re.IGNORECASE),
            re.compile(r"(避免|建議|應該|可以|只會動|不碰)", re.IGNORECASE),
            re.compile(r"(尚未開工|還沒開始|尚未提交|未提交|尚未)", re.IGNORECASE),
            re.compile(r"^(只有|這批就是)", re.IGNORECASE),
            re.compile(r"後面.*就能", re.IGNORECASE),
            re.compile(r"已同步到$", re.IGNORECASE),
        ),
    },
    "progress": {
        "positive": (
            re.compile(r"^(我正在|我現在|我在|我會|我先|我接著|我直接|我再|接下來|下一步|完成後|然後)", re.IGNORECASE),
            re.compile(r"(檢查|確認|比對|整理|補|修|讀|規劃|更新|同步|新增|建立|設計文件|實作計畫)", re.IGNORECASE),
        ),
        "negative": (
            re.compile(r"^(計畫如下|目前方向已很清楚)$", re.IGNORECASE),
            re.compile(r"^(我先讀取|我先讀|我現在進入修改|我現在會補.+塊|先確認這個想法|再開始收斂方案)", re.IGNORECASE),
            re.compile(r"^(我現在先做唯讀審核|我現在補最小實作|我現在補.+文件)$", re.IGNORECASE),
            re.compile(
                r"^(我先修這個|我接著讀經驗.+|我再補兩件事|我再做一個小修|然後直接補齊|然後補兩筆|我再補一層證據|我現在開始補正式實作)$",
                re.IGNORECASE,
            ),
            re.compile(r"(commit|提交|全綠|通過|已完成)", re.IGNORECASE),
        ),
    },
    "blocked": {
        "positive": (
            re.compile(r"(錯誤|失敗|阻塞|待確認|等待|無法|卡住|衝突|紅燈|缺件|不一致)", re.IGNORECASE),
        ),
        "negative": (
            re.compile(r"(不是內容錯誤|不是功能阻塞|不是行為錯誤)", re.IGNORECASE),
            re.compile(r"(沒有錯誤|無錯誤|已排除|已解決|已修復|較像|沒有新的阻塞)", re.IGNORECASE),
            re.compile(r"(不算有效的紅燈|不是功能退化|不是我們要的 red|都合理)", re.IGNORECASE),
            re.compile(r"(預期一致|如預期失敗)", re.IGNORECASE),
            re.compile(r"(一律先用|這一段不碰資料庫)", re.IGNORECASE),
            re.compile(r"^(我先|我會|我直接|我再|我補|我改|通過後|如果|等.+後)", re.IGNORECASE),
            re.compile(r"^(找到阻塞了|有阻塞問題|失敗點很清楚|失敗點很乾淨|沒有新的阻塞)$", re.IGNORECASE),
        ),
    },
}

SUMMARY_MIN_SCORE = {
    "completed": 1,
    "supplemental_completed": 6,
    "progress": 1,
    "blocked": 3,
}


def _format_datetime(value: datetime | None) -> str:
    if not value:
        return "-"
    return value.strftime("%Y-%m-%d %H:%M")


def _format_duration(minutes: int) -> str:
    hours, remainder = divmod(minutes, 60)
    if hours and remainder:
        return f"{hours}h {remainder}m"
    if hours:
        return f"{hours}h"
    return f"{remainder}m"


def _bullet_list(items: list[str], indent: str = "- ") -> list[str]:
    if not items:
        return [f"{indent}(none)"]
    return [f"{indent}{item}" for item in items]


def _compact_summary_text(value: str, limit: int = 120) -> str:
    normalized = " ".join(value.split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3] + "..."


def _score_summary_item(value: str, section: str) -> int:
    normalized = " ".join(value.split())
    score = 0
    if section == "progress":
        if re.search(r"^(我正在|我現在|我在)", normalized, re.IGNORECASE):
            score += 2
        elif re.search(
            r"^(我先|我接著|我直接|我再|接下來|下一步|完成後|然後)",
            normalized,
            re.IGNORECASE,
        ):
            score += 2
    rules = SUMMARY_SCORE_RULES.get(section)
    if rules is None and section == "supplemental_completed":
        rules = SUMMARY_SCORE_RULES.get("completed", {})
    if rules is None:
        rules = {}
    for pattern in rules.get("positive", ()):
        if pattern.search(normalized):
            score += 2
    for pattern in rules.get("negative", ()):
        if pattern.search(normalized):
            score -= 3
    if len(normalized) <= 80:
        score += 1
    elif len(normalized) >= 180:
        score -= 1
    return score


def _pick_summary_item(items: list[str], section: str) -> str | None:
    cleaned = [item.strip() for item in items if item and item.strip()]
    if not cleaned:
        return None
    candidates: list[str] = []
    for item in cleaned:
        if any(pattern.search(item) for pattern in SUMMARY_SKIP_PATTERNS):
            continue
        if section in {"completed", "supplemental_completed"} and re.search(
            r"(尚未|未提交)", item, re.IGNORECASE
        ):
            continue
        if section == "blocked" and re.fullmatch(r"(找到阻塞了|有阻塞問題)", item):
            continue
        candidates.append(item)
    if not candidates:
        if section in {"completed", "supplemental_completed", "blocked"}:
            return None
        candidates = cleaned
    ranked = sorted(
        ((_score_summary_item(item, section), item) for item in candidates),
        key=lambda entry: (entry[0], -len(entry[1])),
        reverse=True,
    )
    best_score, best_item = ranked[0]
    if best_score < SUMMARY_MIN_SCORE.get(section, 0):
        return None
    return _compact_summary_text(best_item)


def _render_project_summary(project: dict[str, Any]) -> list[str]:
    label = project.get("project_label") or project["project_key"]
    coverage = (
        f"{_format_duration(project.get('active_minutes', 0))} | "
        f"{_format_datetime(project.get('coverage_start'))} -> "
        f"{_format_datetime(project.get('coverage_end'))}"
    )
    completed = _pick_summary_item(project.get("confirmed_done", []), "completed")
    inferred = _pick_summary_item(project.get("inferred_done", []), "supplemental_completed")
    in_progress = _pick_summary_item(project.get("in_progress", []), "progress")
    blocked = _pick_summary_item(project.get("blocked", []), "blocked")

    lines = [
        f"### {label}",
        f"- 工時 / 時段：{coverage}",
    ]
    if completed:
        lines.append(f"- 主要完成：{completed}")
    elif inferred:
        lines.append(f"- 主要完成：{inferred}")
        inferred = None
    if inferred and inferred == completed:
        inferred = None
    if inferred and inferred == in_progress:
        inferred = None
    if inferred:
        lines.append(f"- 補充完成：{inferred}")
    if in_progress:
        lines.append(f"- 主要進行中：{in_progress}")
    if blocked:
        lines.append(f"- 阻塞：{blocked}")
    lines.append("")
    return lines


def render_report(
    window_label: str,
    projects: list[dict[str, Any]],
    stats: dict[str, Any] | None = None,
    warnings: list[str] | None = None,
) -> str:
    report_stats = stats or {}
    lines = [
        f"# 工作日誌：{window_label}",
        "",
        "## 摘要",
        f"- 專案數：{report_stats.get('project_count', len(projects))}",
        f"- Session 數：{report_stats.get('session_count', 0)}",
        f"- 總涵蓋時段：{_format_datetime(report_stats.get('coverage_start'))} -> {_format_datetime(report_stats.get('coverage_end'))}",
        f"- 估算有效工時：{_format_duration(report_stats.get('active_minutes', 0))}",
        "",
        "## 統計",
        f"- 總涵蓋時段：{_format_datetime(report_stats.get('coverage_start'))} -> {_format_datetime(report_stats.get('coverage_end'))}",
        f"- 估算有效工時：{_format_duration(report_stats.get('active_minutes', 0))}",
        f"- Session 數：{report_stats.get('session_count', 0)}",
        f"- 專案數：{report_stats.get('project_count', len(projects))}",
        "",
        "## 各專案工作摘要",
    ]

    for project in projects:
        lines.extend(_render_project_summary(project))

    lines.extend(
        [
        "## 各專案紀錄",
        ]
    )

    for project in projects:
        label = project.get("project_label") or project["project_key"]
        lines.extend(
            [
                f"### {label}",
                f"- 專案路徑：{project.get('project_path') or 'unclassified'}",
                f"- 主要工作時段：{_format_datetime(project.get('coverage_start'))} -> {_format_datetime(project.get('coverage_end'))}",
                f"- 花費時長：{_format_duration(project.get('active_minutes', 0))}",
                "- 已確認完成",
                *_bullet_list(project.get("confirmed_done", []), indent="  - "),
                "- 推定完成",
                *_bullet_list(project.get("inferred_done", []), indent="  - "),
                "- 進行中 / 計畫中",
                *_bullet_list(project.get("in_progress", []), indent="  - "),
                "- 阻塞 / 待確認",
                *_bullet_list(project.get("blocked", []), indent="  - "),
                "",
            ]
        )

    lines.extend(
        [
            "## 跨專案總結",
            f"- 已確認完成項目：{sum(len(project.get('confirmed_done', [])) for project in projects)}",
            f"- 推定完成項目：{sum(len(project.get('inferred_done', [])) for project in projects)}",
            f"- 進行中 / 計畫中：{sum(len(project.get('in_progress', [])) for project in projects)}",
            f"- 阻塞 / 待確認：{sum(len(project.get('blocked', [])) for project in projects)}",
            "",
            "## 後續建議 / 明日延續",
        ]
    )

    open_items = [
        item
        for project in projects
        for item in project.get("in_progress", []) + project.get("blocked", [])
    ]
    lines.extend(_bullet_list(open_items, indent="- "))
    lines.append("")

    if warnings:
        lines.extend(["## Warnings", *_bullet_list(warnings), ""])

    lines.extend(["## Evidence"])
    evidence = [path for project in projects for path in project.get("evidence", [])]
    lines.extend(_bullet_list(evidence, indent="- "))
    lines.extend(["", MANUAL_NOTES_HEADING, "- "])
    return "\n".join(lines) + "\n"


def extract_manual_notes(existing_text: str) -> str:
    match = re.search(
        rf"{re.escape(MANUAL_NOTES_HEADING)}\n(?P<content>.*)$",
        existing_text,
        re.DOTALL,
    )
    if not match:
        return "- "
    content = match.group("content").strip("\n")
    return content or "- "


def merge_manual_notes(rendered_text: str, manual_notes: str) -> str:
    if MANUAL_NOTES_HEADING not in rendered_text:
        return rendered_text.rstrip() + f"\n\n{MANUAL_NOTES_HEADING}\n{manual_notes}\n"
    prefix, _separator, _suffix = rendered_text.partition(f"{MANUAL_NOTES_HEADING}\n")
    return prefix + f"{MANUAL_NOTES_HEADING}\n{manual_notes.rstrip()}\n"


def write_report(path: Path, rendered_text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    manual_notes = "- "
    if path.exists():
        manual_notes = extract_manual_notes(path.read_text(encoding="utf-8"))
    path.write_text(merge_manual_notes(rendered_text, manual_notes), encoding="utf-8")
