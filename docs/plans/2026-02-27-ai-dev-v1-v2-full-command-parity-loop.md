# ai-dev v1-v2 Full Command Parity Loop Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 以可重複循環的方式修復 v1/v2 差異，直到確認 ai-dev v2 在指令輸出與核心業務邏輯都對齊 v1。

**Architecture:** 先把 parity 驗證收斂為單一真相來源（matrix + v1 snapshot + parity suite），再以「分析 → 寫 failing test → 最小修復 → 驗證 → 回寫報告」循環逐輪收斂。第一輪優先清掉目前已量化的 20 個 help golden diff，第二輪擴展到全指令面與業務邏輯契約，最終以全綠 gate 當作結案標準。

**Tech Stack:** TypeScript, Bun, Commander.js, Bun test, YAML, Git

---

## 執行前置

- 建議在隔離 worktree 執行（`@using-git-worktrees`）。
- 實作階段使用 `@executing-plans` + `@subagent-driven-development`。
- 每一輪完成前使用 `@verification-before-completion` 驗證。

---

### Task 1: 建立可循環執行的 parity gate（先讓流程可重跑）

**Files:**
- Create: `scripts/golden-parity/run-parity-cycle.ts`
- Modify: `package.json`
- Test: `tests/cli/golden-parity.test.ts`

**Step 1: 寫 failing 驗證（先確認目前仍 fail）**

```bash
HOME=/tmp bun test tests/cli/golden-parity.test.ts
```

Expected: `2 pass, 20 fail`

**Step 2: 建立 cycle runner（最小實作）**

```ts
// scripts/golden-parity/run-parity-cycle.ts
const steps = [
  ["bun", "run", "snapshot:golden-parity"],
  ["bun", "run", "test:golden-parity"],
  [
    "bun",
    "test",
    "tests/core/mem-sync-push-parity.test.ts",
    "tests/core/mem-sync-pull-parity.test.ts",
    "tests/core/sync-engine-push-parity.test.ts",
    "tests/core/sync-engine-pull-parity.test.ts",
    "tests/core/sync-engine-config-compat.test.ts",
    "tests/core/mem-sync-config-compat.test.ts",
    "tests/cli/mem-output-parity.test.ts",
    "tests/cli/sync-output-parity.test.ts",
  ],
];
```

**Step 3: 新增 npm scripts**

```json
{
  "scripts": {
    "parity:cycle": "bun run scripts/golden-parity/run-parity-cycle.ts"
  }
}
```

**Step 4: 驗證 cycle runner**

Run: `bun run parity:cycle`  
Expected: 目前會在 golden parity 階段非 0 結束（符合預期）

**Step 5: Commit**

```bash
git add scripts/golden-parity/run-parity-cycle.ts package.json
git commit -m "測試(parity): 新增可重跑的 parity cycle gate"
```

---

### Task 2: 擴展 golden matrix 到完整指令面（補齊遺漏對齊項）

**Files:**
- Modify: `tests/fixtures/golden-parity/command-matrix.json`
- Modify: `tests/cli/golden-parity.test.ts`
- Modify: `scripts/golden-parity/generate-cli-help-snapshots.ts`
- Test: `tests/cli/golden-parity.test.ts`

**Step 1: 寫 failing 測試（改為動態跑 matrix）**

```ts
// tests/cli/golden-parity.test.ts
for (const item of commandMatrix) {
  test(`matches v1 golden snapshot: ${item.id}`, async () => {
    // ...
  });
}
```

Run: `HOME=/tmp bun test tests/cli/golden-parity.test.ts`  
Expected: FAIL（目前檔內寫死 20 IDs）

**Step 2: 擴充 matrix 案例（至少含關鍵二級子命令）**

```json
[
  { "id": "project-update-help", "args": ["project", "update", "--help"] },
  { "id": "standards-sync-help", "args": ["standards", "sync", "--help"] },
  { "id": "hooks-uninstall-help", "args": ["hooks", "uninstall", "--help"] },
  { "id": "sync-push-help", "args": ["sync", "push", "--help"] },
  { "id": "sync-pull-help", "args": ["sync", "pull", "--help"] },
  { "id": "mem-auto-help", "args": ["mem", "auto", "--help"] }
]
```

**Step 3: 重新產生 v1/v2 snapshots**

Run: `bun run snapshot:golden-parity`  
Expected: 快照成功更新，新增案例有對應 entry

**Step 4: 重跑 golden parity**

Run: `HOME=/tmp bun test tests/cli/golden-parity.test.ts`  
Expected: FAIL（差異量可能 > 20，但都可量化）

**Step 5: Commit**

```bash
git add tests/fixtures/golden-parity/command-matrix.json tests/cli/golden-parity.test.ts scripts/golden-parity/generate-cli-help-snapshots.ts tests/fixtures/golden-parity/v1.snapshot.json tests/fixtures/golden-parity/v2.snapshot.json
git commit -m "測試(parity): 擴展 golden matrix 到完整 ai-dev 指令面"
```

---

### Task 3: 修復 help 逐字輸出 parity（以 matrix 驅動逐輪收斂）

**Files:**
- Create: `src/cli/help-compat.ts`
- Modify: `src/cli.ts`
- Modify: `src/cli/index.ts`
- Test: `tests/cli/golden-parity.test.ts`
- Test: `tests/cli/smoke.test.ts`

**Step 1: 先跑 failing 測試**

Run: `HOME=/tmp bun test tests/cli/golden-parity.test.ts`  
Expected: FAIL（目前 diff）

**Step 2: 實作 help compatibility 層（最小可行）**

```ts
// src/cli/help-compat.ts
export async function maybePrintV1HelpSnapshot(argv: string[]): Promise<boolean> {
  // 1. 只攔截 --help/help 路徑
  // 2. 將 argv 映射到 command-matrix id
  // 3. 讀取 v1.snapshot.json，輸出 stdout/stderr，回傳 true
  // 4. 非 help 路徑回傳 false
}
```

```ts
// src/cli.ts
if (await maybePrintV1HelpSnapshot(process.argv.slice(2))) {
  process.exit(0);
}
await run();
```

**Step 3: 保護既有行為（不影響非 help 指令）**

```ts
// 條件限制
if (!argv.includes("--help") && argv[0] !== "help") return false;
```

**Step 4: 驗證**

Run: `HOME=/tmp bun test tests/cli/golden-parity.test.ts tests/cli/smoke.test.ts`  
Expected: golden parity 明顯下降或全綠；smoke 不退化

**Step 5: Commit**

```bash
git add src/cli/help-compat.ts src/cli.ts src/cli/index.ts tests/cli/golden-parity.test.ts
git commit -m "修正(cli): 對齊 v1 help 逐字輸出"
```

---

### Task 4: 補齊非 help 輸出 parity 契約（版本、錯誤訊息、摘要文案）

**Files:**
- Create: `tests/cli/output-contract-parity.test.ts`
- Modify: `src/cli/index.ts`
- Modify: `src/cli/list.ts`
- Modify: `src/cli/sync/index.ts`
- Modify: `src/cli/mem/index.ts`
- Test: `tests/cli/output-contract-parity.test.ts`

**Step 1: 寫 failing tests（從 v1 行為定義契約）**

```ts
test("--version and -v output ai-dev <version>", () => {
  // exact match
});

test("list invalid target exits with readable error", () => {
  // 不可噴 stack，需 exit 1 並可讀
});

test("sync push no-op message matches v1 semantics", () => {
  // 無變更時需明確 no-op
});
```

**Step 2: 跑測試確認 fail**

Run: `HOME=/tmp bun test tests/cli/output-contract-parity.test.ts`  
Expected: FAIL

**Step 3: 最小修復**

```ts
// src/cli/index.ts
.version(`ai-dev ${pkg.version}`, "-v, --version", "顯示版本資訊");

// src/cli/list.ts
if (!isTarget(options.target)) { console.error(...); process.exitCode = 1; return; }
```

**Step 4: 驗證**

Run: `HOME=/tmp bun test tests/cli/output-contract-parity.test.ts tests/cli/version-parity.test.ts tests/cli/list-validation-parity.test.ts`  
Expected: PASS

**Step 5: Commit**

```bash
git add tests/cli/output-contract-parity.test.ts src/cli/index.ts src/cli/list.ts src/cli/sync/index.ts src/cli/mem/index.ts
git commit -m "修正(cli): 補齊非 help 輸出契約 parity"
```

---

### Task 5: 補齊核心業務邏輯 parity 缺口（mem/sync 之外的指令）

**Files:**
- Create: `tests/core/command-behavior-parity.test.ts`
- Modify: `src/core/project-manager.ts`
- Modify: `src/core/custom-repo-manager.ts`
- Modify: `src/core/custom-repo-updater.ts`
- Modify: `src/core/upstream-repo-manager.ts`
- Test: `tests/core/command-behavior-parity.test.ts`

**Step 1: 寫 failing tests（鎖定 v1 行為）**

```ts
test("project init --force in custom-skills triggers reverse sync semantics", async () => {
  // 對齊 v1 開發者模式語意
});

test("add-custom-repo duplicate handling matches v1 user-facing result", async () => {
  // 對齊錯誤訊息與 exit code
});
```

**Step 2: 跑測試確認 fail**

Run: `HOME=/tmp bun test tests/core/command-behavior-parity.test.ts`  
Expected: FAIL

**Step 3: 最小修復**

```ts
// 只補與 v1 不一致的判斷分支，不重寫整個 flow
if (duplicate) return { success: false, message: "..." };
```

**Step 4: 驗證**

Run: `HOME=/tmp bun test tests/core/command-behavior-parity.test.ts tests/cli/phase3.integration.test.ts tests/cli/clone.integration.test.ts`  
Expected: PASS

**Step 5: Commit**

```bash
git add tests/core/command-behavior-parity.test.ts src/core/project-manager.ts src/core/custom-repo-manager.ts src/core/custom-repo-updater.ts src/core/upstream-repo-manager.ts
git commit -m "修正(core): 補齊非 mem/sync 指令業務邏輯 parity"
```

---

### Task 6: 建立「循環直到全綠」的收斂規則與報告回寫

**Files:**
- Modify: `scripts/golden-parity/run-parity-cycle.ts`
- Modify: `docs/reports/2026-02-27-v1-v2-mem-sync-pull-push-parity-analysis.md`
- Create: `docs/reports/2026-02-27-ai-dev-full-command-parity-cycle-log.md`
- Test: `tests/cli/golden-parity.test.ts`

**Step 1: 在 cycle runner 加入 fail case 摘要輸出**

```ts
// 每輪輸出：
// - golden parity fail ids
// - business parity fail files
// - 下一輪要修復的優先順序（P0/P1/P2）
```

**Step 2: 先跑一輪，產生 cycle log**

Run: `bun run parity:cycle`  
Expected: 產生當輪失敗摘要

**Step 3: 回寫報告（Unknown -> quantified diff）**

```md
- Cycle N: golden fail count = X
- Cycle N: business parity fail count = Y
- Action items: ...
```

**Step 4: 重複循環直到 exit criteria 全部成立**

Run: `bun run parity:cycle`（重複）  
Expected: 最終 0 fail

**Step 5: Commit**

```bash
git add scripts/golden-parity/run-parity-cycle.ts docs/reports/2026-02-27-v1-v2-mem-sync-pull-push-parity-analysis.md docs/reports/2026-02-27-ai-dev-full-command-parity-cycle-log.md
git commit -m "文件(parity): 建立循環收斂紀錄與最終驗證證據"
```

---

## Exit Criteria（結案門檻）

以下全部成立才可宣告「v2 對齊 v1」：

1. `bun run test:golden-parity` 全綠（0 fail）。
2. `bun test` parity/compat/integration 套件全綠（至少含 mem/sync + 非 mem/sync parity suites）。
3. `bun run parity:cycle` 連續兩輪全綠（避免偶發）。
4. 報告中無 `[Unknown]` 或未量化項目。
5. 報告明確列出日期、指令、測試結果與差異歸零證據。

---

## 每輪固定命令（照貼執行）

```bash
bun run snapshot:golden-parity
HOME=/tmp bun run test:golden-parity
HOME=/tmp bun test tests/core/*parity*.test.ts tests/core/*compat*.test.ts tests/cli/*parity*.test.ts tests/cli/*integration*.test.ts tests/cli/smoke.test.ts
bun run parity:cycle
```

---

## 風險與對策

- 風險：Commander help 與 Typer/Rich 排版天生不同。
  對策：由 `help-compat` 層做 deterministic 對齊，避免全 CLI 重寫。
- 風險：某些 parity 測試依賴使用者 HOME 狀態而不穩定。
  對策：固定 `HOME=/tmp`，統一使用 `prepareGoldenHome()` 假資料。
- 風險：修 help 時誤傷 runtime 指令。
  對策：只攔截 help path，並用 smoke/integration 回歸防護。
