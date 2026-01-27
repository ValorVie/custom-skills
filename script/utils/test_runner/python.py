"""Python (pytest) 測試執行器。"""

import subprocess
import shutil

from .base import TestRunner, CommandResult


class PythonTestRunner(TestRunner):
    """Python pytest 測試執行器。

    負責執行 pytest 命令並回傳原始輸出，分析工作交給 AI。
    """

    @property
    def name(self) -> str:
        return "pytest"

    @property
    def install_hint(self) -> str:
        return "pip install pytest"

    @property
    def coverage_install_hint(self) -> str:
        return "pip install pytest-cov"

    def is_available(self) -> bool:
        """檢查 pytest 是否已安裝。"""
        return shutil.which("pytest") is not None

    def is_coverage_available(self) -> bool:
        """檢查 pytest-cov 是否已安裝。"""
        if not self.is_available():
            return False
        try:
            result = subprocess.run(
                ["pytest", "--co", "-q", "--cov-report="],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return "unrecognized arguments" not in result.stderr
        except Exception:
            return False

    def run(
        self,
        path: str | None = None,
        verbose: bool = False,
        fail_fast: bool = False,
        keyword: str | None = None,
    ) -> CommandResult:
        """執行 pytest 測試。"""
        if not self.is_available():
            return CommandResult(
                output=f"Error: {self.name} 未安裝。請執行: {self.install_hint}",
                exit_code=1,
            )

        cmd = ["pytest", "--tb=short"]

        if verbose:
            cmd.append("-v")

        if fail_fast:
            cmd.append("-x")

        if keyword:
            cmd.extend(["-k", keyword])

        if path:
            cmd.append(path)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
            )
            return CommandResult(
                output=result.stdout + result.stderr,
                exit_code=result.returncode,
            )
        except subprocess.TimeoutExpired:
            return CommandResult(
                output="Error: 測試執行超時（5 分鐘）",
                exit_code=1,
            )
        except Exception as e:
            return CommandResult(
                output=f"Error: {e}",
                exit_code=1,
            )

    def run_with_coverage(
        self,
        path: str | None = None,
        source: str | None = None,
    ) -> CommandResult:
        """執行覆蓋率分析。"""
        if not self.is_available():
            return CommandResult(
                output=f"Error: {self.name} 未安裝。請執行: {self.install_hint}",
                exit_code=1,
            )

        if not self.is_coverage_available():
            return CommandResult(
                output=f"Error: pytest-cov 未安裝。請執行: {self.coverage_install_hint}",
                exit_code=1,
            )

        cov_source = source or "."
        cmd = [
            "pytest",
            f"--cov={cov_source}",
            "--cov-report=term-missing",
        ]

        if path:
            cmd.append(path)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
            )
            return CommandResult(
                output=result.stdout + result.stderr,
                exit_code=result.returncode,
            )
        except subprocess.TimeoutExpired:
            return CommandResult(
                output="Error: 覆蓋率分析超時（5 分鐘）",
                exit_code=1,
            )
        except Exception as e:
            return CommandResult(
                output=f"Error: {e}",
                exit_code=1,
            )
