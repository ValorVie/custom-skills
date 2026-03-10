"""專案投影 manifest：追蹤專案內 AI 生成檔的本機狀態。"""

from pathlib import Path

import yaml
from rich.console import Console

from .paths import get_project_manifest_dir

console = Console()


def get_project_manifest_path(project_id: str) -> Path:
    """回傳指定 project_id 的本機投影 manifest 路徑。"""
    return get_project_manifest_dir() / f"{project_id}.yaml"


def read_project_manifest(project_id: str) -> dict | None:
    """讀取專案投影 manifest。"""
    manifest_path = get_project_manifest_path(project_id)

    if not manifest_path.exists():
        return None

    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            if data is None or not isinstance(data, dict):
                console.print(
                    "[yellow]警告：project projection manifest 格式無效[/yellow]"
                )
                return None
            return data
    except yaml.YAMLError as e:
        console.print(
            f"[yellow]警告：project projection manifest 損壞 ({e})[/yellow]"
        )
        return None
    except Exception as e:
        console.print(
            f"[yellow]警告：讀取 project projection manifest 失敗 ({e})[/yellow]"
        )
        return None


def write_project_manifest(project_id: str, manifest: dict) -> Path:
    """寫入專案投影 manifest。"""
    manifest_path = get_project_manifest_path(project_id)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    with open(manifest_path, "w", encoding="utf-8") as f:
        yaml.dump(manifest, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    return manifest_path
