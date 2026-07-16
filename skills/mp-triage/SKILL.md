---
name: mp-triage
description: |
  以 tracker 無關的狀態模型分流工作項目。Use when: 需要判斷 issue、
  OpenSpec task 或本地 Markdown 是否 ready-for-agent、ready-for-human、
  needs-info、needs-triage 或 wontfix。
---

# mp-triage

本技能判斷工作項目能否交給 agent 執行。它使用固定狀態模型，
不綁定 Beads、GitHub label、OpenSpec checkbox 或本地 Markdown 格式。

## 啟動時先讀

- `docs/agents/triage-states.md`
- `docs/agents/issue-tracker.md`
- `docs/agents/domain.md`
- 目標工作項目的完整內容與既有 triage notes
- 相關 `CONTEXT.md`、`CONTEXT-MAP.md`、ADR 與程式碼

## 狀態模型

每個工作項目只能有一個主要狀態：

- `needs-triage`：需要維護者初步判斷。
- `needs-info`：資訊不足，需回問具體問題。
- `ready-for-agent`：範圍、驗證、依賴都清楚，agent 可自主處理。
- `ready-for-human`：任務有效，但需要人類判斷、外部權限、人工審核或高風險決策。
- `wontfix`：明確不處理，需記錄原因。

可另外標示類別：

- `bug`
- `enhancement`
- `docs`
- `chore`

## Beads 映射

當 `docs/agents/issue-tracker.md` 指定 Beads 為 canonical 時，同時輸出 triage label 與 status：

| 建議狀態 | Beads label | Beads status |
| --- | --- | --- |
| `needs-triage` | `needs-triage` | `blocked` |
| `needs-info` | `needs-info` | `blocked` |
| `ready-for-agent` | `ready-for-agent` | `open` |
| `ready-for-human` | `ready-for-human` | `blocked` |
| `wontfix` | `wontfix` | `closed`，且必須附原因 |

改變狀態時先移除其他 canonical triage label，確保每張 Bead 最多一個。
Dependency blocking 仍以 Beads dependency graph 為準。

## 分流流程

1. 讀完整工作項目。
2. 讀既有 triage notes，避免重問已解決問題。
3. 若是 bug，先嘗試從描述、程式碼與測試建立可重現判斷。
4. 判斷是否有未決的人類決策。
5. 給出狀態建議與理由。
6. 只有在使用者同意時，才更新外部 tracker 或文件。

## 輸出格式

```markdown
## Triage

**建議狀態：** ready-for-agent
**類別：** enhancement
**Beads label：** ready-for-agent
**Beads status：** open

**理由：**
- 範圍清楚。
- 驗證條件可由測試或文件檢查完成。
- 沒有外部權限或產品判斷阻塞。

**下一步：**
- 交給 agent 執行。
```

若狀態是 `needs-info`，問題必須具體、可回答，不可只寫「請提供更多資訊」。

## 出口

- Beads：輸出 label／status／notes 更新建議；只有使用者或儲存庫規則已授權時才執行 `bd update`／`bd label`。
- OpenSpec：更新或建議更新 `tasks.md` 的狀態註記。
- GitHub：輸出 label / comment 草稿；除非使用者明確要求，不直接呼叫 `gh`。
- 本地 Markdown：更新對應文件中的 triage 區塊。
