# MP 工作入口層

說明本 repo 如何使用 mp-* skills 作為工作入口層，以及與其他 skill 家族的分工。

## 角色定位

MP 工作入口層處理「需求進入工程流程之前」的階段：

- 把模糊需求壓成專案語言（`mp-grill-with-docs`）。
- 將既有討論整理成 PRD 或 OpenSpec 前置素材（`mp-to-prd`）。
- 把工作項目分流為 canonical triage state（`mp-triage`）。
- 將討論轉成可追蹤的 issue / task（`mp-to-issues`）。
- 找出架構摩擦並提出 OpenSpec 候選（`mp-improve-codebase-architecture`）。
- 建立或維護本入口層自身（`mp-setup-matt-pocock-skills`）。

## 何時使用

- 需求語意未對齊。
- 還沒進入 OpenSpec proposal 但已有討論。
- 工作項目堆積、需要分流。
- 想 stress-test 一個 plan 而不是直接動手。

## 何時 **不** 使用

- 已經有清楚 spec、要直接實作 → 改用 `openspec-apply-change` / `superpowers:executing-plans` / `superpowers:test-driven-development`。
- 要除錯 → `superpowers:systematic-debugging`。
- 要做 code review → `code-review` 或語言對應的 reviewer skill。

## 與其他家族的邊界

| 家族 | 職責 |
|------|------|
| `mp-*` | 需求對齊、分流、入口轉譯。**不**寫實作程式碼。 |
| `openspec-*` | 規格化變更、apply、verify、archive。 |
| `superpowers:*` | 開發紀律：plan、TDD、debug、review、worktree。 |

如果 mp-* skill 開始要求修改實作程式碼，停下來，改交棒給 openspec-* 或 superpowers:*。

## 共同規則位置

- `docs/agents/issue-tracker.md`：canonical 出口。
- `docs/agents/triage-states.md`：canonical 狀態與外部 mapping。
- `docs/agents/domain.md`：context 模型與 lazy creation 規則。
- 本檔：MP 入口層的職責與邊界。

## 上游

mp-* skills 改寫自 `mattpocock/skills`，但**不**整包安裝上游。每個 mp-* skill 的內容以本 repo 版本為 canonical。
