"""
Project Tracking：讀寫 .ai-dev-project.yaml，追蹤由 init-from 模板管理的檔案。
"""

from datetime import datetime
from pathlib import Path

import yaml
from rich.console import Console

console = Console()

PROJECT_TRACKING_FILE = ".ai-dev-project.yaml"


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
            return data
    except Exception as e:
        console.print(f"[yellow]警告：讀取 {PROJECT_TRACKING_FILE} 失敗 ({e})[/yellow]")
        return None


def save_tracking_file(data: dict, project_dir: Path | None = None) -> None:
    """寫入 .ai-dev-project.yaml。"""
    tracking_path = get_tracking_file_path(project_dir)

    with open(tracking_path, "w", encoding="utf-8") as f:
        yaml.dump(
            data, f, allow_unicode=True, default_flow_style=False, sort_keys=False
        )


def create_tracking_file(
    name: str,
    url: str,
    branch: str,
    managed_files: list[str],
    project_dir: Path | None = None,
) -> None:
    """建立新的 .ai-dev-project.yaml（首次 init-from 時使用）。"""
    now = datetime.now().astimezone().isoformat()
    data = {
        "template": {
            "name": name,
            "url": url,
            "branch": branch,
            "initialized_at": now,
            "last_updated": now,
        },
        "managed_files": sorted(managed_files),
    }
    save_tracking_file(data, project_dir)


def update_tracking_file(
    managed_files: list[str],
    project_dir: Path | None = None,
) -> None:
    """更新既有 .ai-dev-project.yaml 的 managed_files 和 last_updated。"""
    data = load_tracking_file(project_dir)
    if data is None:
        raise FileNotFoundError(
            f"{PROJECT_TRACKING_FILE} 不存在，請先執行 `ai-dev init-from <source>`"
        )

    data.setdefault("template", {})["last_updated"] = (
        datetime.now().astimezone().isoformat()
    )
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
