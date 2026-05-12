## Why

目前 `superpowers` 與 `openspec` 已分別覆蓋任務內執行紀律與正式變更生命週期，但仍缺少一個穩定的「工作入口層」：

- 模糊需求進入 `openspec` 前，缺少強制追問與專案語言校準。
- 大需求可寫成 OpenSpec proposal，但不保證會被切成可驗證的垂直切片。
- 任務是否能交給 agent 執行，缺少跨 Claude Code 與 Codex 共用的狀態模型。
- 架構摩擦常在實作中暴露，但缺少一個只產出候選、不直接重構的回看流程。

`mattpocock/skills` 提供了可參考的技能鏈，但不應整包導入。本 change 將其裁切成本專案的 `mp-*` 工作入口技能，保留 `superpowers` 與 `openspec` 的原職責。

## What Changes

- 新增 MP 工作入口層技能：
  - P0：`mp-setup-matt-pocock-skills`（來源：`setup-matt-pocock-skills`）
  - P0：`mp-grill-with-docs`（來源：`grill-with-docs`）
  - P0：`mp-to-issues`（來源：`to-issues`）
  - P1：`mp-triage`（來源：`triage`）
  - P1：`mp-improve-codebase-architecture`（來源：`improve-codebase-architecture`）
  - P2：`mp-to-prd`（來源：`to-prd`）
- 新增 `docs/agents/` 工作入口規則：
  - `docs/agents/issue-tracker.md`
  - `docs/agents/triage-states.md`
  - `docs/agents/domain.md`
  - `docs/agents/mp-workflow.md`
- 更新 Claude Code 與 Codex 的專案入口文件：
  - `CLAUDE.md`
  - `AGENTS.md`
- 保留既有 `superpowers` 與 `openspec` 工作流，不搬運上游 `tdd`、`diagnose`、`grill-me`、`caveman` 等重疊或非必要技能。
- 補充文件說明 MP 工作入口層與 `openspec`、`superpowers` 的銜接規則。
- 新增 `mattpocock/skills` 上游追蹤資料，讓未來可用固定對照表審核上游更新。

## Capabilities

### New Capabilities

- `mp-workflow-entry-layer`：MP 工作入口層，負責需求追問、專案語言沉澱、垂直切片、任務分流與架構候選回看。

### Modified Capabilities

- `skill-integration`：不直接修改既有 spec；本 change 以新 capability 表達裁切後的工作流能力。

## Impact

- **Skills：**
  - `skills/mp-setup-matt-pocock-skills/`
  - `skills/mp-grill-with-docs/`
  - `skills/mp-to-issues/`
  - `skills/mp-triage/`
  - `skills/mp-improve-codebase-architecture/`
  - `skills/mp-to-prd/`
- **Claude Code 投影：**
  - `.claude/skills/mp-*`
  - `CLAUDE.md`
- **Codex 投影：**
  - `.codex/skills/mp-*`
  - `AGENTS.md`
- **共同文件：**
  - `docs/agents/`
  - `docs/dev-guide/workflow/`
  - `CONTEXT.md`（若尚不存在，僅在 `mp-grill-with-docs` 首次需要沉澱專案語言時建立）
  - `docs/adr/`（僅在符合 ADR 條件時建立）
- **上游追蹤：**
  - `upstream/sources.yaml`
  - `upstream/mattpocock-skills/last-sync.yaml`
  - `upstream/mattpocock-skills/mapping.yaml`
- **驗證：**
  - OpenSpec 驗證
  - skill 結構檢查
  - Claude / Codex 投影檢查
  - 觸發案例檢查
