# hook-testing Specification

## Purpose

提供 ecc-hooks 的單元測試框架，支援 mock 策略和完整的測試覆蓋。

## Requirements

### Requirement: Hook 測試框架

系統 SHALL 提供 hooks 腳本的單元測試框架。

#### Scenario: 測試框架設定

- **WHEN** 設定測試環境
- **THEN** 使用 Jest 作為測試框架
- **AND** 測試檔案位於 `plugins/ecc-hooks/tests/code-quality/`
- **AND** 測試檔案命名為 `<script-name>.test.js`

#### Scenario: 測試執行

- **WHEN** 執行測試
- **THEN** 使用 `npm test` 或 `jest` 命令
- **AND** 支援單一檔案測試 `jest <file>.test.js`
- **AND** 輸出測試覆蓋率報告

### Requirement: Mock 策略

系統 SHALL 使用 mock 來隔離外部依賴。

#### Scenario: Mock 外部工具

- **WHEN** 測試依賴外部工具的 hook（Prettier、tsc、PHPStan 等）
- **THEN** mock `child_process.execSync`
- **AND** 模擬工具成功執行的回應
- **AND** 模擬工具失敗的回應
- **AND** 模擬工具不存在的情況

#### Scenario: Mock 檔案系統

- **WHEN** 測試依賴檔案讀寫的 hook
- **THEN** mock `fs.existsSync`
- **AND** mock `fs.readFileSync`
- **AND** 模擬檔案存在與不存在的情況
- **AND** 模擬檔案內容

#### Scenario: Mock stdin/stdout

- **WHEN** 測試 hook 的輸入輸出
- **THEN** 模擬 `process.stdin` 輸入 JSON 資料
- **AND** 捕捉 `console.log` 輸出（stdout）
- **AND** 捕捉 `console.error` 輸出（stderr）

### Requirement: 測試覆蓋

系統 SHALL 為每個獨立腳本提供完整的測試覆蓋。

#### Scenario: 格式化 hooks 測試

- **WHEN** 測試格式化相關 hooks
- **THEN** 測試工具存在時正確執行格式化
- **AND** 測試工具不存在時靜默跳過
- **AND** 測試格式化失敗時不中斷流程
- **AND** 確保原始輸入正確輸出

#### Scenario: 靜態分析 hooks 測試

- **WHEN** 測試靜態分析相關 hooks
- **THEN** 測試配置檔存在時執行分析
- **AND** 測試配置檔不存在時跳過
- **AND** 測試有錯誤時輸出警告
- **AND** 測試錯誤輸出限制在 10 行

#### Scenario: Debug 警告 hooks 測試

- **WHEN** 測試 debug 程式碼警告 hooks
- **THEN** 測試偵測到 debug 程式碼時輸出警告
- **AND** 測試無 debug 程式碼時無輸出
- **AND** 測試警告顯示行號和內容
- **AND** 測試警告限制在 5 行

#### Scenario: Stop hook 測試

- **WHEN** 測試 Stop hook
- **THEN** 測試非 Git 目錄時靜默跳過
- **AND** 測試 Git 目錄中檢查修改的檔案
- **AND** 測試多語言 debug 程式碼偵測
- **AND** 測試 Python 註解排除邏輯

### Requirement: 測試輔助函式

系統 SHALL 提供測試輔助函式簡化測試撰寫。

#### Scenario: 輸入模擬

- **WHEN** 測試需要模擬 Claude Code hook 輸入
- **THEN** 提供 `createMockInput(filePath)` 函式
- **AND** 回傳符合 hook 協議的 JSON 物件

#### Scenario: 腳本執行

- **WHEN** 測試需要執行腳本並取得輸出
- **THEN** 提供 `runScript(scriptPath, input)` 函式
- **AND** 回傳 `{ stdout, stderr, exitCode }`
