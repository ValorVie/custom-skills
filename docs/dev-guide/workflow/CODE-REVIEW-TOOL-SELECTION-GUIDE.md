---
title: 程式碼審查工具選擇指南
type: guide
date: 2026-03-09
author: ValorVie
status: draft
---

# 程式碼審查工具選擇指南

## 概述

這份指南說明如何在不同開發階段選擇合適的 code review 工具、agent 與輔助 skill。適用對象：會使用 Claude Code、custom-skills 與 superpowers 的開發者，以及需要設計 AI 提示詞或工作流程的人。

目標不是找出唯一的「最佳工具」，而是根據場景選對工具，並在適當時機提醒 AI 使用。

## 前置條件

- 你能存取 custom-skills / superpowers 中的 review 相關 skills 與 agents
- 你能提供明確的上下文：需求、task、git diff、PR 或 review comments
- 你知道目前是在「整理程式碼」、「做正式審查」還是「處理審查意見」

## 快速開始

最簡單的選擇規則如下：

```text
剛寫完程式，想先整理但不改行為 → code-simplifier
剛完成某個 task / step，想檢查是否符合需求 → code-reviewer
準備開 PR / merge，想做正式審查 → reviewer
變更高風險，需要完整多段式審查 → code-review.workflow
已收到 review comments，要決定哪些該改 → receiving-code-review
不確定現在該不該 review → requesting-code-review
只想要 checklist / quality gate → code-review-assistant
```

## 工具定位總覽

| 工具 | 類型 | 最佳使用時機 | 核心強項 | 不適合的情境 |
|------|------|-------------|---------|-------------|
| `code-simplifier` | 整理型 agent | 剛完成修改，想先簡化與清理 touched code | 降低複雜度、移除重複、改善可讀性，且以不改變行為為前提 | 不能取代正式需求對齊或 PR 審查 |
| `code-reviewer` | 任務驗收型 agent | 完成一個明確的 step、task、里程碑後 | 檢查需求/計畫對齊、架構、測試、文件與 readiness | 單純小修或只想做 checklist 時太重 |
| `reviewer` | PR / diff reviewer | 開 PR 前、merge 前、做安全與品質審查時 | 專注 diff、品質、安全、maintainability、測試 adequacy | 不擅長驗證「是否符合原始規劃」 |
| `code-review.workflow` | 完整審查流程 | 高風險變更、多人協作、正式 merge gate | 把 context、quality、security/testing、decision 分段處理 | 小改動時成本過高 |
| `code-review-assistant` | checklist / rubric | 想快速對照 review 面向或 pre-commit gate | 10 類 review 維度與 commit 前檢查項目完整 | 不是執行 review 的主 agent |
| `requesting-code-review` | 發起時機 skill | 想判斷現在是否該要求 review | 定義何時應主動 review，避免拖到 merge 前才檢查 | 不會自己完成 technical review |
| `receiving-code-review` | 回應意見 skill | 已收到 reviewer comments 準備修改時 | 強制先驗證再修改，避免盲改與錯改 | 不負責產出原始 review finding |

## 完整流程

### 步驟 1：先判斷目前所處階段

先回答這個問題：你現在是在以下哪一階段？

1. 剛完成編碼，想先整理程式碼
2. 剛完成一個 task / step，想做階段性驗收
3. 準備開 PR 或 merge
4. 變更風險高，需要正式審查流程
5. 已經收到 review comments，準備處理

這一步會直接決定主要工具，不要把所有 review 工具混成同一層。

### 步驟 2：選擇主要工具

#### 場景 A：先整理程式碼，不改行為

適用於：
- 剛完成一段功能
- 發現 touched code 已可運作，但結構不夠乾淨
- 想在正式 review 前先降低 reviewer 噪音

建議使用：`code-simplifier`

```text
請先用 code-simplifier 整理這次 touched code。
限制：不要改變行為、不要擴大 scope、只做簡化與可讀性改善。
```

#### 場景 B：驗收某個已完成的 task / step

適用於：
- 你有 proposal、plan、task、spec 或明確需求敘述
- 你剛完成里程碑，希望確認沒有偏離原意

建議使用：`code-reviewer`

```text
我剛完成 step 3。請用 code-reviewer 根據需求與 git diff 審查：
- What was implemented: ...
- Plan or requirements: ...
- Base SHA: ...
- Head SHA: ...
```

#### 場景 C：PR / merge 前正式審查

適用於：
- 準備發 PR
- 想做 diff 導向的品質、安全、測試審查
- 想得到 blocking / important / suggestion 分級結果

建議使用：`reviewer`

```text
這是本次 PR 的變更範圍。請用 reviewer 做 pre-merge review，
重點看安全、測試、可維護性與明顯的設計問題。
```

#### 場景 D：高風險或正式流程審查

適用於：
- auth、permission、payment、migration、DB schema、核心 API
- 多人協作
- 需要清楚的 decision gate

建議使用：`code-review.workflow`

```text
這次變更風險較高，請按完整 code-review workflow 執行：
1. 先理解 context
2. 再做 quality review
3. 接著做 security/testing review
4. 最後給出 review decision
```

#### 場景 E：處理 reviewer comments

適用於：
- 你已經收到 PR comments 或 inline review
- 你懷疑某些建議未必適合目前程式碼
- 你想避免盲目照單全收

建議使用：`receiving-code-review`

```text
以下是 review comments。請先依 receiving-code-review 驗證每一條，
再決定哪些要改、哪些要澄清、哪些要技術性 push back。
```

### 步驟 3：視需要加上輔助工具

主要工具選定後，再補上必要的輔助 skill：

| 主要工具 | 建議搭配 | 用途 |
|----------|---------|------|
| `code-simplifier` | `reviewer` | 簡化後再做正式 diff review |
| `code-reviewer` | `reviewer` | 先驗證需求對齊，再做品質/安全把關 |
| `reviewer` | `receiving-code-review` | reviewer 回來後，用標準流程處理意見 |
| `code-review.workflow` | `receiving-code-review` | 高風險流程中，確保意見處理也有紀律 |
| `任一 review 流程` | `code-review-assistant` | 當作 checklist / gate，避免遺漏基礎項目 |

## 推薦組合

### 組合 1：一般功能開發

```text
code-simplifier -> code-reviewer -> reviewer
```

- 先把 touched code 整乾淨
- 再確認沒有偏離 task / spec
- 最後做正式 merge 前審查

### 組合 2：只有 PR，沒有正式 spec

```text
code-simplifier -> reviewer
```

- 適合 ad-hoc 開發、小功能、快速迭代
- 如果沒有明確計畫文件，就不一定需要 `code-reviewer`

### 組合 3：高風險變更

```text
code-simplifier -> code-review.workflow -> receiving-code-review
```

- 適合 auth、DB、migration、permission、核心 API
- 不建議只做單一 reviewer 就直接 merge

### 組合 4：收到大量 review comments

```text
receiving-code-review -> 修正 -> reviewer（必要時複審）
```

- 先驗證 comment 是否正確
- 修正後再做一次 focused review，確認沒有引入回歸

## AI 自動提醒規則

如果你希望 AI 在對話中主動挑對工具，可以用以下規則：

### 使用者說出這些訊號時，AI 應主動提醒

| 使用者訊號 | AI 應提醒的工具 | 原因 |
|-----------|----------------|------|
| 「我剛完成 step 2 / task 3 / milestone」 | `code-reviewer` | 這是階段性驗收點 |
| 「我要開 PR / merge / pre-merge」 | `reviewer` | 這是正式 diff review 時機 |
| 「幫我整理這次改動，但不要改功能」 | `code-simplifier` | 這是簡化與可讀性整理場景 |
| 「這次是 auth / DB / migration 相關」 | `code-review.workflow` | 高風險，應走完整流程 |
| 「這些 comments 幫我處理」 | `receiving-code-review` | 先驗證再修改，避免盲改 |
| 「現在需不需要 review？」 | `requesting-code-review` | 先判斷 review 時機 |
| 「幫我檢查能不能 commit」 | `code-review-assistant` | 先走 checklist / quality gate |

### 可直接放進提示詞的提醒模板

```text
當使用者提到以下情境時，請主動建議使用對應工具：
- 完成 task / step -> code-reviewer
- 準備 PR / merge -> reviewer
- 高風險變更 -> code-review.workflow
- 想整理 touched code 且不改行為 -> code-simplifier
- 收到 review comments -> receiving-code-review
- 不確定是否該 review -> requesting-code-review
若是正式開發流程，優先採用：
code-simplifier -> code-reviewer 或 reviewer -> receiving-code-review
```

## 進階用法（選用）

### 情境 A：有 spec / plan 的規格驅動開發

適用於有 OpenSpec、設計文件或 task breakdown 的情境。

建議順序：

```text
完成實作 -> code-simplifier -> code-reviewer -> reviewer
```

原因：
- `code-reviewer` 能補足「是否符合原始規劃」
- `reviewer` 能補足「是否適合 merge」

### 情境 B：多人協作的嚴格 merge gate

適用於多人共同維護同一分支，或需保留審查紀錄的情境。

建議順序：

```text
requesting-code-review -> code-review.workflow -> receiving-code-review
```

原因：
- 先定義何時發起 review
- 再按固定流程分段審查
- 最後以標準方式處理 findings

## 常見問題

**Q: `code-reviewer` 和 `reviewer` 最容易混淆，怎麼分？**  
A: 前者偏「需求/計畫對齊」，後者偏「PR / diff 的品質、安全與 maintainability」。有 spec 時通常先 `code-reviewer`，要 merge 時再 `reviewer`。

**Q: `code-simplifier` 能不能取代 code review？**  
A: 不能。它主要負責簡化與整理 touched code，降低複雜度與 reviewer 噪音，但不等於正式需求驗收或安全審查。

**Q: 小改動也需要完整流程嗎？**  
A: 不需要。小修通常 `code-simplifier -> reviewer` 或甚至只做 `code-review-assistant` checklist 就夠。只有高風險變更才建議升級到 `code-review.workflow`。

**Q: 收到 reviewer 建議後，應該直接照做嗎？**  
A: 不建議。先用 `receiving-code-review` 驗證建議是否適合目前程式碼，再決定修改、澄清或技術性 push back。

## 疑難排解

| 問題 | 原因 | 解決方式 |
|------|------|----------|
| 不知道該用哪個 review 工具 | 把整理、驗收、正式審查、處理意見混成同一件事 | 先判斷目前階段，再選對應主要工具 |
| reviewer 找很多風格問題，訊號太雜 | 在正式 review 前沒有先清理 touched code | 先跑 `code-simplifier` 再做正式審查 |
| 明明通過 PR review，卻發現不符合原需求 | 只做 diff review，沒做 plan alignment | 在 milestone 完成後加一道 `code-reviewer` |
| 收到 comment 後越改越亂 | 沒有先驗證 comment 是否正確 | 先用 `receiving-code-review` 梳理 comment，再逐項處理 |
| 高風險改動只用單一 reviewer，信心不足 | 缺少 context review 與 security/testing 分段 | 升級到 `code-review.workflow` |

## 相關資源

- [CODE-QUALITY-TOOLS.md](./CODE-QUALITY-TOOLS.md) - 程式碼品質工具安裝指南
- [TOOL-DECISION-GUIDE.md](./TOOL-DECISION-GUIDE.md) - 開發情境決策指南
- [Development Workflow](./DEVELOPMENT-WORKFLOW.md) - 完整開發工作流程
- [Claude Plugins Official: code-simplifier](https://github.com/anthropics/claude-plugins-official/blob/main/plugins/code-simplifier/agents/code-simplifier.md) - `code-simplifier` 定義來源
