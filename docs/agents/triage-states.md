# Triage States

MP 工作入口層使用固定狀態模型，不綁定外部 label 名稱。

## Canonical 狀態

| 狀態 | 意義 |
| --- | --- |
| `needs-triage` | 尚未分流。預設新工作項目都從這裡開始。 |
| `needs-info` | 已分流但缺資訊，無法開工。等待提問者或關係人補齊。 |
| `ready-for-agent` | 條件齊全，AI agent 可直接執行。 |
| `ready-for-human` | 條件齊全，但需要人類判斷或操作。 |
| `wontfix` | 確認不做。需附原因。 |

## Mapping 規則

外部系統若已有 label（如 GitHub issue 的 `bug`、`enhancement` 等），**不改變** canonical 狀態名稱。
僅在本檔附加 mapping 表，並由 mp-triage 等 skill 對外做轉譯。

### Beads mapping（canonical 執行狀態）

每張 Bead 必須至多有一個 canonical triage label。Triage label 表示能否交棒，Beads status 表示執行生命週期：

| Canonical label | Beads status | 行為 |
| --- | --- | --- |
| `needs-triage` | `blocked` | 等待維護者分流，不進入 `bd ready` |
| `needs-info` | `blocked` | 等待補充資訊，不進入 `bd ready` |
| `ready-for-agent` | `open` | 無 blocking dependency 時可由 `bd ready` 認領 |
| `ready-for-human` | `blocked` | 等待人類判斷或操作，以 label 查詢 |
| `wontfix` | `closed` | 關閉並記錄原因 |

依賴造成的阻擋使用 `bd dep add <blocked> <blocker>`，不要以 triage label 取代依賴圖。

### GitHub Issues 來源 mapping

| 外部 label / 狀態 | canonical |
| --- | --- |
| 無 label、剛開的 issue | `needs-triage` |
| `question`、待補資訊註解 | `needs-info` |
| `good first issue`、有完整重現步驟 | `ready-for-agent` |
| 需設計討論、需 maintainer 決策 | `ready-for-human` |
| `wontfix`、closed-not-planned | `wontfix` |

### OpenSpec tasks.md mapping

| 來源 | canonical |
| --- | --- |
| 新建 change，task 未開展 | `needs-triage` 或 `ready-for-agent`（視描述完整度） |
| task 標註缺資訊 | `needs-info` |
| task 已具足細節、有驗收條件 | `ready-for-agent` |
| task 標註需人類決策 | `ready-for-human` |
| change 標註 abandoned / archived | `wontfix` |

## 使用建議

- 新工作預設 `needs-triage`／`blocked`，由 mp-triage 同時改寫 label 與 status。
- 改變 triage state 時先移除舊的 canonical label，確保最多只有一個。
- `ready-for-agent` 仍可能被 dependency 阻擋；是否可開工一律以 `bd ready` 為準。
- 不要在 canonical state 之外新增中間狀態。若覺得不夠用，先檢視是否其實是描述不清，而非缺狀態。

## 輕量軌分流檢查

mp-triage 建議某工作項目走輕量軌（不開 OpenSpec change）時，必須逐項說明
三項準入條件的判斷依據（定義見 `docs/dev-guide/workflow/DEVELOPMENT-WORKFLOW.md`）：

1. 範圍在單一模組或文件群，不影響 `openspec/specs/` 既有規格行為。
2. 單一 session 可完成實作與驗證。
3. 不屬於 `docs/agents/issue-tracker.md` 定義的正式變更。

任一條件不成立 → 改建議 OpenSpec 流程，並說明是哪一項不成立。
