---
name: mp-setup-matt-pocock-skills
description: |
  建立 MP 工作入口層的專案規則。Use when: 首次導入 mattpocock/skills 改寫版、
  需要設定 docs/agents/、需要讓 Claude Code 與 Codex 共同讀取 issue tracker、
  triage states、domain docs 規則，或 mp-* 技能缺少專案入口脈絡。
---

# mp-setup-matt-pocock-skills

本技能用來建立儲存庫層級的 MP 工作入口規則。它不是用來執行功能實作，也不是用來取代 `openspec-*` 或 `superpowers:*`。

## 使用前提

- 先讀取並遵守 `auto-skill`。
- 先檢查現有檔案，不可直接覆寫使用者內容。
- 若同時存在 `CLAUDE.md` 與 `AGENTS.md`，兩者都要更新，但只放入口提示。
- 共同規則一律放在 `docs/agents/`。

## 探查

開始前先讀取：

- `git remote -v`
- `CLAUDE.md`
- `AGENTS.md`
- `docs/agents/`
- `CONTEXT.md`
- `CONTEXT-MAP.md`
- `docs/adr/`
- `openspec/`
- `.scratch/`

輸出你看到的現況：已存在、缺少、可能衝突。

## 三個決策

一次只問一個決策問題。每個問題都要附上你的建議與理由。

### 1. 工作項目出口

先判斷此儲存庫實際追蹤工作的地方。

預設建議順序：

1. 若正在處理正式變更，優先使用 OpenSpec `tasks.md`。
2. 若使用者明確要 GitHub issue，輸出 GitHub issue draft。
3. 若沒有外部 tracker，輸出本地 Markdown。

記錄到 `docs/agents/issue-tracker.md`。

### 2. 任務分流狀態

MP 使用固定狀態模型，不綁定外部 label：

- `needs-triage`
- `needs-info`
- `ready-for-agent`
- `ready-for-human`
- `wontfix`

若外部系統有既有 label，只在文件中記錄 mapping，不改變 canonical state 名稱。

記錄到 `docs/agents/triage-states.md`。

### 3. 專案語言與決策文件

確認此儲存庫是 single-context 還是 multi-context：

- single-context：根目錄 `CONTEXT.md`，決策在 `docs/adr/`。
- multi-context：根目錄 `CONTEXT-MAP.md` 指向各子 context。

檔案採 lazy creation。只有在真的沉澱術語或 ADR 時才建立 `CONTEXT.md` 或 `docs/adr/`。

記錄到 `docs/agents/domain.md`。

## 寫入規則

必須建立或更新：

- `docs/agents/issue-tracker.md`
- `docs/agents/triage-states.md`
- `docs/agents/domain.md`
- `docs/agents/mp-workflow.md`

若 `CLAUDE.md` 存在，加入或更新「MP 工作入口層」區塊。若 `AGENTS.md` 存在，也做同樣更新。

入口區塊只應包含：

- MP 工作入口層是什麼。
- 何時使用 `mp-*`。
- 共同規則位於 `docs/agents/`。
- `openspec-*` 與 `superpowers:*` 仍保留原職責。

不得在 `CLAUDE.md` 與 `AGENTS.md` 各自維護不同版本的詳細規則。

## 完成條件

- `docs/agents/` 四份文件存在。
- `CLAUDE.md` 與 `AGENTS.md` 若存在，都指向 `docs/agents/`。
- 沒有直接安裝或複製整包上游 `mattpocock/skills`。
- 沒有覆寫 `openspec-*` 或 `superpowers:*`。
