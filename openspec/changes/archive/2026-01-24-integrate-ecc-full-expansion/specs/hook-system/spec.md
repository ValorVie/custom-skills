## ADDED Requirements

### Requirement: Claude Code Hook 支援

系統 SHALL 提供 Claude Code 事件 Hook 的 Python 實作。

#### Scenario: 支援的 Hook 事件

- **WHEN** Claude Code 觸發事件
- **THEN** 支援 SessionStart 事件
- **AND** 支援 SessionEnd 事件
- **AND** 支援 PreCompact 事件
- **AND** 支援 PreToolUse 事件
- **AND** 支援 PostToolUse 事件
- **AND** 支援 Stop 事件

#### Scenario: Hook 配置格式

- **WHEN** 配置 Hooks
- **THEN** 使用 `hooks.json` 格式
- **AND** 支援 matcher 條件過濾
- **AND** 支援 command 執行腳本

### Requirement: Memory Persistence Hooks

系統 SHALL 提供記憶持久化 Hook 機制。

#### Scenario: Session Start Hook

- **WHEN** Claude Code 新 Session 開始
- **THEN** 執行 `session-start.py`
- **AND** 載入先前 Session 的 context
- **AND** 偵測專案的 package manager（npm/yarn/pnpm/bun）
- **AND** 將 context 輸出供 Claude 讀取

#### Scenario: Session End Hook

- **WHEN** Claude Code Session 結束
- **THEN** 執行 `session-end.py`
- **AND** 儲存當前 Session 狀態
- **AND** 記錄重要的對話摘要
- **AND** 儲存至 `~/.claude/sessions/` 或專案本地 `.claude/`

#### Scenario: Pre-Compact Hook

- **WHEN** Claude Code 即將執行 compact
- **THEN** 執行 `pre-compact.py`
- **AND** 儲存當前狀態快照
- **AND** 記錄 compact 前的關鍵資訊

### Requirement: Strategic Compact Hook

系統 SHALL 提供策略性 context 壓縮建議機制。

#### Scenario: Compact 建議觸發

- **GIVEN** PreToolUse 事件（Edit 或 Write 工具）
- **WHEN** 累計工具調用次數超過閾值（預設 50）
- **THEN** 執行 `suggest-compact.py`
- **AND** 輸出壓縮建議訊息
- **AND** 每 25 次調用後重複提醒

#### Scenario: 可配置閾值

- **WHEN** 設定環境變數 `COMPACT_THRESHOLD`
- **THEN** 使用指定值作為建議閾值
- **AND** 預設值為 50

#### Scenario: 策略性建議時機

- **WHEN** 輸出壓縮建議
- **THEN** 建議在探索完成後、執行前壓縮
- **AND** 建議在完成 milestone 後壓縮
- **AND** 建議在 context 轉換前壓縮

### Requirement: Hook 跨平台相容

所有 Hook 腳本 SHALL 相容 Windows、macOS 和 Linux。

#### Scenario: Python 跨平台執行

- **WHEN** Hook 腳本執行
- **THEN** 使用 Python 標準庫
- **AND** 避免 shell-specific 語法
- **AND** 使用 `pathlib` 處理路徑

#### Scenario: 檔案路徑處理

- **WHEN** 存取檔案路徑
- **THEN** 使用 `os.path` 或 `pathlib`
- **AND** 正確處理 Windows 與 Unix 路徑分隔符

#### Scenario: 環境變數存取

- **WHEN** 讀取環境變數
- **THEN** 使用 `os.environ.get()`
- **AND** 提供合理預設值

### Requirement: Hook 狀態儲存

Hook 系統 SHALL 提供狀態儲存機制。

#### Scenario: 狀態儲存位置

- **WHEN** 儲存 Session 狀態
- **THEN** 優先儲存至專案本地 `.claude/sessions/`
- **AND** 若無專案則儲存至 `~/.claude/sessions/`

#### Scenario: 狀態檔案格式

- **WHEN** 儲存狀態檔案
- **THEN** 使用 JSON 格式
- **AND** 包含時間戳記
- **AND** 包含 Session ID

#### Scenario: 狀態檔案清理

- **WHEN** 狀態檔案過多
- **THEN** 保留最近 10 個 Session 狀態
- **AND** 自動刪除舊的狀態檔案

### Requirement: hooks.json 配置

系統 SHALL 提供 hooks.json 配置範例。

#### Scenario: 配置檔案結構

- **WHEN** 建立 hooks.json
- **THEN** 包含 `$schema` 欄位（驗證用）
- **AND** 包含 `hooks` 物件
- **AND** 按事件類型分組（PreToolUse, PostToolUse, SessionStart 等）

#### Scenario: Hook 定義結構

- **WHEN** 定義單一 Hook
- **THEN** 包含 `matcher` 條件
- **AND** 包含 `hooks` 陣列（執行的 commands）
- **AND** 可選 `description` 說明

#### Scenario: Matcher 條件語法

- **WHEN** 定義 matcher
- **THEN** 支援 `*` 匹配所有
- **AND** 支援 `tool == "Bash"` 工具匹配
- **AND** 支援 `tool_input.file_path matches "*.ts"` 路徑匹配
