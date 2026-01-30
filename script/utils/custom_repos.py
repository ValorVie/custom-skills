"""
Custom Repos 管理：使用者自訂 repo 的設定檔讀寫、結構驗證。
"""

from datetime import datetime
from pathlib import Path

import yaml
from rich.console import Console

console = Console()

# Custom repo 根目錄必須包含的目錄
REQUIRED_DIRS = ["agents", "skills", "commands", "hooks", "plugins"]


def get_custom_repos_config_path() -> Path:
    """回傳 custom repos 設定檔路徑。"""
    return Path.home() / ".config" / "ai-dev" / "repos.yaml"


def load_custom_repos() -> dict:
    """讀取 custom repos 設定檔。

    Returns:
        dict: 設定檔內容，檔案不存在時回傳 {"repos": {}}
    """
    config_path = get_custom_repos_config_path()
    if not config_path.exists():
        return {"repos": {}}

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            if data is None or not isinstance(data, dict):
                return {"repos": {}}
            if "repos" not in data:
                data["repos"] = {}
            return data
    except Exception as e:
        console.print(f"[yellow]警告：讀取 repos.yaml 失敗 ({e})[/yellow]")
        return {"repos": {}}


def save_custom_repos(data: dict) -> None:
    """寫入 custom repos 設定檔。

    Args:
        data: 設定檔內容
    """
    config_path = get_custom_repos_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)

    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(
            data, f, allow_unicode=True, default_flow_style=False, sort_keys=False
        )


def add_custom_repo(name: str, url: str, branch: str, local_path: str) -> bool:
    """新增 custom repo 條目到設定檔。

    Args:
        name: repo 名稱（作為 key）
        url: Git clone URL
        branch: 追蹤的分支
        local_path: 本地路徑（如 ~/.config/company-tools/）

    Returns:
        bool: 是否成功新增
    """
    data = load_custom_repos()

    if name in data["repos"]:
        console.print(f"[yellow]⚠ {name} 已存在於 repos.yaml[/yellow]")
        return False

    data["repos"][name] = {
        "url": url,
        "branch": branch,
        "local_path": local_path,
        "added_at": datetime.now().astimezone().isoformat(),
    }

    save_custom_repos(data)
    console.print(f"[green]✓ 已加入 repos.yaml[/green]")
    return True


def remove_custom_repo(name: str) -> bool:
    """從設定檔移除 custom repo 條目。

    Args:
        name: repo 名稱

    Returns:
        bool: 是否成功移除
    """
    data = load_custom_repos()

    if name not in data["repos"]:
        console.print(f"[yellow]⚠ {name} 不存在於 repos.yaml[/yellow]")
        return False

    del data["repos"][name]
    save_custom_repos(data)
    console.print(f"[green]✓ 已從 repos.yaml 移除 {name}[/green]")
    return True


def list_custom_repos() -> dict:
    """回傳所有 custom repos 清單。

    Returns:
        dict: repos 字典（key 為名稱，value 為 repo 資訊）
    """
    data = load_custom_repos()
    return data.get("repos", {})


def validate_repo_structure(repo_dir: Path, auto_fix: bool = False) -> list[str]:
    """驗證 repo 目錄結構是否符合規範。

    檢查根目錄是否包含五個必要目錄。缺少時發出警告但不阻擋。

    Args:
        repo_dir: repo 本地目錄
        auto_fix: 是否自動建立缺少的目錄（含 .gitkeep）

    Returns:
        list[str]: 缺少的目錄名稱清單（空表示全部合規）
    """
    missing = []
    for dir_name in REQUIRED_DIRS:
        if not (repo_dir / dir_name).is_dir():
            missing.append(dir_name)

    if missing:
        console.print(f"[yellow]⚠ 缺少以下目錄：{', '.join(missing)}[/yellow]")
        if auto_fix:
            for dir_name in missing:
                dir_path = repo_dir / dir_name
                dir_path.mkdir(parents=True, exist_ok=True)
                (dir_path / ".gitkeep").touch()
            console.print(
                f"[green]✓ 已自動建立 {len(missing)} 個目錄（含 .gitkeep）[/green]"
            )
            missing = []
        else:
            console.print(
                "[dim]  提示：Git 不追蹤空目錄，建議在各目錄中加入 .gitkeep 檔案[/dim]"
            )
    else:
        console.print("[green]✓ 目錄結構驗證通過[/green]")

    return missing
