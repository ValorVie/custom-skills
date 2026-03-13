"""覆蓋率分析命令。"""

import sys
from pathlib import Path

import typer

from ..utils.test_runner import detect_test_runner, PythonTestRunner


def _normalize_coverage_source(source: str | None) -> str | None:
    """將不穩定的單檔案來源收斂成 pytest-cov 較穩定的父目錄。"""
    if not source:
        return None

    source_path = Path(source)
    if source_path.is_file():
        normalized = str(source_path.parent) or "."
        typer.echo(
            f"Info: 偵測到單一檔案路徑，coverage 將改用父目錄：{normalized}"
        )
        return normalized

    return source


def coverage(
    path: str = typer.Argument(None, help="測試路徑（檔案或目錄）"),
    source: str = typer.Option(None, "--source", "-s", help="模組名稱或目錄"),
):
    """執行覆蓋率分析並輸出原始結果。

    使用 pytest-cov 執行測試並生成覆蓋率報告。

    範例：
        ai-dev coverage                      # 分析整個專案
        ai-dev coverage --source script/     # 僅分析指定目錄
        ai-dev coverage --source script.commands  # 僅分析指定模組
    """
    project_path = Path.cwd()

    # 偵測測試框架
    runner = detect_test_runner(project_path)
    if runner is None:
        print("Error: 無法偵測測試框架", file=sys.stderr)
        print("支援的框架：pytest (Python)", file=sys.stderr)
        raise typer.Exit(code=1)

    # 目前只支援 Python
    if not isinstance(runner, PythonTestRunner):
        print("Error: 覆蓋率分析目前僅支援 Python", file=sys.stderr)
        raise typer.Exit(code=1)

    # 檢查 pytest 是否可用
    if not runner.is_available():
        print(f"Error: {runner.name} 未安裝", file=sys.stderr)
        print(f"安裝指令：{runner.install_hint}", file=sys.stderr)
        raise typer.Exit(code=1)

    # 檢查 pytest-cov 是否可用
    if not runner.is_coverage_available():
        print("Error: pytest-cov 未安裝", file=sys.stderr)
        print(f"安裝指令：{runner.coverage_install_hint}", file=sys.stderr)
        raise typer.Exit(code=1)

    # 執行覆蓋率分析
    result = runner.run_with_coverage(
        path=path,
        source=_normalize_coverage_source(source),
    )

    # 輸出原始結果
    print(result.output)

    # 回傳 exit code
    raise typer.Exit(code=result.exit_code)
