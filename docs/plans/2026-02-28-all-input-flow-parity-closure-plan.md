# ai-dev All-Input/Flow Parity Closure Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 把 `ai-dev` v1/v2 parity 驗證升級為「命令樹自動全覆蓋 + 發佈可用快照資產 + 全 parity/compat 回歸」，並明確界定可被形式化驗證的邊界。

**Architecture:** 採用三層收斂：`(1) command tree -> non-help matrix 自動生成`、`(2) snapshot pipeline 同步輸出 tests 與 release assets`、`(3) parity cycle 執行完整 parity/compat 套件並固定 HOME 隔離`。最後以報告定義「可證明覆蓋範圍」與「非有限可證明區域」。

**Tech Stack:** TypeScript, Bun, Commander.js, Bun test, JSON snapshots

---

### Task 1: Non-Help Matrix 改為命令樹自動生成

**Files:**
- Create: `tests/fixtures/golden-parity/non-help-matrix.ts`
- Modify: `tests/fixtures/golden-parity/harness.ts`
- Test: `tests/cli/non-help-matrix-coverage.test.ts`

**Step 1: 寫 failing coverage test**

```ts
expect(matrixById.has("root-invalid-option")).toBe(true);
expect(matrixById.has(`${nodeId}-invalid-option`)).toBe(true);
if (node.requiredArgCount > 0) {
  expect(matrixById.has(`${nodeId}-missing-required-args`)).toBe(true);
}
```

**Step 2: Run test to verify it fails**

Run: `HOME=/tmp bun test tests/cli/non-help-matrix-coverage.test.ts`  
Expected: FAIL（舊 matrix 為手寫，無法保證覆蓋所有 node）

**Step 3: 寫最小實作**

```ts
const program = createProgram();
walk(program, []);
matrix.push({ id: `${nodeId}-invalid-option`, args: [...node.path, "--parity-probe"] });
```

**Step 4: Run test to verify it passes**

Run: `HOME=/tmp bun test tests/cli/non-help-matrix-coverage.test.ts`  
Expected: PASS

**Step 5: Commit**

```bash
git add tests/fixtures/golden-parity/non-help-matrix.ts tests/fixtures/golden-parity/harness.ts tests/cli/non-help-matrix-coverage.test.ts
git commit -m "測試(parity): 將 non-help matrix 改為命令樹自動全覆蓋"
```

### Task 2: Snapshot Pipeline 同步輸出生成後 matrix 與 release assets

**Files:**
- Modify: `scripts/golden-parity/generate-cli-help-snapshots.ts`
- Modify: `tests/fixtures/golden-parity/non-help-command-matrix.json`
- Modify: `src/assets/parity/non-help-command-matrix.json`
- Modify: `src/assets/parity/v1-non-help.snapshot.json`

**Step 1: 寫 failing 驗證**

Run: `bun run snapshot:golden-parity && diff -u tests/fixtures/golden-parity/non-help-command-matrix.json src/assets/parity/non-help-command-matrix.json`  
Expected: FAIL（尚未保證兩端同步）

**Step 2: 寫最小實作**

```ts
await saveJson(NON_HELP_MATRIX_FIXTURE_PATH, nonHelpMatrix);
await saveJson(NON_HELP_MATRIX_ASSET_PATH, nonHelpMatrix);
await saveJson(NON_HELP_SNAPSHOT_ASSET_PATH, nonHelpRows.v1Rows);
```

**Step 3: Run test to verify it passes**

Run: `bun run snapshot:golden-parity`  
Expected: 生成 fixture 與 assets 且內容一致

**Step 4: Commit**

```bash
git add scripts/golden-parity/generate-cli-help-snapshots.ts tests/fixtures/golden-parity/non-help-command-matrix.json src/assets/parity/non-help-command-matrix.json src/assets/parity/v1-non-help.snapshot.json
git commit -m "修正(parity): 快照流程同步輸出 non-help fixture 與 release assets"
```

### Task 3: Parity Cycle 擴展為完整 parity/compat 套件並固定 HOME 隔離

**Files:**
- Modify: `scripts/golden-parity/run-parity-cycle.ts`
- Modify: `package.json`

**Step 1: 寫 failing 驗證**

Run: `bun run parity:cycle`  
Expected: FAIL（若沿用共享 HOME，`sync init parity` 可能出現權限或污染）

**Step 2: 寫最小實作**

```ts
function buildParityEnv() {
  const parityHome = process.env.PARITY_HOME ?? "/tmp";
  return { ...process.env, HOME: parityHome, USERPROFILE: parityHome };
}
```

**Step 3: Run test to verify it passes**

Run: `bun run parity:cycle`  
Expected: PASS（golden parity + full parity/compat suites 全綠）

**Step 4: Commit**

```bash
git add scripts/golden-parity/run-parity-cycle.ts package.json
git commit -m "測試(parity): 擴展 parity cycle 並加入 HOME 隔離"
```

### Task 4: 更新循環報告並定義可證明覆蓋邊界

**Files:**
- Modify: `docs/reports/2026-02-27-ai-dev-full-command-parity-cycle-log.md`
- Modify: `docs/reports/2026-02-27-v1-v2-mem-sync-pull-push-parity-analysis.md`

**Step 1: 更新 cycle log**

```md
- 新增 auto-generated non-help matrix coverage test
- parity cycle 擴至 full parity/compat suites
- 修正 HOME 隔離後連續全綠
```

**Step 2: 更新分析報告**

```md
- 標記已可形式化驗證的 finite surface（command tree parser branches）
- 標記不可有限證明區域（外部網路、檔案系統狀態、第三方副作用）
```

**Step 3: Run final verification**

Run:

```bash
bun run snapshot:golden-parity
bun run test:golden-parity
bun run parity:cycle
```

Expected: 全部 PASS

**Step 4: Commit**

```bash
git add docs/reports/2026-02-27-ai-dev-full-command-parity-cycle-log.md docs/reports/2026-02-27-v1-v2-mem-sync-pull-push-parity-analysis.md
git commit -m "文件(parity): 更新全量覆蓋與可證明邊界報告"
```
