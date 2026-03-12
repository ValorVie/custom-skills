from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta
from pathlib import Path
import re
from typing import Any


CLAUSE_SPLIT_PATTERN = re.compile(
    r"[。；;：:]|，(?=(?:我正在|我現在|我在|我接著|現在|目前|先|再|接下來|下一步|之後|接著|再來|然後|準備|預計|待辦|規劃|確認))"
)

CONFIRMED_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in [
        r"\bcompleted?\b",
        r"\bdone\b",
        r"\bmerged?\b",
        r"\bcommitted?\b",
        r"完成",
        r"已完成",
        r"完成了",
        r"已提交",
        r"修正完成",
        r"部署完成",
    ]
]

INFERRED_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in [
        r"\badded?\b",
        r"\bimplemented?\b",
        r"\bupdated?\b",
        r"\bwrote\b",
        r"\bbuilt\b",
        r"新增",
        r"加入",
        r"實作",
        r"建立",
        r"撰寫",
        r"更新",
        r"修改",
        r"補上",
        r"同步",
        r"產出",
    ]
]

IN_PROGRESS_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in [
        r"\bnext\b",
        r"\bplan\b",
        r"\bplanned\b",
        r"\btodo\b",
        r"\bpending\b",
        r"下一步",
        r"計畫",
        r"規劃",
        r"待辦",
        r"進行中",
        r"接下來",
        r"準備",
        r"預計",
        r"確認",
    ]
]

BLOCKED_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in [
        r"\berror\b",
        r"\bfailed?\b",
        r"\bexception\b",
        r"\bblocked\b",
        r"錯誤",
        r"失敗",
        r"阻塞",
        r"待確認",
        r"等待",
        r"無法",
    ]
]

META_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in [
        r"^<subagent_notification>",
        r"\bI'?m using the\b",
        r"我已讀完",
        r"我已讀取",
        r"請做 review",
        r"\breview\b",
    ]
]

NEGATED_ISSUE_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in [
        r"沒有錯誤",
        r"無錯誤",
        r"沒有失敗",
        r"無失敗",
        r"沒錯就",
        r"不是內容錯誤",
        r"不是功能阻塞",
        r"不是行為錯誤",
    ]
]

NON_COMPLETION_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in [
        r"未完成",
        r"完成度",
        r"完成率",
        r"規劃完成度",
        r"尚未",
        r"未提交",
        r"尚未開工",
        r"還沒開始",
    ]
]

RESOLVED_ISSUE_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in [
        r"(修復|修正|解決|排除).*(錯誤|失敗|exception|error|問題)",
        r"處理.*(完成|已完成|完畢|好了)",
        r"(錯誤|失敗|exception|error|問題).*(已修復|已修正|已解決|已排除|處理完成)",
        r"(錯誤|失敗|阻塞|問題).*(排除了|已排除|解除|已解除|收掉|清掉|過了)",
    ]
]

PROGRESS_PRIORITY_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in [
        r"^(我正在|我現在|我在|我接著|我會|我直接|我再|現在|目前|接著|接下來|下一步|之後|完成後|我先|我要|我想把|這次會|會先|會再|會直接|會把|會生成|先|再|然後)",
        r"一定要先",
    ]
]

EXPLANATION_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in [
        r"^原因是",
        r"^這一節",
        r"^重點是",
        r"^目前其實有",
        r"^資料模型與環境變數",
        r"^UI、API、搜尋、錯誤處理與測試",
    ]
]

QUESTION_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in [
        r"[?？]",
        r"你希望",
        r"哪一種",
        r"要不要",
    ]
]

STRUCTURAL_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in [
        r"^\d+\.",
        r"^[-*]\s",
    ]
]


@dataclass
class TimeWindow:
    start: datetime
    end: datetime
    label: str
    bucket: str


def parse_timestamp(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, (int, float)):
        timestamp = float(value)
        if timestamp > 10_000_000_000:
            timestamp /= 1000.0
        return datetime.fromtimestamp(timestamp).astimezone()
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        if text.isdigit():
            return parse_timestamp(int(text))
        try:
            return datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone()
        except ValueError:
            return None
    return None


def normalize_path(value: str | None) -> str | None:
    if not value:
        return None
    return str(Path(value).expanduser())


def derive_project_key(project_path: str | None) -> str:
    normalized = normalize_path(project_path)
    if not normalized:
        return "unclassified"
    return normalized


def derive_project_label(project_path: str | None) -> str:
    normalized = normalize_path(project_path)
    if not normalized:
        return "unclassified"
    name = Path(normalized).name
    return name or normalized


def build_activity_windows(
    timestamps: list[Any], idle_threshold_minutes: int = 30
) -> list[tuple[datetime, datetime, int]]:
    parsed = sorted(ts for ts in (parse_timestamp(value) for value in timestamps) if ts)
    if not parsed:
        return []

    windows: list[tuple[datetime, datetime, int]] = []
    window_start = parsed[0]
    window_end = parsed[0]

    for current in parsed[1:]:
        delta_minutes = (current - window_end).total_seconds() / 60
        if delta_minutes <= idle_threshold_minutes:
            window_end = current
            continue
        windows.append(_finalize_activity_window(window_start, window_end))
        window_start = current
        window_end = current

    windows.append(_finalize_activity_window(window_start, window_end))
    return windows


def _finalize_activity_window(
    start: datetime, end: datetime
) -> tuple[datetime, datetime, int]:
    if end <= start:
        return (start, end, 0)
    minutes = max(1, int(((end - start).total_seconds() + 59) // 60))
    return (start, end, minutes)


def bucket_active_minutes(
    timestamps: list[Any], idle_threshold_minutes: int = 30
) -> int:
    return sum(
        minutes
        for _start, _end, minutes in build_activity_windows(
            timestamps, idle_threshold_minutes=idle_threshold_minutes
        )
    )


def build_time_window(
    range_name: str,
    start_text: str | None = None,
    end_text: str | None = None,
    now: datetime | None = None,
) -> TimeWindow:
    current = (now or datetime.now().astimezone()).replace(microsecond=0)
    normalized = range_name.strip().lower()

    if start_text or end_text:
        if not start_text or not end_text:
            raise ValueError("Both --start and --end are required together.")
        start = parse_timestamp(start_text)
        end = parse_timestamp(end_text)
        if not start or not end:
            raise ValueError("Could not parse explicit time range.")
        return TimeWindow(start=start, end=end, label=f"{start_text} -> {end_text}", bucket="custom")

    if normalized in {"today", "今天"}:
        start = current.replace(hour=0, minute=0, second=0)
        end = start + timedelta(days=1)
        return TimeWindow(start=start, end=end, label="今天", bucket="daily")

    if normalized in {"yesterday", "昨天"}:
        end = current.replace(hour=0, minute=0, second=0)
        start = end - timedelta(days=1)
        return TimeWindow(start=start, end=end, label="昨天", bucket="daily")

    if normalized in {"this-week", "this_week", "week", "本週"}:
        start = current.replace(hour=0, minute=0, second=0) - timedelta(days=current.weekday())
        end = start + timedelta(days=7)
        return TimeWindow(start=start, end=end, label="本週", bucket="weekly")

    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", range_name):
        date = datetime.fromisoformat(range_name).astimezone()
        start = datetime.combine(date.date(), time.min, tzinfo=current.tzinfo)
        end = start + timedelta(days=1)
        return TimeWindow(start=start, end=end, label=range_name, bucket="daily")

    raise ValueError(f"Unsupported time range: {range_name}")


def event_in_window(timestamp: Any, window: TimeWindow) -> bool:
    parsed = parse_timestamp(timestamp)
    if not parsed:
        return False
    return window.start <= parsed < window.end


def compact_text(value: str | None, limit: int = 120) -> str | None:
    if not value:
        return None
    normalized = " ".join(value.split())
    if not normalized:
        return None
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3] + "..."


def signal_text(event: dict[str, Any]) -> str:
    title = compact_text(event.get("title"))
    text = compact_text(event.get("text"))
    parts: list[str] = []
    if text:
        parts.append(text)
    elif title:
        parts.append(title)
    raw = event.get("raw", {})
    if isinstance(raw, dict):
        for key in ("content", "output", "description", "command"):
            value = compact_text(raw.get(key))
            if value and value not in parts:
                parts.append(value)
    if not text and title and title not in parts:
        parts.insert(0, title)
    return " | ".join(parts)


def _matches_any(text: str, patterns: list[re.Pattern[str]]) -> bool:
    return any(pattern.search(text) for pattern in patterns)


def _append_unique(target: list[str], value: str) -> None:
    if value not in target:
        target.append(value)


def _split_signal_fragments(text: str) -> list[str]:
    fragments: list[str] = []
    for segment in text.split(" | "):
        for fragment in CLAUSE_SPLIT_PATTERN.split(segment):
            normalized = compact_text(fragment, limit=240)
            if normalized and normalized not in fragments:
                fragments.append(normalized)
    return fragments


def is_negated_issue(text: str) -> bool:
    return _matches_any(text, NEGATED_ISSUE_PATTERNS)


def is_completion_context(text: str) -> bool:
    if _matches_any(text, NON_COMPLETION_PATTERNS):
        return False
    if _matches_any(text, RESOLVED_ISSUE_PATTERNS):
        return True
    return _matches_any(text, CONFIRMED_PATTERNS)


def is_progress_priority(text: str) -> bool:
    return _matches_any(text, PROGRESS_PRIORITY_PATTERNS)


def is_explanatory_context(text: str) -> bool:
    return _matches_any(text, EXPLANATION_PATTERNS)


def is_question_context(text: str) -> bool:
    return _matches_any(text, QUESTION_PATTERNS)


def is_structural_context(text: str) -> bool:
    return _matches_any(text, STRUCTURAL_PATTERNS)


def classify_evidence(text: str) -> dict[str, str]:
    normalized = compact_text(text, limit=240)
    if not normalized:
        return {"kind": "unknown", "text": ""}
    if _matches_any(normalized, META_PATTERNS):
        return {"kind": "meta", "text": normalized}
    if is_question_context(normalized) or is_structural_context(normalized):
        return {"kind": "unknown", "text": normalized}
    if is_explanatory_context(normalized):
        return {"kind": "unknown", "text": normalized}
    if is_progress_priority(normalized) or _matches_any(normalized, IN_PROGRESS_PATTERNS):
        return {"kind": "progress", "text": normalized}
    if is_completion_context(normalized):
        return {"kind": "deliverable", "status": "confirmed", "text": normalized}
    if _matches_any(normalized, INFERRED_PATTERNS):
        return {"kind": "deliverable", "status": "inferred", "text": normalized}
    if not is_negated_issue(normalized) and _matches_any(normalized, BLOCKED_PATTERNS):
        return {"kind": "issue", "text": normalized}
    return {"kind": "unknown", "text": normalized}


def summarize_project_events(
    project_key: str,
    project_path: str | None,
    events: list[dict[str, Any]],
    idle_threshold_minutes: int = 30,
) -> dict[str, Any]:
    filtered_events = [event for event in events if _should_include_event(event)]
    timestamps = [event.get("timestamp") for event in filtered_events]
    parsed = sorted(ts for ts in (parse_timestamp(value) for value in timestamps) if ts)
    activity_windows = build_activity_windows(
        timestamps, idle_threshold_minutes=idle_threshold_minutes
    )
    confirmed_done: list[str] = []
    inferred_done: list[str] = []
    in_progress: list[str] = []
    blocked: list[str] = []
    evidence: list[str] = []
    warnings: list[str] = []

    for event in filtered_events:
        for fragment in _split_signal_fragments(signal_text(event)):
            evidence_item = classify_evidence(fragment)
            kind = evidence_item.get("kind")
            text = evidence_item.get("text")
            if not text or kind in {"meta", "unknown"}:
                continue
            if kind == "deliverable" and evidence_item.get("status") == "confirmed":
                _append_unique(confirmed_done, text)
                continue
            if kind == "deliverable":
                _append_unique(inferred_done, text)
                continue
            if kind == "progress":
                _append_unique(in_progress, text)
                continue
            if kind == "issue":
                _append_unique(blocked, text)
        evidence_path = event.get("evidence_path")
        if evidence_path:
            _append_unique(evidence, str(evidence_path))

    if not activity_windows or not any(minutes > 0 for _start, _end, minutes in activity_windows):
        warnings.append("Sparse event history; effective work time is low-confidence.")

    session_count = len(
        {event.get("session_id") for event in filtered_events if event.get("session_id")}
    )
    return {
        "project_key": project_key,
        "project_path": project_path,
        "session_count": session_count,
        "confirmed_done": confirmed_done,
        "inferred_done": inferred_done,
        "in_progress": in_progress,
        "blocked": blocked,
        "evidence": evidence,
        "warnings": warnings,
        "active_minutes": sum(minutes for _start, _end, minutes in activity_windows),
        "activity_windows": [(start, end) for start, end, _minutes in activity_windows],
        "coverage_start": parsed[0] if parsed else None,
        "coverage_end": parsed[-1] if parsed else None,
    }


def build_project_summaries(
    events: list[dict[str, Any]], idle_threshold_minutes: int = 30
) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    project_paths: dict[str, str | None] = {}
    project_labels: dict[str, str | None] = {}
    for event in events:
        if not _should_include_event(event):
            continue
        key = event.get("project_key") or derive_project_key(event.get("project_path"))
        grouped.setdefault(key, []).append(event)
        project_paths.setdefault(key, event.get("project_path"))
        project_labels.setdefault(key, event.get("project_label"))

    summaries = [
        summarize_project_events(
            project_key=key,
            project_path=project_paths.get(key),
            events=sorted(grouped[key], key=lambda item: parse_timestamp(item.get("timestamp")) or datetime.min.astimezone()),
            idle_threshold_minutes=idle_threshold_minutes,
        )
        for key in sorted(grouped)
    ]
    for summary in summaries:
        summary["project_label"] = project_labels.get(summary["project_key"]) or derive_project_label(
            summary.get("project_path")
        )
    return summaries


def dedupe_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: dict[tuple[Any, ...], dict[str, Any]] = {}
    confidence_rank = {"low": 0, "medium": 1, "high": 2}

    for event in events:
        signature = (
            event.get("tool"),
            event.get("session_id"),
            str(parse_timestamp(event.get("timestamp")) or event.get("timestamp")),
            event.get("event_type"),
            event.get("title"),
            event.get("text"),
        )
        current = deduped.get(signature)
        if not current:
            deduped[signature] = event
            continue
        event_rank = confidence_rank.get(str(event.get("confidence")), -1)
        current_rank = confidence_rank.get(str(current.get("confidence")), -1)
        if event_rank > current_rank:
            deduped[signature] = event
            continue
        if event_rank == current_rank and event.get("project_path") and not current.get("project_path"):
            deduped[signature] = event

    return list(deduped.values())


def _should_include_event(event: dict[str, Any]) -> bool:
    if _is_user_event(event):
        return False
    if str(event.get("confidence")) == "low" and not event.get("project_path"):
        return False
    return True


def _is_user_event(event: dict[str, Any]) -> bool:
    title = str(event.get("title") or "").strip().lower()
    if title == "user":
        return True
    raw = event.get("raw")
    if isinstance(raw, dict):
        payload = raw.get("payload")
        if isinstance(payload, dict):
            role = str(payload.get("role") or "").strip().lower()
            if role == "user":
                return True
    return False


def build_overall_stats(projects: list[dict[str, Any]]) -> dict[str, Any]:
    coverage_points = [
        parsed
        for project in projects
        for point in (project.get("coverage_start"), project.get("coverage_end"))
        if (parsed := parse_timestamp(point))
    ]
    coverage_points.sort()
    session_count = sum(project.get("session_count", 0) for project in projects)
    active_minutes = _merge_activity_windows(projects)
    return {
        "coverage_start": coverage_points[0] if coverage_points else None,
        "coverage_end": coverage_points[-1] if coverage_points else None,
        "active_minutes": active_minutes,
        "session_count": session_count,
        "project_count": len(projects),
    }


def _merge_activity_windows(projects: list[dict[str, Any]]) -> int:
    windows: list[tuple[datetime, datetime]] = []
    for project in projects:
        for window in project.get("activity_windows", []):
            normalized = _normalize_window(window)
            if normalized:
                windows.append(normalized)

    if not windows:
        return sum(project.get("active_minutes", 0) for project in projects)

    windows.sort(key=lambda item: item[0])
    merged: list[tuple[datetime, datetime]] = []
    current_start, current_end = windows[0]

    for start, end in windows[1:]:
        if start <= current_end:
            if end > current_end:
                current_end = end
            continue
        merged.append((current_start, current_end))
        current_start, current_end = start, end

    merged.append((current_start, current_end))

    total = 0
    for start, end in merged:
        if end <= start:
            continue
        total += max(1, int(((end - start).total_seconds() + 59) // 60))
    return total


def _normalize_window(window: Any) -> tuple[datetime, datetime] | None:
    if not isinstance(window, (tuple, list)) or len(window) < 2:
        return None
    start = parse_timestamp(window[0])
    end = parse_timestamp(window[1])
    if not start or not end:
        return None
    if end < start:
        return end, start
    return start, end
