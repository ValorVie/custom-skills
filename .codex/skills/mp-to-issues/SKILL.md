---
name: mp-to-issues
description: |
  將 plan、PRD、OpenSpec change 或對話摘要切成可驗證的垂直切片。
  Use when: 需要把大型需求拆成 OpenSpec tasks、GitHub issue draft、
  或本地 Markdown 工作項目；不適用於直接 TDD 實作。
---

# mp-to-issues

本技能把已成形的需求拆成可接手、可驗證的工作項目。它不負責正式規格審核，也不取代 `openspec-*`。

## 啟動時先讀

- `docs/agents/mp-workflow.md`
- `docs/agents/issue-tracker.md`
- `docs/agents/triage-states.md`
- `docs/agents/domain.md`
- 若來源是 OpenSpec change，讀該 change 的 proposal、design、spec、tasks。
- 若存在 `CONTEXT.md`、`CONTEXT-MAP.md` 或 ADR，讀相關部分。

## 切片規則

每個工作項目都必須是垂直切片：

- 走過受影響系統的完整窄路徑。
- 完成後能獨立展示或驗證。
- 有明確驗證條件。
- 盡量小，但不能小到只剩單一水平層。

避免水平切片，例如只改 schema、只改 UI、只寫文件而沒有可驗證閉環。

## AFK / HITL

每個切片必須標示：

- `AFK`：範圍清楚、驗證明確、沒有未決的人類判斷，可交給 agent。
- `HITL`：需要產品判斷、外部存取、人工審核或設計決策。

預設盡量切成 `AFK`。若無法做到，要寫出阻塞原因。

## 輸出模式

依 `docs/agents/issue-tracker.md` 或使用者指定選擇輸出。

### OpenSpec tasks

來源是 OpenSpec change 時優先使用。格式：

```markdown
- [ ] N.M [AFK] 動詞開頭的任務描述
  - 驗證：可執行或可檢查的條件
```

保持依賴順序：阻塞者在前，被阻塞者在後。

### GitHub issue draft

只輸出草稿，除非使用者明確要求建立 issue。

每個草稿包含：

- Title
- Type：`AFK` 或 `HITL`
- Parent
- What to build
- Acceptance criteria
- Blocked by

### 本地 Markdown

用於沒有外部 tracker 的儲存庫。預設輸出到 `.scratch/<topic>/` 或使用者指定路徑。

## 完成條件

- 每個切片都有驗證條件。
- 每個切片都有 `AFK` 或 `HITL`。
- 已指出依賴順序。
- 不直接修改父需求或關閉父 issue。
