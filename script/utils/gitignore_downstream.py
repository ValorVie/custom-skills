"""
gitignore-downstream：將模版的 .gitignore-downstream 合併為目標 .gitignore 中的標記區塊。
"""

from pathlib import Path

from rich.console import Console

console = Console()

DOWNSTREAM_FILENAME = ".gitignore-downstream"

MARKER_START = "# >>> {name} (managed by ai-dev init-from, DO NOT EDIT)"
MARKER_END = "# <<< {name}"


def merge_gitignore_downstream(
    template_dir: Path,
    target_dir: Path,
    template_name: str,
    remove_if_missing: bool = False,
) -> bool:
    """將模版的 .gitignore-downstream 合併到目標 .gitignore 的標記區塊。

    Args:
        template_dir: 模版本地目錄
        target_dir: 目標專案目錄
        template_name: 模版名稱（用於標記）
        remove_if_missing: 若模版已無 downstream 檔案，是否移除既有區塊

    Returns:
        bool: 是否有修改 .gitignore
    """
    downstream_file = template_dir / DOWNSTREAM_FILENAME
    gitignore_path = target_dir / ".gitignore"
    start_marker = MARKER_START.format(name=template_name)
    end_marker = MARKER_END.format(name=template_name)

    # 讀取 downstream 內容
    if downstream_file.is_file():
        downstream_content = downstream_file.read_text(encoding="utf-8").strip()
    else:
        downstream_content = None

    # 模版無 downstream 且不需移除 → 跳過
    if downstream_content is None and not remove_if_missing:
        return False

    # 讀取現有 .gitignore
    if gitignore_path.is_file():
        existing = gitignore_path.read_text(encoding="utf-8")
    else:
        existing = ""

    lines = existing.splitlines(keepends=True)

    # 尋找既有區塊
    start_idx = None
    end_idx = None
    for i, line in enumerate(lines):
        stripped = line.rstrip("\n\r")
        if stripped == start_marker:
            start_idx = i
        elif stripped == end_marker and start_idx is not None:
            end_idx = i
            break

    has_block = start_idx is not None and end_idx is not None

    if downstream_content is None:
        # 模版已刪除 downstream → 移除區塊
        if has_block:
            del lines[start_idx : end_idx + 1]
            # 移除區塊前的空行
            if start_idx > 0 and start_idx <= len(lines) and lines[start_idx - 1].strip() == "":
                del lines[start_idx - 1]
            result = "".join(lines)
            if result and not result.endswith("\n"):
                result += "\n"
            gitignore_path.write_text(result, encoding="utf-8")
            console.print(f"  [yellow]已移除 .gitignore 中的 {template_name} 區塊[/yellow]")
            return True
        return False

    # 建構區塊
    block = f"{start_marker}\n{downstream_content}\n{end_marker}\n"

    if has_block:
        # 替換既有區塊
        lines[start_idx : end_idx + 1] = [block]
        result = "".join(lines)
    else:
        # 附加到尾部
        result = existing
        if result and not result.endswith("\n"):
            result += "\n"
        if result:
            result += "\n"
        result += block

    if result and not result.endswith("\n"):
        result += "\n"

    gitignore_path.write_text(result, encoding="utf-8")
    if has_block:
        console.print(f"  [cyan]已更新 .gitignore 中的 {template_name} 區塊[/cyan]")
    else:
        console.print(f"  [green]已新增 .gitignore 中的 {template_name} 區塊[/green]")
    return True
