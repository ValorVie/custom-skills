## ADDED Requirements

### Requirement: 工作追蹤權責分離

本專案 SHALL 以 Beads 作為執行狀態、認領、依賴、ready 與交接的唯一真實來源，同時保留 OpenSpec 與 GitHub 各自的工件責任。

#### Scenario: 代理選擇可執行工作

- **WHEN** Claude Code、Codex 或其他代理需要選擇下一項工作
- **THEN** 代理 SHALL 使用 `bd ready` 與 `bd show <id>` 判斷可執行性
- **AND** 代理 SHALL 使用 `bd update <id> --claim` 認領工作
- **AND** 代理 SHALL NOT 以 OpenSpec checkbox 或 GitHub issue 狀態取代 Beads 認領

#### Scenario: OpenSpec 正式變更保留工件責任

- **WHEN** 工作採用 OpenSpec 正式變更流程
- **THEN** proposal、design、specs、tasks、verify 與 archive SHALL 由 OpenSpec 管理
- **AND** `tasks.md` checkbox SHALL 表示 change 工件內部進度
- **AND** 需要獨立認領或依賴的切片 SHALL 建立 Beads 工作項目

#### Scenario: GitHub issue 進入內部執行

- **WHEN** 外部 GitHub issue 被接受為內部工作
- **THEN** 系統 SHALL 建立或連結 Beads 工作項目
- **AND** Beads 工作項目 SHALL 保留 GitHub issue 外部引用
- **AND** 後續認領與依賴 SHALL 在 Beads 管理

### Requirement: Triage state 映射到 Beads

本專案 SHALL 以 Beads label 保存 canonical triage state，並以 Beads status 控制代理是否可認領。

#### Scenario: Agent-ready 工作

- **WHEN** 工作被分流為 `ready-for-agent`
- **THEN** 該 Bead SHALL 帶有 `ready-for-agent` label
- **AND** status SHALL 為 `open`
- **AND** 無未完成 blocking dependency 時 SHALL 可由 `bd ready` 查得

#### Scenario: 尚不可交給代理的工作

- **WHEN** 工作被分流為 `needs-triage`、`needs-info` 或 `ready-for-human`
- **THEN** 該 Bead SHALL 帶有對應且唯一的 triage label
- **AND** status SHALL 為 `blocked`
- **AND** 工作 SHALL NOT 出現在 `bd ready`

#### Scenario: 不執行的工作

- **WHEN** 工作被分流為 `wontfix`
- **THEN** 該 Bead SHALL 帶有 `wontfix` label
- **AND** status SHALL 為 `closed`
- **AND** close reason SHALL 說明不執行原因

### Requirement: Claude 與 Codex 使用一致 Beads 規則

Claude Code 與 Codex SHALL 從受管理的入口檔與 hook 載入一致的 Beads 工作流程。

#### Scenario: 整合健康檢查

- **WHEN** 執行 `bd setup claude --check` 與 `bd setup codex --check`
- **THEN** 兩項檢查 SHALL 成功
- **AND** `CLAUDE.md` 與 `AGENTS.md` 的 Beads 管理區段 SHALL 不再顯示 stale
- **AND** SessionStart hook SHALL 注入 `bd prime`

### Requirement: 既有工作遷移分離

本變更 SHALL 不把 active OpenSpec 歷史與未完成工作直接混入規則更新。

#### Scenario: 完成本變更

- **WHEN** 本變更通過驗證
- **THEN** 既有 active OpenSpec 未完成工作遷移 SHALL 由 `custom-skills-szw` 另案追蹤
- **AND** 已完成或已封存的 OpenSpec 歷史 SHALL NOT 被批次匯入 Beads
