## Why

專案已導入 Beads 作為持久工作追蹤器，但既有文件與 `mp-*` 技能仍把 OpenSpec `tasks.md` 或 GitHub Issues 視為執行狀態來源，造成 `bd ready`、認領、依賴與實際工作流程分裂。現在需要統一權責，讓 Claude Code、Codex 與 MP 工作入口層使用同一套可恢復的執行狀態。

## What Changes

- **BREAKING**：本專案的內部執行狀態、認領、依賴與 ready 判斷改以 Beads 為唯一真實來源。
- OpenSpec `tasks.md` 保留為正式變更的範圍、順序與驗收工件；checkbox 是工件進度鏡像，不再決定代理可否認領。
- GitHub Issues 保留為外部需求、錯誤回報與公開討論入口；進入內部執行後必須建立或連結 Beads 工作項目。
- `mp-to-issues` 新增 Beads issue graph 輸出，並在本專案中優先使用。
- `mp-wayfinder` 改用 tracker 無關模型；本專案以 Beads epic、子工作與 blocking dependency 表示地圖。
- `mp-triage` 新增 Beads label 與執行狀態的映射方式。
- 輕量軌由 GitHub issue 出口改為 Beads 出口。
- 刷新 Claude Code 的 Beads 管理區段，使其與 Codex／`AGENTS.md` 的整合規則一致。
- 既有 active OpenSpec 未完成工作的遷移不納入本變更，另由 Beads 工作 `custom-skills-szw` 追蹤。

## Capabilities

### New Capabilities

- `work-tracking`: 定義 Beads、OpenSpec 與 GitHub 的權責邊界、執行狀態映射、跨代理整合與驗證規則。

### Modified Capabilities

- `mp-workflow-entry-layer`: 調整 `mp-to-issues`、`mp-wayfinder` 與 `mp-triage` 的輸出與 tracker 映射要求。
- `mp-lightweight-track`: 將輕量軌的工作追蹤出口由 GitHub Issues 改為 Beads。

## Impact

- 工作流文件：`docs/agents/issue-tracker.md`、`docs/agents/triage-states.md`、`docs/dev-guide/workflow/DEVELOPMENT-WORKFLOW.md`
- MP 技能：`skills/mp-to-issues/SKILL.md`、`skills/mp-wayfinder/SKILL.md`、`skills/mp-triage/SKILL.md`
- AI 入口設定：`CLAUDE.md` 的 Beads 管理區段
- OpenSpec：新增 `work-tracking` 規格，並修改 `mp-workflow-entry-layer`、`mp-lightweight-track` 規格
- Beads：`custom-skills-3i6` 管理本次執行；`custom-skills-szw` 管理後續 active OpenSpec 遷移
