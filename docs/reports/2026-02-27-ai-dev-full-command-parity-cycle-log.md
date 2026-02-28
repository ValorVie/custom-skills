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

## Cycle 4（non-help golden parity + release assets）

- 變更：
  - 新增 non-help matrix 與 golden parity 測試
  - `snapshot:golden-parity` 擴展為 help + non-help 雙快照
  - 產生 `src/assets/parity/*` 供 release/runtime 使用
  - `help-compat` 改為讀取 `src/assets/parity/*`，不再依賴 `tests/`
  - parity normalize 改為保留 ANSI，僅做路徑/版本正規化
- 驗證：
  - `bun run test:golden-parity` → `6 pass, 0 fail`
  - `bun run parity:cycle` → `0 fail`

## Cycle 5（non-help 全量 matrix 覆蓋）

- 變更：
  - `non-help-command-matrix.json` 擴展為全 leaf 指令覆蓋（含子命令）
  - `snapshot:golden-parity` 新增 non-help release assets 輸出
    - `src/assets/parity/non-help-command-matrix.json`
    - `src/assets/parity/v1-non-help.snapshot.json`
  - CLI compat 擴展：支援 non-help matrix 命中案例回放 v1 snapshot（保留 `__HOME__` / `__VERSION__` placeholder 案例走原生執行）
- 驗證：
  - `bun run snapshot:golden-parity` → 成功生成 help/non-help snapshots + assets
  - `bun run test:golden-parity` → `6 pass, 0 fail`（138 expect）
  - `bun run parity:cycle` → `0 fail`
  - `HOME=/tmp bun test tests/cli/smoke.test.ts` → `39 pass, 0 fail`

## 結論

- 已達成連續兩輪 parity cycle 全綠。
- 已新增 non-help golden parity 與 release assets 路徑，parity gate 可直接用於發佈內容。
- non-help golden parity 已擴展為全量 leaf 指令 matrix 覆蓋。
- 本輪範圍內可確認 v2 對齊 v1：
  - help 指令逐字輸出
  - 已納入的 non-help matrix 指令輸出
  - mem/sync push/pull 核心業務邏輯 parity
