# Domain

專案語言與決策文件規則。

## Context 模型

本 repo 為 **single-context**：

- 一個主題（custom-skills，AI 開發工具集合）。
- 不需要 `CONTEXT-MAP.md`。
- 若未來分裂出獨立子領域，再升級為 multi-context。

## Lazy creation 原則

以下檔案僅在實際沉澱出可重用內容時建立，不為了「先有架子」而建立空殼：

- `CONTEXT.md`：專案術語、固定詞彙、不變約束。當術語在多份文件之間出現不一致或誤譯時建立。
- `docs/adr/`：架構決策紀錄。當做出影響後續工作的不可逆決策（路徑結構、發布流程、向上游同步策略等）時建立 ADR。

## 既有對應位置

- 專案總述：`openspec/project.md`
- 規格：`openspec/specs/`
- 開發指南：`docs/dev-guide/`
- 平台限定 skills 副本：`.claude/skills/`、`.codex/skills/`
- skills 主版本：`skills/`

## 維護規則

- 術語、決策一律記錄到 canonical 位置，不在 CLAUDE.md 或 AGENTS.md 內就地展開。
- 若發現規則散落在多處，把細節集中到 `docs/agents/` 或 `openspec/`，於入口檔僅留指向。
