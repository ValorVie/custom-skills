# ai-dev v1/v2 Parity Cycle Remediation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 修復目前仍存在的 v1/v2 parity 缺口，確保 ai-dev v2 在指令輸出與核心業務邏輯上與 v1 對齊。

**Architecture:** 先補會失敗的 parity 測試，接著以最小修改修復核心邏輯與 CLI 行為，再以針對性與整體回歸測試收斂。核心調整集中在 `src/cli/*` 與 `src/core/*`；每個修復都對應至少一個可重現的測試案例。

**Tech Stack:** TypeScript, Bun, Commander.js, Bun test, YAML

---

### Task 1: CLI 版本輸出 parity（`-v/--version`）

**Files:**
- Create: `tests/cli/version-parity.test.ts`
- Modify: `src/cli/index.ts`
- Test: `tests/cli/version-parity.test.ts`

**Step 1: Write the failing test**

```ts
test("-v and --version output 'ai-dev <version>'", () => {
  const pkg = require("../../package.json") as { version: string };
  expect(runCli(["-v"]).stdout.trim()).toBe(`ai-dev ${pkg.version}`);
  expect(runCli(["--version"]).stdout.trim()).toBe(`ai-dev ${pkg.version}`);
});
```

**Step 2: Run test to verify it fails**

Run: `bun test tests/cli/version-parity.test.ts`
Expected: FAIL（目前 `-v` 無效，`--version` 非 v1 格式）

**Step 3: Write minimal implementation**

```ts
program
  .option("-v, --version", "顯示版本資訊")
  .hook("preAction", ...)
  .action(() => {
    if (program.opts().version) {
      console.log(`ai-dev ${pkg.version}`);
      process.exit(0);
    }
  });
```

**Step 4: Run test to verify it passes**

Run: `bun test tests/cli/version-parity.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/cli/version-parity.test.ts src/cli/index.ts
git commit -m "修正(cli): 對齊 v1 版本旗標與輸出格式"
```

---

### Task 2: `list` 參數驗證 parity（無效 target/type 不可 crash）

**Files:**
- Create: `tests/cli/list-validation-parity.test.ts`
- Modify: `src/cli/list.ts`
- Test: `tests/cli/list-validation-parity.test.ts`

**Step 1: Write the failing test**

```ts
test("list rejects invalid --target with clear error and exit 1", () => {
  const result = runCli(["list", "--target", "badtarget", "--type", "skills"]);
  expect(result.exitCode).toBe(1);
  expect(result.stderr + result.stdout).toContain("無效的目標");
});

test("list rejects invalid --type with clear error and exit 1", () => {
  const result = runCli(["list", "--target", "claude", "--type", "badtype"]);
  expect(result.exitCode).toBe(1);
  expect(result.stderr + result.stdout).toContain("無效的類型");
});
```

**Step 2: Run test to verify it fails**

Run: `bun test tests/cli/list-validation-parity.test.ts`
Expected: FAIL（目前會拋出 TypeError stack）

**Step 3: Write minimal implementation**

```ts
if (options.target && !isTarget(options.target)) {
  console.error(`無效的目標：${options.target}`);
  process.exitCode = 1;
  return;
}
if (options.type && !isResourceType(options.type)) {
  console.error(`無效的類型：${options.type}`);
  process.exitCode = 1;
  return;
}
```

**Step 4: Run test to verify it passes**

Run: `bun test tests/cli/list-validation-parity.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/cli/list-validation-parity.test.ts src/cli/list.ts
git commit -m "修正(list): 補齊 target/type 驗證與錯誤輸出"
```

---

### Task 3: `sync init` fail-fast 與 ignore 規則對齊

**Files:**
- Create: `tests/core/sync-engine-init-parity.test.ts`
- Create: `tests/core/sync-engine-ignore-parity.test.ts`
- Modify: `src/core/sync-engine.ts`
- Test: `tests/core/sync-engine-init-parity.test.ts`
- Test: `tests/core/sync-engine-ignore-parity.test.ts`

**Step 1: Write the failing tests**

```ts
test("init throws when git clone fails", async () => {
  // runCommand git clone -> exitCode 1
  await expect(engine.init("https://bad.example/repo.git")).rejects.toThrow("git clone");
});

test("push excludes claude ignore patterns and custom ignore patterns", async () => {
  // 建立 local 目錄含 debug/, cache/, keep.txt
  // push 後 repo 只應保留 keep.txt
});
```

**Step 2: Run tests to verify they fail**

Run: `bun test tests/core/sync-engine-init-parity.test.ts tests/core/sync-engine-ignore-parity.test.ts`
Expected: FAIL（目前 clone 失敗不會中止，syncDirectory 未套用 ignore）

**Step 3: Write minimal implementation**

```ts
if (cloneResult.exitCode !== 0) {
  throw new Error("git clone 失敗");
}

const excludes = resolveIgnorePatterns(directory.ignoreProfile, directory.customIgnore);
await syncDirectory(sourcePath, destinationPath, true, excludes);
```

**Step 4: Run tests to verify they pass**

Run: `bun test tests/core/sync-engine-init-parity.test.ts tests/core/sync-engine-ignore-parity.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/core/sync-engine-init-parity.test.ts tests/core/sync-engine-ignore-parity.test.ts src/core/sync-engine.ts
git commit -m "修正(sync): init 失敗即中止並套用 ignore 規則"
```

---

### Task 4: `mem register` 失敗流程與 `mem pull since` 單位對齊

**Files:**
- Modify: `tests/core/mem-sync.test.ts`
- Create: `tests/core/mem-sync-since-parity.test.ts`
- Modify: `src/core/mem-sync.ts`
- Test: `tests/core/mem-sync.test.ts`
- Test: `tests/core/mem-sync-since-parity.test.ts`

**Step 1: Write the failing tests**

```ts
test("registerDevice throws when server registration fails", async () => {
  await expect(registerDevice({...invalidServer...})).rejects.toThrow("註冊失敗");
});

test("pullMemData sends since in epoch-seconds", async () => {
  // lastPullEpoch=123
  // 斷言請求 URL 包含 since=123 而非 123000
});
```

**Step 2: Run tests to verify they fail**

Run: `bun test tests/core/mem-sync.test.ts tests/core/mem-sync-since-parity.test.ts`
Expected: FAIL（目前 register fail-open，since 乘以 1000）

**Step 3: Write minimal implementation**

```ts
if (!payload?.api_key) {
  throw new Error("裝置註冊失敗，請檢查 server 與 admin secret");
}

let since = config.lastPullEpoch > 0 ? config.lastPullEpoch : 0;
```

**Step 4: Run tests to verify they pass**

Run: `bun test tests/core/mem-sync.test.ts tests/core/mem-sync-since-parity.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/core/mem-sync.test.ts tests/core/mem-sync-since-parity.test.ts src/core/mem-sync.ts
git commit -m "修正(mem): register 失敗流程與 pull since 單位對齊 v1"
```

---

### Task 5: `install --sync-project` 預設與執行路徑對齊

**Files:**
- Modify: `tests/core/installer.test.ts`
- Modify: `src/core/installer.ts`
- Test: `tests/core/installer.test.ts`

**Step 1: Write the failing test**

```ts
test("runInstall enables syncProject by default and triggers sync flow", async () => {
  // 不傳 syncProject
  // 斷言 default true 且 onProgress 包含實際同步訊息
});
```

**Step 2: Run test to verify it fails**

Run: `bun test tests/core/installer.test.ts -t "syncProject"`
Expected: FAIL（目前 default=false 且只有 requested 訊息）

**Step 3: Write minimal implementation**

```ts
const syncProject = options.syncProject ?? true;
if (syncProject) {
  await distributeSkillsFn({ ... , devMode: false, onProgress });
  onProgress("sync-project completed");
}
```

**Step 4: Run test to verify it passes**

Run: `bun test tests/core/installer.test.ts -t "syncProject"`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/core/installer.test.ts src/core/installer.ts
git commit -m "修正(install): sync-project 預設與實際執行流程對齊"
```

---

### Task 6: `add-custom-repo` 重名行為對齊（拒絕覆蓋）

**Files:**
- Create: `tests/utils/custom-repos-duplicate-parity.test.ts`
- Modify: `src/utils/custom-repos.ts`
- Modify: `src/cli/add-custom-repo.ts`
- Test: `tests/utils/custom-repos-duplicate-parity.test.ts`

**Step 1: Write the failing test**

```ts
test("addCustomRepo returns false when name already exists", async () => {
  await addCustomRepo("foo", "https://...", "main", "/tmp/foo");
  await expect(addCustomRepo("foo", "https://...", "main", "/tmp/foo2")).rejects.toThrow("已存在");
});
```

**Step 2: Run test to verify it fails**

Run: `bun test tests/utils/custom-repos-duplicate-parity.test.ts`
Expected: FAIL（目前會直接覆蓋）

**Step 3: Write minimal implementation**

```ts
if (config.repos[name]) {
  throw new Error(`${name} 已存在於 repos.yaml`);
}
```

**Step 4: Run test to verify it passes**

Run: `bun test tests/utils/custom-repos-duplicate-parity.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/utils/custom-repos-duplicate-parity.test.ts src/utils/custom-repos.ts src/cli/add-custom-repo.ts
git commit -m "修正(custom-repo): 重名時拒絕覆蓋以對齊 v1"
```

---

### Task 7: `update` 顯示 Claude Code 版本資訊強韌化

**Files:**
- Modify: `tests/core/claude-code-manager.test.ts`
- Modify: `src/core/claude-code-manager.ts`
- Test: `tests/core/claude-code-manager.test.ts`

**Step 1: Write the failing test**

```ts
test("getClaudeVersion can parse version from stderr fallback", async () => {
  // --version stdout empty, stderr has version
  // 仍可在 update 完成訊息顯示版本
});
```

**Step 2: Run test to verify it fails**

Run: `bun test tests/core/claude-code-manager.test.ts -t "stderr fallback"`
Expected: FAIL

**Step 3: Write minimal implementation**

```ts
const combined = `${versionResult.stdout}\n${versionResult.stderr}`.trim();
const first = combined.split(/\r?\n/).find((line) => line.trim().length > 0);
return first ?? null;
```

**Step 4: Run test to verify it passes**

Run: `bun test tests/core/claude-code-manager.test.ts -t "stderr fallback"`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/core/claude-code-manager.test.ts src/core/claude-code-manager.ts
git commit -m "修正(update): Claude Code 版本解析支援 stderr fallback"
```

---

### Task 8: 回歸驗證與 parity 再盤點

**Files:**
- Modify: `docs/reports/2026-02-27-v1-v2-mem-sync-pull-push-parity-analysis.md`
- Modify: `docs/v1-v2-parity-report.md`

**Step 1: Run targeted parity tests**

Run: `bun test tests/cli/version-parity.test.ts tests/cli/list-validation-parity.test.ts tests/core/sync-engine-init-parity.test.ts tests/core/sync-engine-ignore-parity.test.ts tests/core/mem-sync-since-parity.test.ts tests/utils/custom-repos-duplicate-parity.test.ts tests/core/claude-code-manager.test.ts`
Expected: PASS

**Step 2: Run existing parity and smoke suites**

Run: `bun test tests/cli/*parity*.test.ts tests/core/*parity*.test.ts tests/core/*compat*.test.ts tests/cli/smoke.test.ts tests/core/sync-engine.test.ts tests/core/mem-sync.test.ts`
Expected: PASS（無回歸）

**Step 3: Update reports with residual gaps**

```md
- 更新「已修復」與「仍待對齊」清單
- 若仍有差異，標記 P0/P1/P2 與下一循環入口
```

**Step 4: Commit**

```bash
git add docs/reports/2026-02-27-v1-v2-mem-sync-pull-push-parity-analysis.md docs/v1-v2-parity-report.md
git commit -m "文件(parity): 更新 ai-dev v1/v2 對齊再盤點結果"
```

---

### Task 9: 第六批循環收斂（sync plugin restore + 測試穩定化）

**Files:**
- Modify: `src/core/sync-engine.ts`
- Modify: `tests/core/sync-engine-init-parity.test.ts`
- Modify: `tests/core/sync-engine-push-parity.test.ts`
- Modify: `docs/reports/2026-02-27-v1-v2-mem-sync-pull-push-parity-analysis.md`

**Step 1: 先寫/調整會失敗的 parity 測試**

```ts
test("init restores plugins from manifest when remote content exists", async () => {
  // 斷言 git clone 命令包含 demo-marketplace.git（以子字串比對）
});

test("push returns early when no changes and force=false", async () => {
  // 改用 root/local 隔離目錄，不依賴 ~/.claude
});
```

**Step 2: 跑測試驗證會失敗（或偶發）**

Run: `HOME=/tmp bun test tests/core/sync-engine-init-parity.test.ts tests/core/sync-engine-push-parity.test.ts`
Expected: FAIL 或 flaky（修復前）。

**Step 3: 實作最小修復**

```ts
// tests/core/sync-engine-init-parity.test.ts
command.some((part) => part.includes("demo-marketplace.git"));

// tests/core/sync-engine-push-parity.test.ts
await engine.removeDirectory("~/.claude", { skipMinCheck: true });
await engine.addDirectory(localDir);
```

**Step 4: 重新跑局部與整體回歸**

Run: `HOME=/tmp bun test tests/core/sync-engine-init-parity.test.ts tests/core/sync-engine-push-parity.test.ts tests/core/sync-engine-pull-parity.test.ts`
Expected: PASS

Run: `HOME=/tmp bun test tests/cli/*parity*.test.ts tests/core/*parity*.test.ts tests/core/*compat*.test.ts tests/cli/smoke.test.ts tests/core/sync-engine.test.ts tests/core/mem-sync.test.ts`
Expected: PASS（104 pass, 0 fail）

Run: `HOME=/tmp bun test tests/cli/help-short-options-parity.test.ts tests/core/standards-manager-sync-target.test.ts tests/core/sync-engine-add-validation.test.ts tests/core/sync-engine-remove-confirm.test.ts tests/core/project-manager-reverse-sync.test.ts tests/cli/toggle-list-parity.test.ts tests/core/toggle-config-compat.test.ts tests/cli/install-output-parity.test.ts tests/cli/update-output-parity.test.ts tests/tui/standards-switch.test.tsx tests/tui/openers.test.ts tests/tui/source-index.test.ts tests/cli/clone.integration.test.ts tests/cli/phase3.integration.test.ts`
Expected: PASS（36 pass, 0 fail）

**Step 5: 更新報告**

```md
- 新增「第六批循環收斂」章節
- 記錄 sync init plugin restore 與測試穩定化修復
- 記錄 104/36 回歸測試結果與整包測試非 parity 失敗說明
```
