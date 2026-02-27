---
title: ai-dev non-help golden parity 與 release assets 修復計畫
type: plan
date: 2026-02-27
author: Codex
status: done
---

# ai-dev non-help golden parity 與 release assets 修復計畫

## 目標

1. 把 non-help 指令納入 golden snapshot parity。
2. 把 parity 所需 snapshot 改成發佈時可用資產（不依賴 `tests/`）。
3. 輸出比對保留 ANSI，確保文字與顏色格式可被嚴格驗證。

## 範圍

- CLI parity 驗證基礎設施
- golden snapshot 產生腳本
- help compatibility 載入來源
- non-help parity 測試與 matrix

## 實施步驟

### Step 1: 擴充 golden harness（non-help + placeholder + ANSI 保留）

- 新增 non-help matrix 載入。
- 新增測試資料 placeholder 展開（`__SPEC_FILE__`、`__MISSING_SPEC__`）。
- 在固定 HOME 下建立 `specs/sample.md`。
- normalize 不移除 ANSI，只做路徑/版本正規化。

### Step 2: 建立 non-help golden matrix 與測試

- 新增 `tests/fixtures/golden-parity/non-help-command-matrix.json`。
- 新增 `tests/cli/non-help-golden-parity.test.ts`：
  - matrix 與 snapshot 對齊檢查
  - v2 runtime 與 v1 snapshot 逐案比對

### Step 3: 擴充 snapshot 生成流程

- `snapshot:golden-parity` 同時生成：
  - `v1.snapshot.json` / `v2.snapshot.json`（help）
  - `v1.non-help.snapshot.json` / `v2.non-help.snapshot.json`（non-help）
- 同步輸出發佈資產：
  - `src/assets/parity/help-command-matrix.json`
  - `src/assets/parity/v1-help.snapshot.json`

### Step 4: help compatibility 改讀 release assets

- `src/cli/help-compat.ts` 改為 static import `src/assets/parity/*`。
- 移除 runtime 讀取 `tests/fixtures` 的依賴。

### Step 5: 對齊 non-help 行為（先鎖定 matrix 覆蓋項）

- `derive-tests`：
  - 路徑不存在錯誤訊息對齊 v1。
  - 輸出檔頭改為絕對路徑，與 snapshot 對齊。

### Step 6: 驗證

- `bun run snapshot:golden-parity`
- `bun run test:golden-parity`
- `bun run parity:cycle`

## 完成標準

- `test:golden-parity` 全綠（含 help + non-help）。
- `parity:cycle` 全綠。
- help parity 執行時不依賴 `tests/` 目錄。
- non-help parity 具備可重現 matrix 與快照。
