"""Git 相關工具函數。

提供非內容異動（metadata changes）的檢測與處理功能。
"""

from dataclasses import dataclass, field
from pathlib import Path
import subprocess

from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table


@dataclass
class MetadataChanges:
    """非內容異動的檢測結果。"""

    mode_changes: list[str] = field(default_factory=list)
    """權限變更的檔案清單"""

    line_ending_changes: list[str] = field(default_factory=list)
    """換行符變更的檔案清單"""

    @property
    def has_changes(self) -> bool:
        """是否有任何非內容異動。"""
        return bool(self.mode_changes or self.line_ending_changes)

    @property
    def total_count(self) -> int:
        """非內容異動的檔案總數。"""
        return len(self.mode_changes) + len(self.line_ending_changes)


def is_git_repo(path: Path) -> bool:
    """檢查指定路徑是否為 git 目錄。

    Args:
        path: 要檢查的目錄路徑

    Returns:
        True 如果是 git 目錄，否則 False
    """
    git_dir = path / ".git"
    return git_dir.exists() and git_dir.is_dir()


def get_raw_diff(repo_path: Path) -> list[dict]:
    """取得 git diff --raw 的解析結果。

    Args:
        repo_path: git 倉庫路徑

    Returns:
        解析後的差異清單，每個項目包含：
        - old_mode: 舊權限
        - new_mode: 新權限
        - file_path: 檔案路徑
    """
    try:
        result = subprocess.run(
            ["git", "diff", "--raw"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError:
        return []

    diffs = []
    for line in result.stdout.strip().split("\n"):
        if not line:
            continue
        # 格式: :100644 100755 abc123 def456 M	path/to/file
        parts = line.split("\t")
        if len(parts) < 2:
            continue

        meta = parts[0].split()
        if len(meta) < 5:
            continue

        diffs.append(
            {
                "old_mode": meta[0].lstrip(":"),
                "new_mode": meta[1],
                "file_path": parts[1],
            }
        )

    return diffs


def detect_mode_changes(raw_diff: list[dict]) -> list[str]:
    """識別僅有權限變更的檔案。

    Args:
        raw_diff: get_raw_diff() 的輸出

    Returns:
        權限變更檔案的路徑清單
    """
    mode_changes = []
    for diff in raw_diff:
        if diff["old_mode"] != diff["new_mode"]:
            mode_changes.append(diff["file_path"])
    return mode_changes


def is_only_line_ending_diff(file_path: str, repo_path: Path) -> bool:
    """檢測檔案是否僅有換行符差異。

    Args:
        file_path: 相對於 repo_path 的檔案路徑
        repo_path: git 倉庫路徑

    Returns:
        True 如果只有換行符差異，否則 False
    """
    try:
        # 取得 git 版本的內容
        result = subprocess.run(
            ["git", "show", f"HEAD:{file_path}"],
            cwd=repo_path,
            capture_output=True,
            check=True,
        )
        git_content = result.stdout

        # 讀取工作目錄版本
        full_path = repo_path / file_path
        if not full_path.exists():
            return False
        work_content = full_path.read_bytes()

        # 正規化換行符後比對
        git_normalized = git_content.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
        work_normalized = work_content.replace(b"\r\n", b"\n").replace(b"\r", b"\n")

        return git_normalized == work_normalized

    except (subprocess.CalledProcessError, OSError):
        return False


def detect_metadata_changes(repo_path: Path) -> MetadataChanges:
    """檢測非內容異動。

    Args:
        repo_path: git 倉庫路徑

    Returns:
        MetadataChanges 包含檢測結果
    """
    changes = MetadataChanges()

    if not is_git_repo(repo_path):
        return changes

    raw_diff = get_raw_diff(repo_path)

    # 先取得有權限變更的檔案
    mode_change_files = set(detect_mode_changes(raw_diff))

    # 檢查每個有差異的檔案
    for diff in raw_diff:
        file_path = diff["file_path"]

        # 檢查是否只有權限變更（無內容差異）
        if file_path in mode_change_files:
            if is_only_line_ending_diff(file_path, repo_path):
                # 權限變更 + 換行符變更
                changes.mode_changes.append(file_path)
            else:
                # 檢查是否有實際內容差異
                result = subprocess.run(
                    ["git", "diff", "--quiet", file_path],
                    cwd=repo_path,
                    capture_output=True,
                )
                if result.returncode == 0:
                    # 無內容差異，只有權限變更
                    changes.mode_changes.append(file_path)
        else:
            # 檢查是否只有換行符變更
            if is_only_line_ending_diff(file_path, repo_path):
                changes.line_ending_changes.append(file_path)

    return changes


def revert_files(files: list[str], repo_path: Path) -> bool:
    """還原指定檔案到 git 記錄狀態。

    Args:
        files: 要還原的檔案路徑清單
        repo_path: git 倉庫路徑

    Returns:
        True 如果成功，否則 False
    """
    if not files:
        return True

    try:
        subprocess.run(
            ["git", "checkout", "--"] + files,
            cwd=repo_path,
            capture_output=True,
            check=True,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def set_filemode_config(repo_path: Path, value: bool) -> bool:
    """設定 git core.fileMode 配置。

    Args:
        repo_path: git 倉庫路徑
        value: True 或 False

    Returns:
        True 如果成功，否則 False
    """
    try:
        subprocess.run(
            ["git", "config", "core.fileMode", str(value).lower()],
            cwd=repo_path,
            capture_output=True,
            check=True,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def show_file_list(changes: MetadataChanges, console: Console) -> None:
    """顯示非內容異動檔案的詳細清單。

    Args:
        changes: 檢測結果
        console: Rich Console 實例
    """
    table = Table(title="非內容異動檔案清單")
    table.add_column("檔案路徑", style="cyan")
    table.add_column("異動類型", style="yellow")

    for file_path in changes.mode_changes:
        table.add_row(file_path, "權限變更")

    for file_path in changes.line_ending_changes:
        table.add_row(file_path, "換行符變更")

    console.print(table)


def handle_metadata_changes(changes: MetadataChanges, repo_path: Path, console: Console) -> None:
    """互動式處理非內容異動。

    Args:
        changes: 檢測結果
        repo_path: git 倉庫路徑
        console: Rich Console 實例
    """
    if not changes.has_changes:
        return

    console.print()
    console.print(f"[bold yellow]⚠️  偵測到 {changes.total_count} 個檔案有非內容異動：[/bold yellow]")
    if changes.mode_changes:
        console.print(f"   - 檔案權限變更: {len(changes.mode_changes)} 個")
    if changes.line_ending_changes:
        console.print(f"   - 換行符變更: {len(changes.line_ending_changes)} 個")
    console.print()
    console.print("[dim]這些變更不影響實際內容。如何處理？[/dim]")
    console.print()

    while True:
        console.print("  [1] 還原這些變更 (git checkout)     [bold]← 建議[/bold]")
        console.print("  [2] 設定 git 忽略權限 (core.fileMode=false)")
        console.print("  [3] 忽略，保留變更")
        console.print("  [4] 顯示詳細清單")
        console.print()

        choice = Prompt.ask("選擇", choices=["1", "2", "3", "4"], default="1")

        if choice == "1":
            all_files = changes.mode_changes + changes.line_ending_changes
            if revert_files(all_files, repo_path):
                console.print("[bold green]✓ 已還原所有非內容異動[/bold green]")
            else:
                console.print("[bold red]✗ 還原失敗，請手動執行 git checkout[/bold red]")
            break

        elif choice == "2":
            if set_filemode_config(repo_path, False):
                console.print("[bold green]✓ 已設定 core.fileMode=false[/bold green]")
                console.print("[dim]Git 將忽略檔案權限差異[/dim]")
            else:
                console.print("[bold red]✗ 設定失敗[/bold red]")
            break

        elif choice == "3":
            console.print("[dim]保留變更，不做任何處理[/dim]")
            break

        elif choice == "4":
            show_file_list(changes, console)
            console.print()
            # 顯示清單後繼續迴圈，讓使用者選擇其他選項
