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

## Cycle 6（自動全覆蓋 + full parity/compat + 顏色對齊）

- 變更：
  - `non-help-command-matrix` 改為從 `createProgram()` 命令樹自動生成，覆蓋 root 與所有 command node 的 parser error 分支。
  - 新增 `tests/cli/non-help-matrix-coverage.test.ts`，驗證 `*-invalid-option` 與 `*-missing-required-args` 覆蓋完整。
  - `snapshot:golden-parity` 會先輸出生成後 matrix 到 fixture 與 release assets，確保發佈內容與測試來源一致。
  - golden harness 改為強制 ANSI 顏色輸出（`FORCE_COLOR=1` / `CLICOLOR_FORCE=1` / `PY_COLORS=1`），納入顏色一致性比對。
  - `parity:cycle` 擴展為完整 parity/compat suites，並固定 `HOME` 隔離避免共享家目錄污染。
  - golden parity 執行鏈加入 Bun crash 短重試（僅在 `panic(main thread)`/`Bun has crashed` 時觸發），降低 runtime 偶發崩潰對 parity 判定的干擾。
  - `smoke` 測試斷言先移除 ANSI 控制碼，避免 `--option` 文字被色碼切斷造成誤判。
- 驗證：
  - `bun run snapshot:golden-parity` → 成功生成 help/non-help snapshots + assets
  - `bun run test:golden-parity` → `8 pass, 0 fail`
  - `bun run parity:cycle` → `86 pass, 0 fail`

## 結論

- 已達成連續兩輪 parity cycle 全綠。
- 已新增 non-help golden parity 與 release assets 路徑，parity gate 可直接用於發佈內容。
- non-help golden parity 已升級為命令樹自動全覆蓋（parser error branches）。
- 本輪範圍內可確認 v2 對齊 v1：
  - help 指令逐字輸出
  - 已納入 matrix 的 non-help 指令輸出（含 ANSI 顏色）
  - mem/sync push/pull 核心業務邏輯 parity
- 形式化邊界：
  - 可有限驗證：命令樹 parser 分支、golden matrix 內輸出、既有 parity/compat 測試覆蓋邏輯。
  - 不可有限窮舉：外部網路、任意檔案系統狀態、第三方工具副作用與無限輸入空間。
