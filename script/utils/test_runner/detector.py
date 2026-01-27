"""測試框架偵測。"""

from pathlib import Path

from .base import TestRunner
from .python import PythonTestRunner


def detect_test_runner(project_path: Path | None = None) -> TestRunner | None:
    """偵測專案使用的測試框架。

    Args:
        project_path: 專案路徑，預設為當前目錄

    Returns:
        對應的 TestRunner 實例，或 None 如果無法偵測
    """
    if project_path is None:
        project_path = Path.cwd()

    # Python 專案偵測
    if _is_python_project(project_path):
        return PythonTestRunner()

    # 未來可以加入其他語言的偵測
    # if _is_node_project(project_path):
    #     return NodeTestRunner()

    return None


def _is_python_project(project_path: Path) -> bool:
    """檢查是否為 Python 專案。"""
    # 檢查 pyproject.toml
    if (project_path / "pyproject.toml").exists():
        return True

    # 檢查 pytest.ini
    if (project_path / "pytest.ini").exists():
        return True

    # 檢查 setup.py
    if (project_path / "setup.py").exists():
        return True

    # 檢查 setup.cfg 中的 pytest 設定
    setup_cfg = project_path / "setup.cfg"
    if setup_cfg.exists():
        try:
            content = setup_cfg.read_text()
            if "[tool:pytest]" in content:
                return True
        except Exception:
            pass

    # 檢查 tests 目錄中是否有 Python 測試檔案
    tests_dir = project_path / "tests"
    if tests_dir.exists():
        if any(tests_dir.glob("test_*.py")) or any(tests_dir.glob("*_test.py")):
            return True

    return False
