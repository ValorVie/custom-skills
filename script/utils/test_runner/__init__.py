"""測試執行器模組。

提供可擴充的測試執行架構，支援多語言測試框架。
腳本負責執行命令，分析工作交給 AI。
"""

from .base import CommandResult, TestRunner
from .python import PythonTestRunner
from .detector import detect_test_runner

__all__ = [
    "CommandResult",
    "TestRunner",
    "PythonTestRunner",
    "detect_test_runner",
]
