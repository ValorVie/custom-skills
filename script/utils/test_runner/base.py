"""測試執行器抽象基類。"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class CommandResult:
    """命令執行結果。"""

    output: str
    """命令輸出（stdout + stderr）"""

    exit_code: int
    """Exit code"""

    @property
    def success(self) -> bool:
        """是否成功執行（exit code 為 0）。"""
        return self.exit_code == 0


class TestRunner(ABC):
    """測試執行器抽象基類。

    所有語言的測試執行器都應繼承此類別。
    負責執行測試命令並回傳原始輸出，分析工作交給 AI。
    """

    @abstractmethod
    def run(
        self,
        path: str | None = None,
        verbose: bool = False,
        fail_fast: bool = False,
        keyword: str | None = None,
    ) -> CommandResult:
        """執行測試。

        Args:
            path: 測試路徑（檔案或目錄）
            verbose: 是否顯示詳細輸出
            fail_fast: 是否在第一個失敗後停止
            keyword: 過濾測試名稱的關鍵字

        Returns:
            CommandResult 包含原始輸出和 exit code
        """
        pass

    @abstractmethod
    def run_with_coverage(
        self,
        path: str | None = None,
        source: str | None = None,
    ) -> CommandResult:
        """執行覆蓋率分析。

        Args:
            path: 測試路徑（檔案或目錄）
            source: 原始碼路徑

        Returns:
            CommandResult 包含原始輸出和 exit code
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """檢查測試框架是否可用。"""
        pass

    @abstractmethod
    def is_coverage_available(self) -> bool:
        """檢查覆蓋率工具是否可用。"""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """測試框架名稱。"""
        pass

    @property
    @abstractmethod
    def install_hint(self) -> str:
        """安裝提示訊息。"""
        pass

    @property
    @abstractmethod
    def coverage_install_hint(self) -> str:
        """覆蓋率工具安裝提示。"""
        pass
