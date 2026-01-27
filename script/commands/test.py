"""測試執行命令。"""

import sys
import typer
from pathlib import Path

from ..utils.test_runner import detect_test_runner

def test(
    path: str = typer.Argument(None, help="測試路徑（檔案或目錄）"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="顯示詳細輸出"),
    fail_fast: bool = typer.Option(False, "--fail-fast", "-x", help="失敗時立即停止"),
    keyword: str = typer.Option(None, "-k", help="過濾測試名稱"),
):
    """執行測試並輸出原始結果。

    自動偵測專案的測試框架並執行測試。
    目前支援 Python (pytest)。

    範例：
        ai-dev test                    # 執行所有測試
        ai-dev test tests/             # 執行指定目錄
        ai-dev test -v                 # 詳細輸出
        ai-dev test -x                 # 失敗即停
        ai-dev test -k "test_name"     # 過濾測試
    """
    project_path = Path.cwd()

    # 偵測測試框架
    runner = detect_test_runner(project_path)
    if runner is None:
        print("Error: 無法偵測測試框架", file=sys.stderr)
        print("支援的框架：pytest (Python)", file=sys.stderr)
        raise typer.Exit(code=1)

    # 檢查框架是否可用
    if not runner.is_available():
        print(f"Error: {runner.name} 未安裝", file=sys.stderr)
        print(f"安裝指令：{runner.install_hint}", file=sys.stderr)
        raise typer.Exit(code=1)

    # 執行測試
    result = runner.run(
        path=path,
        verbose=verbose,
        fail_fast=fail_fast,
        keyword=keyword,
    )

    # 輸出原始結果
    print(result.output)

    # 回傳 exit code
    raise typer.Exit(code=result.exit_code)
