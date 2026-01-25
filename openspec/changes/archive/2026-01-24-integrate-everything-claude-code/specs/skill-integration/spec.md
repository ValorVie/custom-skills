# Spec Delta: Skill Integration

## ADDED Requirements

### Requirement: Everything Claude Code 靜態整合

系統 SHALL 支援從 everything-claude-code 專案選擇性整合資源。

#### Scenario: 靜態整合資源

- **GIVEN** 已評估 ecc 資源的整合價值
- **WHEN** 執行整合作業
- **THEN** 將選定資源轉換為 UDS 格式並直接 commit 到本專案
- **AND** 在檔案頭部加入 upstream 標注

#### Scenario: Upstream 追蹤

- **GIVEN** 已建立 `upstream/` 目錄
- **WHEN** 整合 ecc 資源
- **THEN** 在 `upstream/sources.yaml` 記錄來源資訊
- **AND** 在 `upstream/ecc/mapping.yaml` 記錄檔案對照

#### Scenario: 上游變更檢查

- **GIVEN** 已記錄 `last_synced_commit`
- **WHEN** 上游有新 commits
- **THEN** 產生差異報告供人工審核
- **AND** 透過 OpenSpec 建立變更提案

### Requirement: Hooks Python 實作

系統 SHALL 使用 Python 實作 Hooks 以確保跨平台相容。

#### Scenario: Memory Persistence Hook

- **WHEN** 需要記憶持久化功能
- **THEN** 使用 `hooks/memory_persistence.py` 實作
- **AND** 相容 Windows/macOS/Linux

#### Scenario: Strategic Compact Hook

- **WHEN** 需要 Token 優化功能
- **THEN** 使用 `hooks/strategic_compact.py` 實作
- **AND** 相容 Windows/macOS/Linux

### Requirement: UDS 格式統一

所有整合的資源 SHALL 遵循 UDS 格式規範。

#### Scenario: Agent 格式轉換

- **GIVEN** ecc agent 使用其原生格式
- **WHEN** 整合到本專案
- **THEN** 轉換為 UDS AGENT.md 格式（含 YAML frontmatter）
- **AND** 翻譯為繁體中文

#### Scenario: Attribution 標注

- **WHEN** 整合任何 ecc 資源
- **THEN** 在檔案頭部加入來源標注
- **AND** 包含 Upstream、Source URL、Synced Date、Commit、License
