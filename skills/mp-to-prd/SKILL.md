---
name: mp-to-prd
description: |
  將既有對話與儲存庫脈絡整理成 PRD 或 OpenSpec proposal 前置素材。
  Use when: 使用者要把已討論內容整理成需求摘要、PRD、或進入 OpenSpec 前的 brief；
  不適用於重新訪談使用者。
---

# mp-to-prd

本技能從既有脈絡合成需求文件。不要重新開一輪完整訪談；只有缺少關鍵決策時才提出少量問題。

## 啟動時先讀

- `docs/agents/mp-workflow.md`
- `docs/agents/issue-tracker.md`
- `docs/agents/domain.md`
- 相關 `CONTEXT.md`、`CONTEXT-MAP.md`、ADR
- 已有的對話、issue、OpenSpec artifact 或本地文件

## Seam 先行

變更涉及可測試的程式邏輯時，輸出文件前先確認測試 seam（可觀察行為的公開邊界）：

1. 提出建議的 seam：優先沿用程式碼中既有的 seam；需要新 seam 時提在最高可行位置。
   seam 越少越好，理想是一個。
2. 與使用者核對 seam 是否符合預期，核對後才輸出文件。
3. 文件的 Verification Direction / Testing Decisions 引用已確認的 seam。

純文件、配置或無程式邏輯的變更跳過本節。

## 輸出用途

可輸出兩種形狀：

### OpenSpec brief

用於後續 `openspec-propose` 或 `openspec-new-change`。

```markdown
## Problem

## Intended Outcome

## Known Decisions

## Open Questions

## Out of Scope

## Verification Direction
```

### PRD 摘要

用於產品或跨角色對齊。

```markdown
## Problem Statement

## Solution

## User Stories

## Implementation Decisions

## Testing Decisions

## Out of Scope

## Further Notes
```

## 規則

- 使用專案既有語言，不自行發明新術語。
- 不把容易過期的程式碼片段放進 PRD。
- 不強制每個需求都建立 PRD；若 OpenSpec proposal 已足夠，輸出 brief 即可。
- 若資訊不足，列在 Open Questions，不要假裝已決定。

## 下一步

完成後建議：

- 進入 `mp-to-issues` 切成垂直切片。
- 或進入 `openspec-propose` 建立正式 change。
