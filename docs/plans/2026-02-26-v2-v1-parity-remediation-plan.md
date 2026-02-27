# v2-v1 CLI/TUI Parity Remediation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 將 v2 的 CLI/TUI 指令輸出與業務邏輯全面對齊 v1，達成可驗證的 parity。

**Architecture:** 先建立 parity 測試護欄（help/行為/輸出），再按風險由高到低修復：同步引擎與 standards/toggle 的邏輯差異、project 邊界條件、install/update 輸出一致性，最後補齊 TUI 互動缺口與文件快照。每個任務遵循 DRY/YAGNI，以最小改動讓新測試通過。

**Tech Stack:** TypeScript, Bun, Commander.js, Ink, Chalk, Bun test

---

### Task 1: 建立短選項 parity 測試並修復缺漏

**Skills:** @test-driven-development @verification-before-completion

**Files:**
- Create: `tests/cli/help-short-options-parity.test.ts`
- Modify: `src/cli/clone.ts`
- Modify: `src/cli/add-custom-repo.ts`
- Modify: `src/cli/standards/index.ts`

**Step 1: Write the failing test**

```ts
import { describe, expect, test } from "bun:test";

function runHelp(args: string[]) {
  const p = Bun.spawnSync(["bun", "src/cli.ts", ...args, "--help"], {
    cwd: process.cwd(),
    stdout: "pipe",
    stderr: "pipe",
  });
  return Buffer.from(p.stdout).toString("utf8");
}

describe("help short options parity", () => {
  test("clone has -f -s -b", () => {
    const out = runHelp(["clone"]);
    expect(out).toContain("-f, --force");
    expect(out).toContain("-s, --skip-conflicts");
    expect(out).toContain("-b, --backup");
  });

  test("add-custom-repo has -n -b", () => {
    const out = runHelp(["add-custom-repo"]);
    expect(out).toContain("-n, --name");
    expect(out).toContain("-b, --branch");
  });

  test("standards sync has -n -t", () => {
    const out = runHelp(["standards", "sync"]);
    expect(out).toContain("-n, --dry-run");
    expect(out).toContain("-t, --target");
  });
});
```

**Step 2: Run test to verify it fails**

Run: `bun test tests/cli/help-short-options-parity.test.ts`
Expected: FAIL（缺少短選項）

**Step 3: Write minimal implementation**

```ts
// src/cli/clone.ts
.option("-f, --force", t("opt.force"))
.option("-s, --skip-conflicts", t("opt.skip_conflicts"))
.option("-b, --backup", t("opt.backup"))

// src/cli/add-custom-repo.ts
.option("-n, --name <name>", t("opt.name"))
.option("-b, --branch <branch>", t("opt.branch"), "main")

// src/cli/standards/index.ts (sync)
.option("-n, --dry-run", t("opt.dry_run"))
.option("-t, --target <target>", t("opt.target"), "claude")
```

**Step 4: Run test to verify it passes**

Run: `bun test tests/cli/help-short-options-parity.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/cli/help-short-options-parity.test.ts src/cli/clone.ts src/cli/add-custom-repo.ts src/cli/standards/index.ts
git commit -m "修正(cli): 補齊 clone/add-custom-repo/standards sync 短選項"
```

---

### Task 2: 修復 standards sync 的 target/dry-run 行為

**Skills:** @test-driven-development @coding-standards

**Files:**
- Create: `tests/core/standards-manager-sync-target.test.ts`
- Modify: `src/core/standards-manager.ts`
- Modify: `src/cli/standards/index.ts`

**Step 1: Write the failing test**

```ts
test("syncStandards dryRun does not rename files", async () => {
  const result = await syncStandards(projectRoot, { target: "claude", dryRun: true });
  expect(result.success).toBe(true);
  expect(await Bun.file(activePath).exists()).toBe(true);
  expect(await Bun.file(disabledPath).exists()).toBe(false);
});

test("syncStandards target only affects one target", async () => {
  await syncStandards(projectRoot, { target: "claude" });
  expect(await Bun.file(claudeDisabledPath).exists()).toBe(true);
  expect(await Bun.file(opencodeActivePath).exists()).toBe(true);
});
```

**Step 2: Run test to verify it fails**

Run: `bun test tests/core/standards-manager-sync-target.test.ts`
Expected: FAIL（目前無 target/dry-run 參數）

**Step 3: Write minimal implementation**

```ts
export async function syncStandards(
  projectRoot = process.cwd(),
  options: { target?: TargetType; dryRun?: boolean } = {},
): Promise<SyncStandardsResult> {
  const target = options.target;
  const dryRun = options.dryRun ?? false;

  // dryRun: only count planned moves, do not rename
  // target: only iterate selected target when syncing skills/commands/agents
}
```

```ts
// src/cli/standards/index.ts
const result = await syncStandards(process.cwd(), {
  target: options.target as TargetType,
  dryRun: options.dryRun,
});
```

**Step 4: Run test to verify it passes**

Run: `bun test tests/core/standards-manager-sync-target.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/core/standards-manager-sync-target.test.ts src/core/standards-manager.ts src/cli/standards/index.ts
git commit -m "修正(standards): sync 新增 target 與 dry-run 行為對齊"
```

---

### Task 3: 修復 sync init 參數相容（--remote 必填）

**Skills:** @test-driven-development

**Files:**
- Create: `tests/cli/sync-init-parity.test.ts`
- Modify: `src/cli/sync/index.ts`

**Step 1: Write the failing test**

```ts
test("sync init requires --remote", () => {
  const p = Bun.spawnSync(["bun", "src/cli.ts", "sync", "init"], { stdout: "pipe", stderr: "pipe" });
  const err = Buffer.from(p.stderr).toString("utf8");
  expect(p.exitCode).toBe(1);
  expect(err).toContain("required option");
});
```

**Step 2: Run test to verify it fails**

Run: `bun test tests/cli/sync-init-parity.test.ts`
Expected: FAIL（目前可不給 --remote）

**Step 3: Write minimal implementation**

```ts
sync
  .command("init")
  .requiredOption("--remote <url>", t("opt.remote"))
```

**Step 4: Run test to verify it passes**

Run: `bun test tests/cli/sync-init-parity.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/cli/sync-init-parity.test.ts src/cli/sync/index.ts
git commit -m "修正(sync): init 要求必填 --remote 參數"
```

---

### Task 4: 修復 sync add 路徑驗證邏輯

**Skills:** @test-driven-development

**Files:**
- Create: `tests/core/sync-engine-add-validation.test.ts`
- Modify: `src/core/sync-engine.ts`

**Step 1: Write the failing test**

```ts
test("addDirectory rejects non-existing path", async () => {
  await expect(engine.addDirectory("/tmp/not-exists-123")).rejects.toThrow("目錄不存在");
});
```

**Step 2: Run test to verify it fails**

Run: `bun test tests/core/sync-engine-add-validation.test.ts`
Expected: FAIL

**Step 3: Write minimal implementation**

```ts
const expanded = expandHome(pathValue);
if (!(await pathExists(expanded))) {
  throw new Error("目錄不存在");
}
```

**Step 4: Run test to verify it passes**

Run: `bun test tests/core/sync-engine-add-validation.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/core/sync-engine-add-validation.test.ts src/core/sync-engine.ts
git commit -m "修正(sync): add 先驗證目錄存在性"
```

---

### Task 5: 修復 sync remove 的刪除確認流程

**Skills:** @test-driven-development @security-review

**Files:**
- Create: `tests/core/sync-engine-remove-confirm.test.ts`
- Modify: `src/core/sync-engine.ts`
- Modify: `src/cli/sync/index.ts`

**Step 1: Write the failing test**

```ts
test("removeDirectory keeps repo subdir when deleteRepoSubdir=false", async () => {
  await engine.removeDirectory("~/.claude", { deleteRepoSubdir: false, skipMinCheck: true });
  expect(await Bun.file(repoSubdirPath).exists()).toBe(true);
});
```

**Step 2: Run test to verify it fails**

Run: `bun test tests/core/sync-engine-remove-confirm.test.ts`
Expected: FAIL（目前一定刪除）

**Step 3: Write minimal implementation**

```ts
async removeDirectory(pathValue: string, options: { skipMinCheck?: boolean; deleteRepoSubdir?: boolean } = {}) {
  // ...
  if (options.deleteRepoSubdir) {
    await rm(repoSubdirPath, { recursive: true, force: true });
  }
}
```

```ts
// src/cli/sync/index.ts
const { deleteSubdir } = await inquirer.prompt([{ type: "confirm", name: "deleteSubdir", message: `是否刪除 repo 子目錄 ${removed.repoSubdir}/ ?`, default: false }]);
await engine.removeDirectory(path, { deleteRepoSubdir: deleteSubdir });
```

**Step 4: Run test to verify it passes**

Run: `bun test tests/core/sync-engine-remove-confirm.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/core/sync-engine-remove-confirm.test.ts src/core/sync-engine.ts src/cli/sync/index.ts
git commit -m "修正(sync): remove 新增 repo 子目錄刪除確認"
```

---

### Task 6: 修復 project init 反向同步觸發條件

**Skills:** @test-driven-development

**Files:**
- Create: `tests/core/project-manager-reverse-sync.test.ts`
- Modify: `src/core/project-manager.ts`

**Step 1: Write the failing test**

```ts
test("shouldReverseSync requires force=true", () => {
  expect(shouldReverseSync(projectRoot, false)).toBe(false);
  expect(shouldReverseSync(projectRoot, true)).toBe(true);
});
```

**Step 2: Run test to verify it fails**

Run: `bun test tests/core/project-manager-reverse-sync.test.ts`
Expected: FAIL（目前未檢查 force）

**Step 3: Write minimal implementation**

```ts
function shouldReverseSync(targetDir: string, force: boolean): boolean {
  if (!force) return false;
  const cwd = resolve(process.cwd());
  return basename(cwd) === "custom-skills" && resolve(targetDir) === cwd;
}

if (shouldReverseSync(targetDir, force)) {
  await reverseSyncProjectToTemplate(targetDir, templateDir);
}
```

**Step 4: Run test to verify it passes**

Run: `bun test tests/core/project-manager-reverse-sync.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/core/project-manager-reverse-sync.test.ts src/core/project-manager.ts
git commit -m "修正(project): 僅在 --force 時啟用反向同步"
```

---

### Task 7: 修復 toggle --list 表格輸出對齊 v1

**Skills:** @test-driven-development

**Files:**
- Create: `tests/cli/toggle-list-parity.test.ts`
- Modify: `src/cli/toggle.ts`
- Create: `src/utils/toggle-config.ts`

**Step 1: Write the failing test**

```ts
test("toggle --list prints overall-enabled column", () => {
  const out = runCli(["toggle", "-l"]);
  expect(out).toContain("整體啟用");
  expect(out).toContain("停用項目");
});
```

**Step 2: Run test to verify it fails**

Run: `bun test tests/cli/toggle-list-parity.test.ts`
Expected: FAIL

**Step 3: Write minimal implementation**

```ts
// src/utils/toggle-config.ts
export interface ToggleConfig { [target: string]: { [type: string]: { enabled: boolean; disabled: string[] } } }

export async function loadToggleConfig(): Promise<ToggleConfig> { /* read ~/.config/custom-skills/toggle-config.yaml */ }
```

```ts
// src/cli/toggle.ts (list)
printTable(
  ["目標", "類型", "整體啟用", "停用項目"],
  rows.map((r) => [r.targetLabel, r.type, r.enabled ? "✓" : "✗", r.disabled.join(", ") || "-"])
);
```

**Step 4: Run test to verify it passes**

Run: `bun test tests/cli/toggle-list-parity.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/cli/toggle-list-parity.test.ts src/cli/toggle.ts src/utils/toggle-config.ts
git commit -m "修正(toggle): --list 輸出補齊整體啟用欄位"
```

---

### Task 8: 修復 toggle-config.yaml 相容邏輯（全域開關 + disabled 清單）

**Skills:** @test-driven-development

**Files:**
- Create: `tests/core/toggle-config-compat.test.ts`
- Modify: `src/cli/toggle.ts`
- Modify: `src/utils/toggle-config.ts`

**Step 1: Write the failing test**

```ts
test("disable writes name into toggle-config disabled list", async () => {
  await runToggleDisable("claude", "skills", "alpha");
  const cfg = await loadToggleConfig();
  expect(cfg.claude.skills.disabled).toContain("alpha");
});

test("--all --disable sets enabled=false", async () => {
  await runToggleAllDisable("claude", "skills");
  const cfg = await loadToggleConfig();
  expect(cfg.claude.skills.enabled).toBe(false);
});
```

**Step 2: Run test to verify it fails**

Run: `bun test tests/core/toggle-config-compat.test.ts`
Expected: FAIL

**Step 3: Write minimal implementation**

```ts
if (options.disable) {
  section.disabled = [...new Set([...section.disabled, options.name])];
}
if (options.enable) {
  section.disabled = section.disabled.filter((x) => x !== options.name);
}

if (options.all && options.disable) section.enabled = false;
if (options.all && options.enable) section.enabled = true;

await saveToggleConfig(config);
```

**Step 4: Run test to verify it passes**

Run: `bun test tests/core/toggle-config-compat.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/core/toggle-config-compat.test.ts src/cli/toggle.ts src/utils/toggle-config.ts
git commit -m "修正(toggle): 恢復 toggle-config 全域與 disabled 相容行為"
```

---

### Task 9: install 輸出流程對齊 v1（開頭/進度/收尾）

**Skills:** @test-driven-development @verification-before-completion

**Files:**
- Create: `tests/cli/install-output-parity.test.ts`
- Modify: `src/core/installer.ts`
- Modify: `src/cli/install.ts`
- Modify: `src/utils/progress-formatter.ts`

**Step 1: Write the failing test**

```ts
test("install prints start banner and completion banner", () => {
  const out = runInstallCli(["--skip-npm", "--skip-bun", "--skip-repos", "--skip-skills"]);
  expect(out).toContain("開始安裝...");
  expect(out).toContain("安裝完成！");
});
```

**Step 2: Run test to verify it fails**

Run: `bun test tests/cli/install-output-parity.test.ts`
Expected: FAIL

**Step 3: Write minimal implementation**

```ts
// src/core/installer.ts
onProgress("開始安裝...");
onProgress("檢查前置需求...");

// src/cli/install.ts
console.log(chalk.bold.blue("開始安裝..."));
// existing runInstall...
console.log(chalk.bold.green("安裝完成！"));
```

**Step 4: Run test to verify it passes**

Run: `bun test tests/cli/install-output-parity.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/cli/install-output-parity.test.ts src/core/installer.ts src/cli/install.ts src/utils/progress-formatter.ts
git commit -m "修正(install): 補齊 v1 開始與完成輸出流程"
```

---

### Task 10: update 輸出流程對齊 v1（進度與摘要）

**Skills:** @test-driven-development

**Files:**
- Create: `tests/cli/update-output-parity.test.ts`
- Modify: `src/core/updater.ts`
- Modify: `src/cli/update.ts`
- Modify: `src/utils/progress-formatter.ts`

**Step 1: Write the failing test**

```ts
test("update prints start banner, updated repos section and completion", () => {
  const out = runUpdateCli(["--skip-npm", "--skip-bun", "--skip-repos", "--skip-plugins"]);
  expect(out).toContain("開始更新...");
  expect(out).toContain("更新完成！");
  expect(out).toContain("提示：如需分發 Skills");
});
```

**Step 2: Run test to verify it fails**

Run: `bun test tests/cli/update-output-parity.test.ts`
Expected: FAIL

**Step 3: Write minimal implementation**

```ts
// src/core/updater.ts
onProgress("開始更新...");

// src/cli/update.ts
console.log(chalk.bold.blue("開始更新..."));
// existing render
console.log(chalk.bold.green("更新完成！"));
console.log(chalk.dim("提示：如需分發 Skills 到各工具目錄，請執行：ai-dev clone"));
```

**Step 4: Run test to verify it passes**

Run: `bun test tests/cli/update-output-parity.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/cli/update-output-parity.test.ts src/core/updater.ts src/cli/update.ts src/utils/progress-formatter.ts
git commit -m "修正(update): 補齊 v1 進度與完成提示輸出"
```

---

### Task 11: 修復 TUI Standards Enter 切換流程

**Skills:** @frontend-patterns @test-driven-development

**Files:**
- Create: `tests/tui/standards-switch.test.tsx`
- Modify: `src/tui/App.tsx`
- Modify: `src/tui/screens/StandardsScreen.tsx`

**Step 1: Write the failing test**

```tsx
test("press Enter on standards screen triggers switch", async () => {
  // mock performSwitchProfile and assert called with selected profile
});
```

**Step 2: Run test to verify it fails**

Run: `bun test tests/tui/standards-switch.test.tsx`
Expected: FAIL

**Step 3: Write minimal implementation**

```tsx
// App.tsx
onConfirmEnter: async () => {
  if (screen === "standards") {
    const profile = standardsProfiles[standardsIndex];
    if (!profile) return;
    const msg = await performSwitchProfile(profile);
    setConfirmMessage(msg);
    setScreen("confirm");
  }
}
```

**Step 4: Run test to verify it passes**

Run: `bun test tests/tui/standards-switch.test.tsx`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/tui/standards-switch.test.tsx src/tui/App.tsx src/tui/screens/StandardsScreen.tsx
git commit -m "修正(tui): Standards 畫面補上 Enter 切換流程"
```

---

### Task 12: 修復 TUI MCP e/f 實際動作（編輯器/資料夾）

**Skills:** @frontend-patterns @backend-patterns

**Files:**
- Create: `src/tui/utils/openers.ts`
- Create: `tests/tui/openers.test.ts`
- Modify: `src/tui/App.tsx`
- Modify: `src/tui/screens/SettingsScreen.tsx`

**Step 1: Write the failing test**

```ts
test("openInEditor uses $EDITOR or vim", async () => {
  // mock spawn and assert command
});
```

**Step 2: Run test to verify it fails**

Run: `bun test tests/tui/openers.test.ts`
Expected: FAIL

**Step 3: Write minimal implementation**

```ts
// src/tui/utils/openers.ts
export function openInEditor(path: string) {
  const editor = process.env.EDITOR ?? "vim";
  return Bun.spawn([editor, path], { stdin: "inherit", stdout: "inherit", stderr: "inherit" });
}

export function openInFileManager(dir: string) {
  const cmd = process.platform === "darwin" ? "open" : "xdg-open";
  return Bun.spawn([cmd, dir], { stdin: "ignore", stdout: "ignore", stderr: "ignore" });
}
```

**Step 4: Run test to verify it passes**

Run: `bun test tests/tui/openers.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add src/tui/utils/openers.ts tests/tui/openers.test.ts src/tui/App.tsx src/tui/screens/SettingsScreen.tsx
git commit -m "修正(tui): MCP 設定支援 e/f 開啟編輯器與資料夾"
```

---

### Task 13: 修復 TUI source 篩選（實際來源標記）

**Skills:** @frontend-patterns @refactoring-assistant

**Files:**
- Create: `src/tui/utils/source-index.ts`
- Create: `tests/tui/source-index.test.ts`
- Modify: `src/tui/hooks/useResources.ts`
- Modify: `src/cli/list.ts`

**Step 1: Write the failing test**

```ts
test("resolveSource returns upstream source instead of fixed custom-skills", async () => {
  expect(resolveSource("skills", "skill-creator", index)).toBe("anthropic-skills");
});
```

**Step 2: Run test to verify it fails**

Run: `bun test tests/tui/source-index.test.ts`
Expected: FAIL

**Step 3: Write minimal implementation**

```ts
// source-index.ts
export function resolveSource(type: "skills" | "commands" | "agents" | "workflows", name: string, index: SourceIndex): ResourceSource {
  return index[type].get(name) ?? "user-custom";
}
```

```ts
// useResources.ts
source: resolveSource(dirKey as any, name, sourceIndex),
```

**Step 4: Run test to verify it passes**

Run: `bun test tests/tui/source-index.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add src/tui/utils/source-index.ts tests/tui/source-index.test.ts src/tui/hooks/useResources.ts src/cli/list.ts
git commit -m "修正(tui): Source 篩選改用真實來源索引"
```

---

### Task 14: 更新 parity 報告與快照

**Skills:** @documentation-guide @code-review-assistant

**Files:**
- Modify: `docs/v1-v2-parity-report.md`
- Modify: `docs/plans/v1-output-snapshot.txt`
- Modify: `docs/plans/v2-output-snapshot.txt`

**Step 1: Write failing doc check (optional script)**

```bash
rg "⚠️|🔧" docs/v1-v2-parity-report.md
```

**Step 2: Run command to verify mismatch remains**

Run: `rg "⚠️|🔧" docs/v1-v2-parity-report.md`
Expected: 有結果（尚未更新）

**Step 3: Update report and snapshots**

```md
- 將已修復項目改為 ✅
- 將仍不對齊項目列為「殘餘差異」並附測試案例
- 更新 v2 snapshot 為最新實際輸出
```

**Step 4: Verify doc status**

Run: `rg "⚠️|🔧" docs/v1-v2-parity-report.md`
Expected: 僅保留「已確認未修」項目，無過時描述

**Step 5: Commit**

```bash
git add docs/v1-v2-parity-report.md docs/plans/v1-output-snapshot.txt docs/plans/v2-output-snapshot.txt
git commit -m "文件(parity): 更新 v1/v2 對齊報告與快照"
```

---

### Task 15: 全量驗證與整合提交

**Skills:** @verification-before-completion @requesting-code-review

**Files:**
- Modify: `CHANGELOG.md`（若使用者可見行為有變）

**Step 1: Run focused test suites**

Run: `bun test tests/cli/help-short-options-parity.test.ts tests/core/standards-manager-sync-target.test.ts tests/core/sync-engine-add-validation.test.ts tests/core/sync-engine-remove-confirm.test.ts tests/core/project-manager-reverse-sync.test.ts tests/cli/toggle-list-parity.test.ts tests/core/toggle-config-compat.test.ts tests/cli/install-output-parity.test.ts tests/cli/update-output-parity.test.ts tests/tui/standards-switch.test.tsx tests/tui/openers.test.ts tests/tui/source-index.test.ts`
Expected: PASS

**Step 2: Run full test suite**

Run: `bun test`
Expected: PASS

**Step 3: Run build**

Run: `bun run build`
Expected: exit code 0

**Step 4: Manual parity smoke checks**

Run:
```bash
bun src/cli.ts clone --help
bun src/cli.ts standards sync --help
bun src/cli.ts sync init --help
bun src/cli.ts sync remove ~/.claude
bun src/cli.ts toggle -t claude -T skills -l
bun src/cli.ts project init /tmp/ai-dev-plan-smoke
bun src/cli.ts tui --help
```
Expected: 與 v1 行為/輸出契約一致（包含短選項、確認提示、重啟提醒）

**Step 5: Commit**

```bash
git add -A
git commit -m "修正(parity): 完成 v2 與 v1 CLI/TUI 輸出與邏輯對齊"
```
