"""
Project Tracking：讀寫 .ai-dev-project.yaml，追蹤專案意圖與模板管理檔案。
"""

from copy import deepcopy
from pathlib import Path
import re

import yaml
from rich.console import Console

console = Console()

PROJECT_TRACKING_FILE = ".ai-dev-project.yaml"
TRACKING_SCHEMA_VERSION = "2"
DEFAULT_PROJECTION = {
    "targets": ["claude", "codex", "gemini"],
    "profile": "default",
    "allow_local_generation": True,
}


def _generate_project_id(project_dir: Path | None = None) -> str:
    """依目錄名稱產生穩定的 project_id。"""
    base = Path(project_dir or Path.cwd()).resolve().name.strip().lower()
    normalized = re.sub(r"[^a-z0-9]+", "-", base).strip("-")
    return normalized or "ai-dev-project"


def _apply_tracking_defaults(
    data: dict, project_dir: Path | None = None, persist: bool = False
) -> dict:
    """補齊 schema v2 的預設欄位，保留舊檔相容性。"""
    changed = False

    if data.get("managed_by") != "ai-dev":
        data["managed_by"] = "ai-dev"
        changed = True

    if data.get("schema_version") != TRACKING_SCHEMA_VERSION:
        data["schema_version"] = TRACKING_SCHEMA_VERSION
        changed = True

    if not data.get("project_id"):
        data["project_id"] = _generate_project_id(project_dir)
        changed = True

    projection = data.get("projection")
    if not isinstance(projection, dict):
        data["projection"] = dict(DEFAULT_PROJECTION)
        changed = True
    else:
        for key, value in DEFAULT_PROJECTION.items():
            if key not in projection:
                projection[key] = value[:] if isinstance(value, list) else value
                changed = True

    if "managed_files" in data and isinstance(data["managed_files"], list):
        sorted_files = sorted(data["managed_files"])
        if sorted_files != data["managed_files"]:
            data["managed_files"] = sorted_files
            changed = True

    if persist and changed:
        save_tracking_file(data, project_dir)

    return data


def _strip_runtime_template_fields(data: dict) -> dict:
    """移除不應留在 project intent 的 runtime template 欄位。"""
    template = data.get("template")
    if isinstance(template, dict):
        template.pop("initialized_at", None)
        template.pop("last_updated", None)
    return data


def get_tracking_file_path(project_dir: Path | None = None) -> Path:
    """回傳 .ai-dev-project.yaml 的路徑。"""
    base = project_dir or Path.cwd()
    return base / PROJECT_TRACKING_FILE


def load_tracking_file(project_dir: Path | None = None) -> dict | None:
    """讀取 .ai-dev-project.yaml。

    Returns:
        dict: 追蹤檔案內容，不存在時回傳 None
    """
    tracking_path = get_tracking_file_path(project_dir)
    if not tracking_path.exists():
        return None

    try:
        with open(tracking_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            if not isinstance(data, dict):
                return None
            return _apply_tracking_defaults(data, project_dir)
    except Exception as e:
        console.print(f"[yellow]警告：讀取 {PROJECT_TRACKING_FILE} 失敗 ({e})[/yellow]")
        return None


def save_tracking_file(data: dict, project_dir: Path | None = None) -> None:
    """寫入 .ai-dev-project.yaml。"""
    tracking_path = get_tracking_file_path(project_dir)
    normalized = _apply_tracking_defaults(deepcopy(data), project_dir)
    normalized = _strip_runtime_template_fields(normalized)

    with open(tracking_path, "w", encoding="utf-8") as f:
        yaml.dump(
            normalized, f, allow_unicode=True, default_flow_style=False, sort_keys=False
        )


def create_tracking_file(
    name: str,
    url: str,
    branch: str,
    managed_files: list[str],
    project_dir: Path | None = None,
) -> None:
    """建立新的 .ai-dev-project.yaml（首次 init-from 時使用）。"""
    data = {
        "managed_by": "ai-dev",
        "schema_version": TRACKING_SCHEMA_VERSION,
        "project_id": _generate_project_id(project_dir),
        "template": {
            "name": name,
            "url": url,
            "branch": branch,
        },
        "projection": dict(DEFAULT_PROJECTION),
        "managed_files": sorted(managed_files),
    }
    save_tracking_file(data, project_dir)


def update_tracking_file(
    managed_files: list[str],
    project_dir: Path | None = None,
) -> None:
    """更新既有 .ai-dev-project.yaml 的 managed_files。"""
    data = load_tracking_file(project_dir)
    if data is None:
        raise FileNotFoundError(
            f"{PROJECT_TRACKING_FILE} 不存在，請先執行 `ai-dev init-from <source>`"
        )

    data = _apply_tracking_defaults(data, project_dir)
    data["managed_files"] = sorted(managed_files)
    save_tracking_file(data, project_dir)


def get_managed_files(project_dir: Path | None = None) -> list[str]:
    """取得由模板管理的檔案清單。

    Returns:
        list[str]: 相對路徑清單，不存在追蹤檔案時回傳空清單
    """
    data = load_tracking_file(project_dir)
    if data is None:
        return []
    return data.get("managed_files", [])


def is_file_managed(relative_path: str, project_dir: Path | None = None) -> str | None:
    """檢查指定檔案是否由模板管理。

    Returns:
        str | None: 管理此檔案的模板名稱，若未管理則回傳 None
    """
    data = load_tracking_file(project_dir)
    if data is None:
        return None

    managed = data.get("managed_files", [])
    if relative_path in managed:
        return data.get("template", {}).get("name")
    return None


def get_git_exclude_config(project_dir: Path | None = None) -> dict | None:
    """取得 git_exclude 設定。

    Returns:
        dict: git_exclude 設定，不存在時回傳 None
    """
    data = load_tracking_file(project_dir)
    if data is None:
        return None
    return data.get("git_exclude")


def update_git_exclude_config(
    enabled: bool,
    patterns: list[str],
    keep_tracked: list[str],
    version: str = "1",
    project_dir: Path | None = None,
) -> None:
    """更新 .ai-dev-project.yaml 中的 git_exclude 設定。"""
    data = load_tracking_file(project_dir)
    if data is None:
        data = {}

    data = _apply_tracking_defaults(data, project_dir)

    data["git_exclude"] = {
        "enabled": enabled,
        "version": version,
        "patterns": sorted(patterns),
        "keep_tracked": sorted(keep_tracked),
    }
    save_tracking_file(data, project_dir)
