# Issue Tracker 規則

本文件是 MP 工作入口層判斷工作項目出口的共同真實來源。

## 預設出口

本專案的預設工作出口依情境排序：

1. **OpenSpec tasks**：正式變更、規格驅動工作、需要 proposal/design/spec 驗證時使用。
2. **GitHub issue draft**：需要交給外部 issue tracker 或跨人協作時使用。除非使用者明確要求，不直接建立 issue。
3. **本地 Markdown**：草稿、一次性整理、或不適合進 OpenSpec 的探索工作使用。

## MP 技能使用規則

- `mp-to-issues` 若來源是 OpenSpec change，優先輸出或更新 `tasks.md` 友善格式。
- `mp-triage` 判斷狀態時不依賴外部 label；label 只是狀態的外部映射。
- `mp-to-prd` 可輸出 OpenSpec brief 或 PRD 摘要，不強制發布到 issue tracker。
- 任何外部寫入動作，例如呼叫 `gh issue create`，都需要使用者明確要求。

## OpenSpec tasks 格式

建議每個任務保留可驗證語言：

```markdown
- [ ] N.M [AFK] 建立或更新某個可驗證產物
  - 驗證：執行或檢查某個具體條件
```

`AFK` 表示 agent 可自主處理；`HITL` 表示需要人類判斷、外部權限或人工審核。

## GitHub issue draft 格式

```markdown
## What to build

## Acceptance criteria

- [ ] 可驗證條件

## Blocked by

None

## Triage

State: needs-triage
Type: AFK
```

## 本地 Markdown 格式

預設可放在 `.scratch/<topic>/` 或使用者指定路徑。若該工作會轉成正式變更，應再整理成 OpenSpec change。
