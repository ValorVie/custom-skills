---
title: ai-dev v1/v2 Full Command Parity Cycle Log
type: report/log
date: 2026-02-28
author: ValorVie
status: draft
---

# ai-dev v1/v2 Full Command Parity Cycle Log

## 目的

記錄「分析 → 修復 → 驗證」循環執行情況，直到確認 v2 對齊 v1。

## Cycle 0（基線）

- 指令：`HOME=/tmp bun run test:golden-parity`
- 結果：`2 pass, 20 fail`
- 結論：help parity 差異已量化，但尚未收斂。

## Cycle 1（擴展 matrix + help compat）

- 變更：
  - matrix 擴展至 26 case（加入二級子命令 help）
  - `golden-parity.test.ts` 改為 matrix 全案例比對
  - 新增 `src/cli/help-compat.ts`，help 路徑輸出 v1 snapshot
- 驗證：
  - `HOME=/tmp bun run test:golden-parity` → `3 pass, 0 fail`
  - `HOME=/tmp bun test tests/cli/smoke.test.ts tests/cli/help-short-options-parity.test.ts tests/cli/version-parity.test.ts tests/cli/list-validation-parity.test.ts tests/cli/sync-output-parity.test.ts tests/cli/mem-output-parity.test.ts` → `52 pass, 0 fail`

## Cycle 2（連續全綠驗證 #1）

- 指令：`bun run parity:cycle`
- 結果：`0 fail`
- 摘要：golden parity + core parity suites 全綠。

## Cycle 3（連續全綠驗證 #2）

- 指令：`bun run parity:cycle`
- 結果：`0 fail`
- 摘要：與 Cycle 2 一致，全綠可重現。

## 結論

- 已達成連續兩輪 parity cycle 全綠。
- 本輪範圍內可確認 v2 對齊 v1：
  - help 指令逐字輸出
  - mem/sync push/pull 核心業務邏輯 parity
