## MODIFIED Requirements

### Requirement: Memory Persistence Hooks

系統 SHALL 提供記憶持久化 Hook 機制。

#### Scenario: Session Start Hook

- **WHEN** Claude Code 新 Session 開始
- **THEN** 執行 `session-start.py`
- **AND** 載入先前 Session 的 context
- **AND** 偵測專案的 package manager（npm/yarn/pnpm/bun）
- **AND** 將 context 輸出供 Claude 讀取
- **AND** 透過 subprocess 呼叫 Node.js 讀取 session 別名
- **AND** 若有可用別名則顯示最近 5 個別名（名稱與 session 路徑）
- **AND** 若 Node.js 不可用或別名讀取失敗則靜默跳過，不影響現有功能

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
