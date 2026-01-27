## 1. 擴充 TestRunner 架構

- [x] 1.1 在 TestRunner ABC 新增 `run_with_coverage()` 和 `is_coverage_available()`
- [x] 1.2 在 PythonTestRunner 實作 `run_with_coverage()` 方法
- [x] 1.3 使用 `--cov-report=term-missing` 格式輸出

## 2. 建立 CLI 命令

- [x] 2.1 建立 `script/commands/coverage.py`
- [x] 2.2 實作 `coverage` 命令（輸出原始結果）
- [x] 2.3 整合到 `script/main.py`

## 3. 建立 Claude Code 命令

- [x] 3.1 建立 `commands/claude/custom-skills-coverage.md`
- [x] 3.2 定義 AI 分析流程（整體摘要、各檔案覆蓋率、改善建議）

## 4. 驗證

- [x] 4.1 測試 `ai-dev coverage` 基本執行
- [x] 4.2 測試 --source 選項
- [x] 4.3 測試 pytest-cov 未安裝時的錯誤處理

## 5. 架構重構（v2）

- [x] 5.1 移除 CoverageResult, FileCoverage dataclass
- [x] 5.2 移除 `_parse_coverage_json()` 解析邏輯
- [x] 5.3 移除 Rich 表格格式化和 threshold/fail-under 選項
- [x] 5.4 強化 Claude Code 命令的 AI 分析 prompt
- [x] 5.5 更新 design.md 反映新架構
