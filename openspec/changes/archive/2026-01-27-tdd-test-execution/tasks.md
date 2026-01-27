## 1. 建立 TestRunner 抽象架構

- [x] 1.1 建立 `script/utils/test_runner/` 目錄結構
- [x] 1.2 實作 `base.py` - CommandResult dataclass 和 TestRunner ABC
- [x] 1.3 實作 `detector.py` - 框架偵測邏輯

## 2. 實作 PythonTestRunner

- [x] 2.1 實作 `python.py` - PythonTestRunner 類別
- [x] 2.2 實作 `is_available()` - 檢查 pytest 是否安裝
- [x] 2.3 實作 `run()` - 執行 pytest 並回傳原始輸出
- [x] 2.4 實作選項支援（verbose, fail_fast, keyword）

## 3. 建立 CLI 命令

- [x] 3.1 建立 `script/commands/test.py`
- [x] 3.2 實作 `test` 命令（輸出原始結果）
- [x] 3.3 整合到 `script/main.py`

## 4. 建立 Claude Code 命令

- [x] 4.1 建立 `commands/claude/custom-skills-test.md`
- [x] 4.2 定義 AI 分析流程（測試摘要、失敗分析、建議）

## 5. 驗證

- [x] 5.1 測試 `ai-dev test` 基本執行
- [x] 5.2 測試各選項（--verbose, --fail-fast, -k）
- [x] 5.3 測試 pytest 未安裝時的錯誤處理
- [x] 5.4 測試 exit code 正確性

## 6. 架構重構（v2）

- [x] 6.1 移除 TestResult, TestError dataclass（改用 CommandResult）
- [x] 6.2 移除 `_parse_output()`, `_parse_failures()` 解析邏輯
- [x] 6.3 移除 Rich 表格格式化
- [x] 6.4 強化 Claude Code 命令的 AI 分析 prompt
- [x] 6.5 更新 design.md 反映新架構
