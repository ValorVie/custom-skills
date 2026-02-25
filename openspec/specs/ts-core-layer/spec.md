# ts-core-layer Specification

## Purpose
TypeScript 核心業務邏輯層，提供純函式實作的安裝、狀態檢查、同步引擎、記憶體同步、標準管理和專案管理功能，不依賴任何 UI 模組。

## Requirements
### Requirement: core 層為純函式，不依賴 UI
`src/core/` 下的所有模組 SHALL 為純函式，不依賴 Commander.js、Ink、chalk 或任何輸出格式化。回傳結構化資料，由 CLI 層負責呈現。

#### Scenario: installer 回傳結構化結果
- **WHEN** 呼叫 `runInstall(options)`
- **THEN** 回傳 `InstallResult` 物件，包含 `npmPackages`、`repos`、`skills` 陣列

#### Scenario: core 模組可獨立測試
- **WHEN** 在測試中直接呼叫 core 函式
- **THEN** 不需要 mock 任何 UI 相關模組

### Requirement: status-checker 檢查環境狀態
`src/core/status-checker.ts` SHALL 提供 `checkEnvironment()` 函式，檢查 Git、Node.js、Bun、gh、npm 套件和儲存庫狀態。

#### Scenario: 回傳完整環境狀態
- **WHEN** 呼叫 `checkEnvironment()`
- **THEN** 回傳包含 `git`、`node`、`bun`、`gh`、`npmPackages`、`repos` 的物件

### Requirement: installer 安裝環境
`src/core/installer.ts` SHALL 提供 `runInstall()` 函式，執行完整安裝流程：檢查前置條件、安裝 npm 套件、安裝 Bun 套件、建立目錄、clone 儲存庫、複製 skills。

#### Scenario: 安裝全域 npm 套件
- **WHEN** 執行 `runInstall()`
- **THEN** 使用 `npm install -g` 安裝 `NPM_PACKAGES` 中的所有套件

#### Scenario: Clone 儲存庫
- **WHEN** 執行 `runInstall()` 且儲存庫尚未 clone
- **THEN** clone `REPOS` 中的所有儲存庫到對應目錄

### Requirement: sync-engine 同步目錄
`src/core/sync-engine.ts` SHALL 提供同步引擎，支援目錄同步、git 操作、path normalization。

#### Scenario: 同步本地目錄到 sync-repo
- **WHEN** 呼叫 sync push
- **THEN** 將設定的本地目錄複製到 sync-repo，排除 ignore patterns

#### Scenario: 從 sync-repo 恢復到本地
- **WHEN** 呼叫 sync pull
- **THEN** 將 sync-repo 內容還原到本地目錄

### Requirement: mem-sync 客戶端
`src/core/mem-sync.ts` SHALL 提供 claude-mem HTTP sync 客戶端，支援 register、push、pull、status、reindex。

#### Scenario: 推送 observations
- **WHEN** 呼叫 mem push
- **THEN** 從本地 SQLite 讀取新增的 observations，POST 到 sync server

#### Scenario: 拉取 observations
- **WHEN** 呼叫 mem pull
- **THEN** 從 sync server GET observations，匯入本地 SQLite

#### Scenario: Content hash 去重
- **WHEN** 推送已存在的 observation
- **THEN** server 以 content hash 去重，不產生重複

### Requirement: standards-manager 管理標準 profile
`src/core/standards-manager.ts` SHALL 提供標準 profile 管理，支援 status、list、switch、show、overlaps。

#### Scenario: 切換 profile
- **WHEN** 呼叫 standards switch "level-3"
- **THEN** 更新 .standards/ 目錄內容為對應 profile

### Requirement: project-manager 管理專案模板
`src/core/project-manager.ts` SHALL 提供專案模板管理，支援 init、update。

#### Scenario: 初始化專案
- **WHEN** 呼叫 project init
- **THEN** 將 project-template/ 複製到當前目錄，處理衝突
