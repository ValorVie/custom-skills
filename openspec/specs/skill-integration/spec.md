# skill-integration Specification

## Purpose
TBD - created by archiving change integrate-everything-claude-code. Update Purpose after archive.
## Requirements
### Requirement: Everything Claude Code 靜態整合

系統 SHALL 支援從 everything-claude-code 專案選擇性整合資源。

#### Scenario: 靜態整合資源

- **GIVEN** 已評估 ecc 資源的整合價值
- **WHEN** 執行整合作業
- **THEN** 將選定資源複製到 `sources/ecc/` 目錄
- **AND** 保持 ecc 原生格式不轉換
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
- **THEN** 使用 `sources/ecc/hooks/memory-persistence/` 下的 Python 腳本
- **AND** 相容 Windows/macOS/Linux

#### Scenario: Strategic Compact Hook

- **WHEN** 需要 Token 優化功能
- **THEN** 使用 `sources/ecc/hooks/strategic-compact/` 下的 Python 腳本
- **AND** 相容 Windows/macOS/Linux

#### Scenario: Session 狀態持久化

- **WHEN** Session 開始或結束
- **THEN** 使用 `session-start.py` 載入先前 context
- **AND** 使用 `session-end.py` 儲存當前狀態
- **AND** 狀態儲存於 `~/.claude/sessions/` 或專案本地

### Requirement: 原生格式保留

整合的 ecc 資源 SHALL 保持其原生 Claude Code 格式。

#### Scenario: ecc 資源保留原格式

- **GIVEN** ecc 資源使用純 Markdown（無 YAML frontmatter）
- **WHEN** 整合到本專案
- **THEN** 保持原格式不轉換為 UDS 格式
- **AND** 放置於 `sources/ecc/` 目錄

#### Scenario: Attribution 標注

- **WHEN** 整合任何 ecc 資源
- **THEN** 在檔案頭部加入 HTML 註解形式的來源標注
- **AND** 包含 Upstream、Source URL、Synced Date、Commit、License

### Requirement: 優先整合項目完整實作

系統 SHALL 完整實作評估報告中的優先整合項目。

#### Scenario: Hook 機制整合

- **WHEN** 執行 ecc 整合
- **THEN** 包含 memory-persistence hooks（session-start, session-end, pre-compact）
- **AND** 包含 strategic-compact hook（suggest-compact）
- **AND** 包含 hooks.json 配置檔

#### Scenario: Skills 整合

- **WHEN** 執行 ecc 整合
- **THEN** 包含 continuous-learning skill
- **AND** 包含 strategic-compact skill
- **AND** 包含 eval-harness skill
- **AND** 包含 security-review skill
- **AND** 包含 tdd-workflow skill

#### Scenario: Agents 整合

- **WHEN** 執行 ecc 整合
- **THEN** 包含 build-error-resolver agent
- **AND** 包含 e2e-runner agent
- **AND** 包含 doc-updater agent
- **AND** 包含 security-reviewer agent

#### Scenario: Commands 整合

- **WHEN** 執行 ecc 整合
- **THEN** 包含 checkpoint command
- **AND** 包含 build-fix command
- **AND** 包含 e2e command
- **AND** 包含 learn command
- **AND** 包含 test-coverage command
- **AND** 包含 eval command

### Requirement: OpenCode 與 MCP 參考

系統 SHALL 提供 OpenCode 與 MCP 配置參考資源。

#### Scenario: OpenCode 整合說明

- **WHEN** 使用者需要 OpenCode 整合
- **THEN** 在 `sources/ecc/plugins/` 提供整合說明
- **AND** 說明與 Claude Code 的差異

#### Scenario: MCP 配置範例

- **WHEN** 使用者需要 MCP 服務配置
- **THEN** 在 `sources/ecc/mcp-configs/` 提供配置範例
- **AND** 包含常用服務（GitHub, Memory, Context7 等）

### Requirement: TDD 實踐整合

系統 SHALL 整合 ecc TDD 實戰範例作為現有標準的補充。

#### Scenario: TDD 標準擴展

- **GIVEN** 現有 `.standards/test-driven-development.md`
- **WHEN** 需要實戰範例
- **THEN** 新增「實戰範例附錄」章節
- **AND** 連結至 `sources/ecc/skills/tdd-workflow/`

#### Scenario: Mock 範例補充

- **WHEN** 需要具體 Mock 範例
- **THEN** 提供 Supabase/Redis/OpenAI mock 範例連結
- **AND** 來自 ecc tdd-workflow skill

#### Scenario: 測試檔案組織

- **WHEN** 需要測試檔案結構建議
- **THEN** 提供清晰的目錄結構範例連結
- **AND** 來自 ecc tdd-workflow skill

