# opencode-tools Specification

## Purpose
TBD

## Requirements

### Requirement: run-tests 自訂工具

系統 SHALL 在 `.opencode/tools/` 提供 `run-tests.ts` 自訂工具，自動偵測專案的測試框架並執行測試。

#### Scenario: 自動偵測套件管理器
- **WHEN** 使用者呼叫 run-tests 工具
- **THEN** 工具 SHALL 偵測專案使用的套件管理器（npm / pnpm / yarn / bun）
- **THEN** 工具 SHALL 使用偵測到的套件管理器執行測試命令

#### Scenario: 自動偵測測試框架
- **WHEN** 使用者呼叫 run-tests 工具
- **THEN** 工具 SHALL 偵測專案使用的測試框架（jest / vitest / mocha / pytest）
- **THEN** 工具 SHALL 使用對應的框架命令執行測試

#### Scenario: 支援覆蓋率和監控模式
- **WHEN** 使用者呼叫 run-tests 並指定 coverage 或 watch 參數
- **THEN** 工具 SHALL 在測試命令中加入對應的 flag

### Requirement: check-coverage 自訂工具

系統 SHALL 在 `.opencode/tools/` 提供 `check-coverage.ts` 自訂工具，分析測試覆蓋率。

#### Scenario: 覆蓋率報告解析
- **WHEN** 使用者呼叫 check-coverage 工具
- **THEN** 工具 SHALL 解析覆蓋率報告並輸出摘要
- **THEN** 摘要 SHALL 包含行覆蓋率、分支覆蓋率、函式覆蓋率

#### Scenario: 覆蓋率閾值檢查
- **WHEN** 使用者指定覆蓋率閾值
- **THEN** 工具 SHALL 比對實際覆蓋率與閾值
- **THEN** 未達閾值 SHALL 回報失敗並列出未覆蓋的檔案

### Requirement: security-audit 自訂工具

系統 SHALL 在 `.opencode/tools/` 提供 `security-audit.ts` 自訂工具，執行安全性掃描。

#### Scenario: 依賴漏洞掃描
- **WHEN** 使用者呼叫 security-audit 工具
- **THEN** 工具 SHALL 執行套件管理器的 audit 命令（npm audit / pnpm audit 等）
- **THEN** 工具 SHALL 輸出漏洞摘要和嚴重程度分類

#### Scenario: Secret 掃描
- **WHEN** 使用者呼叫 security-audit 工具
- **THEN** 工具 SHALL 掃描專案中的潛在 secret（API key、密碼等）
- **THEN** 若發現 SHALL 列出檔案路徑和匹配 pattern
