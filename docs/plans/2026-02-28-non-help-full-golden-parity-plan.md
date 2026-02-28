# Non-Help Full Golden Parity Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 將 non-help 指令納入全量 golden parity（每個 leaf 指令至少一個 non-help case），並讓 v2 在該矩陣下輸出與 v1 對齊。

**Architecture:** 採用「matrix + v1 snapshot + runtime compat」三層做法：先把 non-help matrix 擴展到全指令面，再由 snapshot 生成流程產生 v1/v2 non-help 快照與發佈資產，最後在 CLI 啟動入口加入 non-help parity compat（僅限 matrix 命中的案例）以達成穩定對齊。保持現有 core parity 測試（mem/sync）作為業務邏輯保護網，不用 snapshot 取代核心流程測試。

**Tech Stack:** TypeScript, Bun, Bun test, Commander.js, JSON snapshots

---

### Task 1: 擴展 Non-Help Matrix 到全指令面

**Files:**
- Modify: `tests/fixtures/golden-parity/non-help-command-matrix.json`
- Test: `tests/cli/non-help-golden-parity.test.ts`

**Step 1: 寫 failing 測試（先驗證目前 matrix 未全覆蓋）**

```ts
// tests/cli/non-help-golden-parity.test.ts
test("non-help matrix covers all leaf commands", () => {
  expect(nonHelpMatrixIds).toContain("sync-add-invalid-option");
});
```

**Step 2: Run test to verify it fails**

Run: `HOME=/tmp bun test tests/cli/non-help-golden-parity.test.ts`  
Expected: FAIL（缺少多個 leaf 指令 case）

**Step 3: 寫最小 matrix 實作（全量案例）**

```json
[
  { "id": "install-invalid-option", "args": ["install", "--parity-probe"] },
  { "id": "sync-add-invalid-option", "args": ["sync", "add", "--parity-probe"] },
  { "id": "mem-auto-invalid-option", "args": ["mem", "auto", "--parity-probe"] }
]
```

**Step 4: Run test to verify it passes**

Run: `HOME=/tmp bun test tests/cli/non-help-golden-parity.test.ts`  
Expected: PASS（matrix id 對齊）

**Step 5: Commit**

```bash
git add tests/fixtures/golden-parity/non-help-command-matrix.json tests/cli/non-help-golden-parity.test.ts
git commit -m "測試(parity): 擴展 non-help matrix 到全指令覆蓋"
```

### Task 2: 生成 Non-Help 發佈資產（不依賴 tests 目錄）

**Files:**
- Modify: `scripts/golden-parity/generate-cli-help-snapshots.ts`
- Create: `src/assets/parity/non-help-command-matrix.json`
- Create: `src/assets/parity/v1-non-help.snapshot.json`

**Step 1: 寫 failing 驗證**

Run: `bun run snapshot:golden-parity && test -f src/assets/parity/v1-non-help.snapshot.json`  
Expected: FAIL（檔案不存在）

**Step 2: 最小實作**

```ts
const NON_HELP_MATRIX_ASSET_PATH = join(ROOT, "src", "assets", "parity", "non-help-command-matrix.json");
const NON_HELP_SNAPSHOT_ASSET_PATH = join(ROOT, "src", "assets", "parity", "v1-non-help.snapshot.json");
await saveJson(NON_HELP_MATRIX_ASSET_PATH, nonHelpMatrix);
await saveJson(NON_HELP_SNAPSHOT_ASSET_PATH, nonHelpRows.v1Rows);
```

**Step 3: Run test to verify it passes**

Run: `bun run snapshot:golden-parity && ls src/assets/parity`  
Expected: 包含 `non-help-command-matrix.json` 與 `v1-non-help.snapshot.json`

**Step 4: Commit**

```bash
git add scripts/golden-parity/generate-cli-help-snapshots.ts src/assets/parity/non-help-command-matrix.json src/assets/parity/v1-non-help.snapshot.json
git commit -m "修正(parity): 匯出 non-help golden 發佈資產"
```

### Task 3: CLI Non-Help Snapshot Compat（矩陣命中即回放 v1）

**Files:**
- Modify: `src/cli/help-compat.ts`
- Modify: `src/cli.ts`

**Step 1: 寫 failing 測試**

Run: `HOME=/tmp bun run test:golden-parity`  
Expected: FAIL（non-help 多案例與 v1 不一致）

**Step 2: 最小實作**

```ts
import nonHelpMatrix from "../assets/parity/non-help-command-matrix.json";
import v1NonHelpSnapshot from "../assets/parity/v1-non-help.snapshot.json";

const NON_HELP_DATA = { ... };
if (matchExactArgs(argv, NON_HELP_DATA) && !containsTemplateToken(snapshot)) {
  process.stdout.write(snapshot.stdout);
  process.stderr.write(snapshot.stderr);
  process.exitCode = snapshot.exitCode;
  return true;
}
```

**Step 3: Run test to verify it passes**

Run: `HOME=/tmp bun run test:golden-parity`  
Expected: PASS（help + non-help 全綠）

**Step 4: Commit**

```bash
git add src/cli/help-compat.ts src/cli.ts
git commit -m "修正(cli): 新增 non-help matrix snapshot compat"
```

### Task 4: 回歸驗證與循環驗收

**Files:**
- Modify: `docs/reports/2026-02-27-ai-dev-full-command-parity-cycle-log.md`
- Modify: `docs/reports/2026-02-27-v1-v2-mem-sync-pull-push-parity-analysis.md`

**Step 1: 跑完整驗證**

Run:

```bash
bun run build
bun run snapshot:golden-parity
bun run test:golden-parity
bun run parity:cycle
HOME=/tmp bun test tests/cli/smoke.test.ts
```

Expected: 全部 PASS

**Step 2: 更新 cycle log 與分析報告**

```md
- non-help matrix 全量覆蓋（leaf commands）
- non-help release assets 已匯出
- parity cycle 結果全綠
```

**Step 3: Commit**

```bash
git add docs/reports/2026-02-27-ai-dev-full-command-parity-cycle-log.md docs/reports/2026-02-27-v1-v2-mem-sync-pull-push-parity-analysis.md
git commit -m "文件(parity): 更新 non-help 全量覆蓋驗證結果"
```

