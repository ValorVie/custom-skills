"""測試生成命令 - 讀取 specs 檔案內容。"""

import sys
from pathlib import Path

import typer
from rich.console import Console

console = Console()


def find_spec_files(path: str) -> list[Path]:
    """搜尋 specs 檔案。

    支援目錄和單一檔案輸入。

    Args:
        path: 檔案或目錄路徑

    Returns:
        找到的 spec 檔案列表
    """
    p = Path(path)
    if p.is_file():
        return [p]
    if p.is_dir():
        return sorted(p.glob("**/*.md"))
    return []


def derive_tests(
    path: str = typer.Argument(..., help="specs 路徑（檔案或目錄）"),
):
    """讀取 OpenSpec specs 檔案內容。

    此命令讀取並輸出 specs 內容，供 AI 理解場景語義並生成測試程式碼。

    範例：
        ai-dev derive-tests specs/                     # 讀取目錄下所有 specs
        ai-dev derive-tests specs/feature/spec.md     # 讀取單一 spec 檔案
    """
    # 檢查路徑是否存在
    p = Path(path)
    if not p.exists():
        print(f"Error: 路徑不存在: {path}", file=sys.stderr)
        raise typer.Exit(code=1)

    # 找到 spec 檔案
    spec_files = find_spec_files(path)

    if not spec_files:
        print(f"Error: 找不到 .md 檔案: {path}", file=sys.stderr)
        raise typer.Exit(code=1)

    # 輸出每個檔案的內容
    for spec_file in spec_files:
        console.print(f"\n--- {spec_file} ---\n")
        content = spec_file.read_text(encoding="utf-8")
        console.print(content)

    # 成功
    raise typer.Exit(code=0)
