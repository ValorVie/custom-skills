# v2 Full Parity Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make v2 ai-dev CLI output and behavior identical to v1 (Python/Rich) across language, table formatting, data correctness, and Claude Code lifecycle.

**Architecture:** Bottom-up approach — fix shared utilities first (i18n, formatter), then update each CLI command, then add missing core modules. Each task is independently testable.

**Tech Stack:** Bun, Commander.js, chalk, cli-table3, ora

---

## Task 1: i18n — Change default locale and add CLI description keys

**Files:**
- Modify: `src/utils/i18n.ts:3` (DEFAULT_LOCALE)
- Modify: `src/utils/i18n.ts:5-103` (add keys)
- Modify: `tests/cli/smoke.test.ts` (update expected values)

**Step 1: Write the failing test**

In `tests/cli/smoke.test.ts`, update the existing `--help shows top-level commands` test to also check for Chinese descriptions:

```typescript
test("--help shows zh-TW descriptions by default", () => {
  const result = runCli(["--help"]);
  expect(result.exitCode).toBe(0);
  expect(result.stdout).toContain("首次安裝 AI 開發環境");
  expect(result.stdout).toContain("更新工具與拉取儲存庫");
  expect(result.stdout).toContain("分發 Skills 到各工具目錄");
});
```

**Step 2: Run test to verify it fails**

Run: `bun test tests/cli/smoke.test.ts -t "zh-TW"`
Expected: FAIL — output still shows English descriptions

**Step 3: Implement — change DEFAULT_LOCALE and add i18n keys**

In `src/utils/i18n.ts`:

1. Change line 3: `const DEFAULT_LOCALE: Locale = "zh-TW";`

2. Add all CLI description keys to both locales. The full key list for command descriptions:

```typescript
// en locale — add these keys:
"cli.description": "AI Development Environment Setup CLI",
"cmd.install": "Install AI development environment",
"cmd.update": "Update packages and repositories",
"cmd.clone": "Distribute resources to configured AI tool directories",
"cmd.status": "Check environment status and tool versions",
"cmd.list": "List installed Skills, Commands, Agents (including disabled)",
"cmd.toggle": "Enable or disable specific resources for a tool",
"cmd.add_repo": "Add and track an upstream repository",
"cmd.add_custom_repo": "Add and track a custom repository",
"cmd.update_custom_repo": "Update all custom repositories",
"cmd.test": "Run tests and output raw results",
"cmd.coverage": "Run coverage analysis and output raw results",
"cmd.derive_tests": "Read OpenSpec spec file contents",
"cmd.tui": "Launch interactive TUI",
"cmd.project": "Project-level initialization and update operations",
"cmd.project_init": "Initialize project from template",
"cmd.project_update": "Run project update commands",
"cmd.standards": "Manage standards configuration (overlap-based)",
"cmd.standards_status": "Show current standards status",
"cmd.standards_list": "List available profiles",
"cmd.standards_switch": "Switch active profile",
"cmd.standards_show": "Show profile content",
"cmd.standards_overlaps": "Show overlapping definitions across profiles",
"cmd.standards_sync": "Sync standards state to .disabled directory",
"cmd.hooks": "ECC Hooks Plugin management commands",
"cmd.hooks_install": "Install hooks plugin",
"cmd.hooks_uninstall": "Uninstall hooks plugin",
"cmd.hooks_status": "Show hooks plugin status",
"cmd.sync": "Manage cross-device sync (Git backend)",
"cmd.sync_init": "Initialize sync config",
"cmd.sync_push": "Push local sync directories into repo dir",
"cmd.sync_pull": "Pull from repo dir into local directories",
"cmd.sync_status": "Show sync status",
"cmd.sync_add": "Add a directory to sync",
"cmd.sync_remove": "Remove directory from sync",
"cmd.mem": "Manage claude-mem cross-device sync (HTTP API backend)",
"cmd.mem_register": "Register this device to sync server",
"cmd.mem_push": "Push local data to sync server",
"cmd.mem_pull": "Pull remote data from sync server",
"cmd.mem_status": "Show mem sync status",
"cmd.mem_reindex": "Reindex local observations",
"cmd.mem_cleanup": "Remove duplicate observations",
"cmd.mem_auto": "Configure automatic memory sync",

// Option help texts
"opt.lang": "Output language (en|zh-TW)",
"opt.json": "以 JSON 格式輸出",
"opt.skip_npm": "Skip global NPM package installation",
"opt.skip_bun": "Skip Bun package installation",
"opt.skip_repos": "Skip repository cloning",
"opt.skip_skills": "Skip skill distribution",
"opt.skip_plugins": "Skip plugin marketplace update",
"opt.sync_project": "Sync project template files",
"opt.force": "Force overwrite",
"opt.skip_conflicts": "Skip conflicting files",
"opt.backup": "Backup before overwrite",
"opt.no_sync_project": "Skip project-template synchronization",
"opt.hide_disabled": "Hide disabled resources",
"opt.target": "Target platform",
"opt.type": "Resource type",
"opt.name": "Resource name",
"opt.enable": "Enable resource",
"opt.disable": "Disable resource",
"opt.list": "List resource toggle state",
"opt.branch": "Tracked branch",
"opt.skip_clone": "Skip cloning and only register config",
"opt.analyze": "Analyze repository structure",
"opt.no_clone": "Do not clone before registering",
"opt.fix": "Create missing standard directories",
"opt.verbose": "Verbose output",
"opt.fail_fast": "Stop on first failure",
"opt.keyword": "Filter tests by name",
"opt.framework": "Test framework (bun|npm|pytest|phpunit)",
"opt.source": "Source path",
"opt.dry_run": "Preview only",
"opt.remote": "Remote git URL",
"opt.no_delete": "Keep local extra files",
"opt.server": "Sync server URL",
"opt.device_name": "Device name",
"opt.admin_secret": "Admin secret",
"opt.interval": "Auto-sync interval in minutes",
"opt.yes": "Skip confirmation prompt",
"opt.only": "Only run one tool (openspec|uds)",
"opt.profile": "Ignore profile",
"opt.ignore": "Custom ignore patterns",

// zh-TW locale — add these keys:
"cli.description": "AI 開發環境設定 CLI",
"cmd.install": "首次安裝 AI 開發環境",
"cmd.update": "更新工具與拉取儲存庫",
"cmd.clone": "分發 Skills 到各工具目錄",
"cmd.status": "檢查環境狀態與工具版本",
"cmd.list": "列出已安裝的 Skills、Commands、Agents（包含停用的）",
"cmd.toggle": "啟用/停用特定工具的特定資源",
"cmd.add_repo": "新增上游 repo 並開始追蹤",
"cmd.add_custom_repo": "新增自訂 repo 並開始追蹤",
"cmd.update_custom_repo": "更新所有自訂 repo",
"cmd.test": "執行測試並輸出原始結果",
"cmd.coverage": "執行覆蓋率分析並輸出原始結果",
"cmd.derive_tests": "讀取 OpenSpec specs 檔案內容",
"cmd.tui": "啟動互動式 TUI 介面",
"cmd.project": "專案級別的初始化與更新操作",
"cmd.project_init": "初始化專案模板",
"cmd.project_update": "執行專案更新指令",
"cmd.standards": "管理標準體系配置（基於重疊檢測）",
"cmd.standards_status": "顯示目前標準體系狀態",
"cmd.standards_list": "列出可用的 profile",
"cmd.standards_switch": "切換啟用的 profile",
"cmd.standards_show": "顯示 profile 內容",
"cmd.standards_overlaps": "顯示跨 profile 的重疊定義",
"cmd.standards_sync": "同步標準體系狀態至 .disabled 目錄",
"cmd.hooks": "ECC Hooks Plugin 管理指令",
"cmd.hooks_install": "安裝 hooks plugin",
"cmd.hooks_uninstall": "移除 hooks plugin",
"cmd.hooks_status": "顯示 hooks plugin 狀態",
"cmd.sync": "管理跨裝置同步（Git backend）",
"cmd.sync_init": "初始化同步設定",
"cmd.sync_push": "推送本地同步目錄至 repo 目錄",
"cmd.sync_pull": "從 repo 目錄拉取至本地目錄",
"cmd.sync_status": "顯示同步狀態",
"cmd.sync_add": "新增同步目錄",
"cmd.sync_remove": "移除同步目錄",
"cmd.mem": "管理 claude-mem 跨裝置同步（HTTP API backend）",
"cmd.mem_register": "註冊此裝置至同步伺服器",
"cmd.mem_push": "推送本地資料至同步伺服器",
"cmd.mem_pull": "從同步伺服器拉取遠端資料",
"cmd.mem_status": "顯示記憶同步狀態",
"cmd.mem_reindex": "重新索引本地 observations",
"cmd.mem_cleanup": "清除重複的 observations",
"cmd.mem_auto": "設定自動記憶同步",

// Option help texts (zh-TW)
"opt.lang": "輸出語言 (en|zh-TW)",
"opt.json": "以 JSON 格式輸出",
"opt.skip_npm": "跳過 NPM 套件安裝",
"opt.skip_bun": "跳過 Bun 套件安裝",
"opt.skip_repos": "跳過 repo 複製",
"opt.skip_skills": "跳過 skill 分發",
"opt.skip_plugins": "跳過 plugin marketplace 更新",
"opt.sync_project": "同步專案模板檔案",
"opt.force": "強制覆寫",
"opt.skip_conflicts": "略過衝突檔案",
"opt.backup": "覆寫前備份",
"opt.no_sync_project": "略過 project-template 同步",
"opt.hide_disabled": "隱藏已停用的資源",
"opt.target": "目標平台",
"opt.type": "資源類型",
"opt.name": "資源名稱",
"opt.enable": "啟用資源",
"opt.disable": "停用資源",
"opt.list": "列出資源切換狀態",
"opt.branch": "追蹤分支",
"opt.skip_clone": "只註冊設定，不複製",
"opt.analyze": "分析 repo 結構",
"opt.no_clone": "註冊前不複製",
"opt.fix": "建立缺少的標準目錄",
"opt.verbose": "詳細輸出",
"opt.fail_fast": "第一個失敗即停止",
"opt.keyword": "依名稱篩選測試",
"opt.framework": "測試框架 (bun|npm|pytest|phpunit)",
"opt.source": "來源路徑",
"opt.dry_run": "僅預覽",
"opt.remote": "遠端 Git URL",
"opt.no_delete": "保留本地多餘檔案",
"opt.server": "同步伺服器 URL",
"opt.device_name": "裝置名稱",
"opt.admin_secret": "管理員密鑰",
"opt.interval": "自動同步間隔（分鐘）",
"opt.yes": "跳過確認提示",
"opt.only": "僅執行特定工具 (openspec|uds)",
"opt.profile": "Ignore profile",
"opt.ignore": "自訂忽略模式",
```

**Step 4: Run test to verify it passes**

Run: `bun test tests/cli/smoke.test.ts -t "zh-TW"`
Expected: PASS

**Step 5: Commit**

```bash
git add src/utils/i18n.ts tests/cli/smoke.test.ts
git commit -m "功能(i18n): 預設語言改為 zh-TW 並新增 CLI 說明 i18n keys"
```

---

## Task 2: i18n — Wire all CLI commands to use t() for descriptions and options

**Files:**
- Modify: `src/cli/index.ts`
- Modify: `src/cli/install.ts`
- Modify: `src/cli/update.ts`
- Modify: `src/cli/clone.ts`
- Modify: `src/cli/status.ts`
- Modify: `src/cli/list.ts`
- Modify: `src/cli/toggle.ts`
- Modify: `src/cli/add-repo.ts`
- Modify: `src/cli/add-custom-repo.ts`
- Modify: `src/cli/update-custom-repo.ts`
- Modify: `src/cli/test.ts`
- Modify: `src/cli/coverage.ts`
- Modify: `src/cli/derive-tests.ts`
- Modify: `src/cli/tui.ts`
- Modify: `src/cli/project/index.ts`
- Modify: `src/cli/standards/index.ts`
- Modify: `src/cli/hooks/index.ts`
- Modify: `src/cli/sync/index.ts`
- Modify: `src/cli/mem/index.ts`

**Note:** Commander.js evaluates `.description()` and `.option()` at definition time, but our `t()` reads the current locale at call time. Since `createProgram()` runs after the module is loaded, and `setLocale()` defaults to zh-TW now, all descriptions will already be in Chinese. The `--lang en` preAction hook only affects runtime messages, not help text — this is acceptable (matches v1 behavior where help is always zh-TW).

**However**, Commander.js evaluates `.description()` at definition time (when `createProgram()` runs), so we need a **lazy description** approach. The simplest: use `t()` calls directly in the `.description()` string since they execute during `createProgram()` which runs after DEFAULT_LOCALE is already set.

**Step 1: Update `src/cli/index.ts`**

Replace all hardcoded strings with `t()` calls:

```typescript
export function createProgram(): Command {
  const program = new Command()
    .name("ai-dev")
    .description(t("cli.description"))
    .version("2.0.0")
    .option("--lang <locale>", t("opt.lang"));
  // ... rest unchanged
```

**Step 2: Update each command file**

For every command file, replace `.description("English text")` with `.description(t("cmd.xxx"))` and `.option("--flag", "English text")` with `.option("--flag", t("opt.xxx"))`.

Example for `src/cli/install.ts`:
```typescript
import { t } from "../utils/i18n";
// ...
.description(t("cmd.install"))
.option("--skip-npm", t("opt.skip_npm"))
.option("--skip-bun", t("opt.skip_bun"))
.option("--skip-repos", t("opt.skip_repos"))
.option("--skip-skills", t("opt.skip_skills"))
.option("--sync-project", t("opt.sync_project"))
.option("--json", t("opt.json"))
```

Repeat for all 18 command files. Each file already imports `t` from `../utils/i18n` or `../../utils/i18n`.

**Step 3: Run all smoke tests**

Run: `bun test tests/cli/smoke.test.ts`
Expected: All pass (some tests check for option names like `--skip-skills` which don't change)

**Step 4: Commit**

```bash
git add src/cli/
git commit -m "功能(i18n): 所有 CLI 指令說明與選項改用 t() 翻譯"
```

---

## Task 3: Formatter — Add table title and Rich-style thick borders

**Files:**
- Modify: `src/utils/formatter.ts`
- Test: `tests/utils/formatter.test.ts` (create)

**Step 1: Write the failing test**

Create `tests/utils/formatter.test.ts`:

```typescript
import { describe, expect, test } from "bun:test";
import { printTable } from "../../src/utils/formatter";

// We'll capture console.log output
function captureLog(fn: () => void): string {
  const logs: string[] = [];
  const orig = console.log;
  console.log = (...args: unknown[]) => logs.push(args.join(" "));
  fn();
  console.log = orig;
  return logs.join("\n");
}

describe("printTable", () => {
  test("renders with title when provided", () => {
    const output = captureLog(() => {
      printTable(["A", "B"], [["1", "2"]], { title: "Test Title" });
    });
    expect(output).toContain("Test Title");
    expect(output).toContain("1");
  });

  test("renders thick borders by default", () => {
    const output = captureLog(() => {
      printTable(["A"], [["1"]]);
    });
    // Should use thick border chars like ━ ┃ ┏ ┓
    expect(output).toContain("━");
  });
});
```

**Step 2: Run test to verify it fails**

Run: `bun test tests/utils/formatter.test.ts`
Expected: FAIL — printTable doesn't accept options parameter

**Step 3: Implement**

Update `src/utils/formatter.ts`:

```typescript
import chalk from "chalk";
import Table from "cli-table3";
import ora, { type Ora } from "ora";

// Rich-style thick border characters (matching Python Rich's default table style)
const RICH_CHARS = {
  top: "━",
  "top-mid": "┳",
  "top-left": "┏",
  "top-right": "┓",
  bottom: "━",
  "bottom-mid": "┻",
  "bottom-left": "┗",
  "bottom-right": "┛",
  left: "┃",
  "left-mid": "┠",
  mid: "─",
  "mid-mid": "┼",
  right: "┃",
  "right-mid": "┨",
  middle: "│",
};

// Thin border for body rows (Rich uses thick for header, thin for body)
const RICH_BODY_CHARS = {
  ...RICH_CHARS,
  "left-mid": "├",
  "right-mid": "┤",
  "mid-mid": "┼",
  mid: "─",
  middle: "│",
};

export interface TableOptions {
  title?: string;
}

export function printTable(
  headers: string[],
  rows: string[][],
  options?: TableOptions,
): void {
  if (options?.title) {
    console.log(chalk.bold(`    ${options.title}    `));
  }

  const table = new Table({
    head: headers,
    chars: RICH_CHARS,
    style: {
      head: ["bold"],
    },
  });

  for (const row of rows) {
    table.push(row);
  }

  console.log(table.toString());
}
```

**Step 4: Run test to verify it passes**

Run: `bun test tests/utils/formatter.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add src/utils/formatter.ts tests/utils/formatter.test.ts
git commit -m "功能(formatter): printTable 新增 title 參數與 Rich 風格粗邊框"
```

---

## Task 4: status — Restructure to 4 grouped tables with Chinese headers

**Files:**
- Modify: `src/utils/i18n.ts` (add status-specific keys)
- Modify: `src/cli/status.ts`

**Step 1: Add i18n keys for status command**

Add to both locales in `src/utils/i18n.ts`:

```typescript
// en
"status.title": "AI Development Environment Status Check",
"status.table_core_tools": "Core Tools",
"status.table_npm_packages": "Global NPM Packages",
"status.table_repos": "Config Repositories",
"status.table_upstream": "Upstream Sync Status",
"status.col_tool": "Tool",
"status.col_status": "Status",
"status.col_version_path": "Version/Path",
"status.col_package": "Package",
"status.col_name": "Name",
"status.col_local_status": "Local Status",
"status.col_synced_at": "Synced At",
"status.installed": "Installed",
"status.missing": "Missing",
"status.up_to_date": "✓ Latest",
"status.has_updates": "↑ Updates available",
"status.behind_n": "⚠ Behind {count} commits",

// zh-TW
"status.title": "AI 開發環境狀態檢查",
"status.table_core_tools": "核心工具",
"status.table_npm_packages": "全域 NPM 套件",
"status.table_repos": "設定儲存庫",
"status.table_upstream": "上游同步狀態",
"status.col_tool": "工具",
"status.col_status": "狀態",
"status.col_version_path": "版本/路徑",
"status.col_package": "套件",
"status.col_name": "名稱",
"status.col_local_status": "本地狀態",
"status.col_synced_at": "同步於",
"status.installed": "已安裝",
"status.missing": "未安裝",
"status.up_to_date": "✓ 最新",
"status.has_updates": "↑ 有可用更新",
"status.behind_n": "⚠ 落後 {count} 個 commit",
```

**Step 2: Rewrite `src/cli/status.ts`**

```typescript
import type { Command } from "commander";

import { checkEnvironment } from "../core/status-checker";
import { printTable } from "../utils/formatter";
import { t } from "../utils/i18n";

export function registerStatusCommand(program: Command): void {
  program
    .command("status")
    .description(t("cmd.status"))
    .option("--json", t("opt.json"))
    .action(async (options: { json?: boolean }) => {
      const status = await checkEnvironment();

      if (options.json) {
        console.log(JSON.stringify(status, null, 2));
        return;
      }

      console.log(t("status.title"));

      // Table 1: Core Tools
      printTable(
        [t("status.col_tool"), t("status.col_status"), t("status.col_version_path")],
        [
          ["Node.js", status.node.installed ? t("status.installed") : t("status.missing"), status.node.version ?? ""],
          ["Git", status.git.installed ? t("status.installed") : t("status.missing"), status.git.version ?? ""],
          ["Bun", status.bun.installed ? t("status.installed") : t("status.missing"), status.bun.version ?? ""],
          ["gh", status.gh.installed ? t("status.installed") : t("status.missing"), status.gh.version ?? ""],
        ],
        { title: t("status.table_core_tools") },
      );

      // Table 2: NPM Packages
      printTable(
        [t("status.col_package"), t("status.col_status")],
        status.npmPackages.map((pkg) => [
          pkg.name,
          pkg.installed ? t("status.installed") : t("status.missing"),
        ]),
        { title: t("status.table_npm_packages") },
      );

      // Table 3: Config Repositories
      const repoRows = status.repos.map((repo) => {
        let localStatus: string;
        if (repo.syncState === "updates-available") {
          localStatus = t("status.has_updates");
        } else if (repo.syncState === "up-to-date") {
          localStatus = t("status.up_to_date");
        } else {
          localStatus = repo.syncState;
        }
        return [repo.name, localStatus];
      });

      printTable(
        [t("status.col_name"), t("status.col_local_status")],
        repoRows,
        { title: t("status.table_repos") },
      );

      // Table 4: Upstream Sync Status
      if (status.upstreamSync.length > 0) {
        printTable(
          [t("status.col_name"), t("status.col_synced_at"), t("status.col_status")],
          status.upstreamSync.map((item) => [
            item.name,
            item.syncedAt ? item.syncedAt.slice(5, 10) : "",
            item.status === "behind"
              ? t("status.behind_n", { count: String(item.behind) })
              : item.status,
          ]),
          { title: t("status.table_upstream") },
        );
      }
    });
}
```

**Step 3: Run smoke test**

Run: `bun test tests/cli/smoke.test.ts -t "status"`
Expected: PASS (status --json still works, status --help still shows "status")

**Step 4: Commit**

```bash
git add src/utils/i18n.ts src/cli/status.ts
git commit -m "功能(status): 重構為 4 個分組表格，使用中文標題與欄位"
```

---

## Task 5: list — Group by Target+Type with Chinese columns

**Files:**
- Modify: `src/utils/i18n.ts` (add list-specific keys)
- Modify: `src/cli/list.ts`

**Step 1: Add i18n keys**

```typescript
// en
"list.col_name": "Name",
"list.col_source": "Source",
"list.col_status": "Status",

// zh-TW
"list.col_name": "名稱",
"list.col_source": "來源",
"list.col_status": "狀態",
```

**Step 2: Rewrite list output section in `src/cli/list.ts`**

Replace the flat table (lines 282-293) with grouped tables:

```typescript
// Group by target+type
const groups = new Map<string, ResourceItem[]>();
for (const item of output) {
  const key = `${item.target} - ${item.type.charAt(0).toUpperCase() + item.type.slice(1)}`;
  const group = groups.get(key) ?? [];
  group.push(item);
  groups.set(key, group);
}

for (const [groupTitle, items] of groups) {
  printTable(
    [t("list.col_name"), t("list.col_source"), t("list.col_status")],
    items.map((item) => [
      item.name,
      item.source,
      item.enabled
        ? chalk.green(t("list.status_enabled"))
        : chalk.red(t("list.status_disabled")),
    ]),
    { title: groupTitle },
  );
}
```

**Step 3: Run smoke test**

Run: `bun test tests/cli/smoke.test.ts -t "list"`
Expected: PASS

**Step 4: Commit**

```bash
git add src/utils/i18n.ts src/cli/list.ts
git commit -m "功能(list): 依 Target+Type 分組表格輸出，使用中文欄位"
```

---

## Task 6: sync status — Use table format

**Files:**
- Modify: `src/utils/i18n.ts` (add sync-specific keys)
- Modify: `src/cli/sync/index.ts`

**Step 1: Add i18n keys**

```typescript
// en
"sync.col_field": "Field",
"sync.col_value": "Value",
"sync.initialized": "Initialized",
"sync.repo_dir": "Repo Dir",
"sync.local_changes": "Local Changes",
"sync.remote_behind": "Remote Behind",
"sync.tracked_dirs": "Tracked Directories",

// zh-TW
"sync.col_field": "項目",
"sync.col_value": "值",
"sync.initialized": "已初始化",
"sync.repo_dir": "Repo 目錄",
"sync.local_changes": "本地變更",
"sync.remote_behind": "遠端落後",
"sync.tracked_dirs": "追蹤目錄數",
```

**Step 2: Update sync status handler**

Replace plain text output in the `sync status` action with:

```typescript
printTable(
  [t("sync.col_field"), t("sync.col_value")],
  [
    [t("sync.initialized"), String(status.initialized)],
    [t("sync.repo_dir"), status.repoDir],
    [t("sync.local_changes"), String(status.localChanges)],
    [t("sync.remote_behind"), String(status.remoteBehind)],
    ...(status.config
      ? [[t("sync.tracked_dirs"), String(status.config.directories.length)]]
      : []),
  ],
);
```

**Step 3: Run smoke test**

Run: `bun test tests/cli/smoke.test.ts -t "sync status"`
Expected: PASS

**Step 4: Commit**

```bash
git add src/utils/i18n.ts src/cli/sync/index.ts
git commit -m "功能(sync): sync status 改用表格格式輸出"
```

---

## Task 7: mem status — Use table format

**Files:**
- Modify: `src/utils/i18n.ts` (add mem-specific keys)
- Modify: `src/cli/mem/index.ts`

**Step 1: Add i18n keys**

```typescript
// en
"mem.col_field": "Field",
"mem.col_value": "Value",
"mem.device": "Device",
"mem.local_obs": "Local Observations",
"mem.pending_push": "Pending Push",
"mem.remote_obs": "Remote Observations",
"mem.remote_unavailable": "unavailable",
"mem.unregistered": "(unregistered)",

// zh-TW
"mem.col_field": "項目",
"mem.col_value": "值",
"mem.device": "裝置",
"mem.local_obs": "本地 Observations",
"mem.pending_push": "待推送",
"mem.remote_obs": "遠端 Observations",
"mem.remote_unavailable": "無法取得",
"mem.unregistered": "（未註冊）",
```

**Step 2: Update mem status handler**

Replace plain text output with:

```typescript
import { printTable } from "../../utils/formatter";
import { t } from "../../utils/i18n";

// In mem status action:
const rows: string[][] = [
  [t("mem.device"), result.config.deviceName || t("mem.unregistered")],
  [t("mem.local_obs"), String(result.localObservations)],
  [t("mem.pending_push"), String(result.pendingPushCount)],
];

if (result.remoteStatus) {
  rows.push([t("mem.remote_obs"), String(result.remoteStatus.observations ?? 0)]);
} else {
  rows.push([t("mem.remote_obs"), t("mem.remote_unavailable")]);
}

printTable([t("mem.col_field"), t("mem.col_value")], rows);
```

**Step 3: Run smoke test**

Run: `bun test tests/cli/smoke.test.ts -t "mem status"`
Expected: PASS

**Step 4: Commit**

```bash
git add src/utils/i18n.ts src/cli/mem/index.ts
git commit -m "功能(mem): mem status 改用表格格式輸出"
```

---

## Task 8: install/update CLI — Use formatted output with tables

**Files:**
- Modify: `src/utils/i18n.ts` (add install/update output keys)
- Modify: `src/cli/install.ts`
- Modify: `src/cli/update.ts`

**Step 1: Add i18n keys for install/update output**

```typescript
// en
"install.summary": "Install Summary",
"install.prerequisites": "Prerequisites",
"install.claude_code": "Claude Code",
"install.installed": "installed",
"install.missing": "missing",
"update.summary": "Update Summary",

// zh-TW
"install.summary": "安裝摘要",
"install.prerequisites": "前置需求",
"install.claude_code": "Claude Code",
"install.installed": "已安裝",
"install.missing": "未安裝",
"update.summary": "更新摘要",
```

**Step 2: Update install.ts and update.ts output sections**

Replace all plain text `console.log` output with `printTable` calls and `t()` strings. The `--json` path stays unchanged; only the human-readable output is reformatted.

**Step 3: Run smoke test**

Run: `bun test tests/cli/smoke.test.ts`
Expected: All pass

**Step 4: Commit**

```bash
git add src/utils/i18n.ts src/cli/install.ts src/cli/update.ts
git commit -m "功能(cli): install/update 人類可讀輸出改用表格與中文"
```

---

## Task 9: Claude Code Manager — New core module

**Files:**
- Create: `src/core/claude-code-manager.ts`
- Create: `tests/core/claude-code-manager.test.ts`

**Step 1: Write the failing test**

Create `tests/core/claude-code-manager.test.ts`:

```typescript
import { describe, expect, mock, test } from "bun:test";
import {
  getClaudeInstallType,
  showClaudeStatus,
  updateClaudeCode,
} from "../../src/core/claude-code-manager";

describe("getClaudeInstallType", () => {
  test("returns null when claude not found", async () => {
    const result = await getClaudeInstallType({
      commandExistsFn: () => false,
      runCommandFn: async () => ({ exitCode: 1, stdout: "", stderr: "" }),
    });
    expect(result).toBeNull();
  });

  test("returns 'npm' when installed via npm", async () => {
    const result = await getClaudeInstallType({
      commandExistsFn: (cmd) => cmd === "claude" || cmd === "npm",
      runCommandFn: async (args) => {
        if (args.includes("npm") && args.includes("list")) {
          return { exitCode: 0, stdout: "@anthropic-ai/claude-code@1.0.0", stderr: "" };
        }
        return { exitCode: 1, stdout: "", stderr: "" };
      },
    });
    expect(result).toBe("npm");
  });

  test("returns 'native' when not npm", async () => {
    const result = await getClaudeInstallType({
      commandExistsFn: (cmd) => cmd === "claude",
      runCommandFn: async (args) => {
        if (args.includes("npm") && args.includes("list")) {
          return { exitCode: 1, stdout: "", stderr: "" };
        }
        return { exitCode: 0, stdout: "", stderr: "" };
      },
    });
    expect(result).toBe("native");
  });
});
```

**Step 2: Run test to verify it fails**

Run: `bun test tests/core/claude-code-manager.test.ts`
Expected: FAIL — module doesn't exist

**Step 3: Implement `src/core/claude-code-manager.ts`**

```typescript
import { commandExists, runCommand } from "../utils/system";
import { t } from "../utils/i18n";

export type ClaudeInstallType = "npm" | "native" | null;

export interface ClaudeManagerDeps {
  commandExistsFn?: typeof commandExists;
  runCommandFn?: typeof runCommand;
}

export async function getClaudeInstallType(
  deps: ClaudeManagerDeps = {},
): Promise<ClaudeInstallType> {
  const commandExistsFn = deps.commandExistsFn ?? commandExists;
  const runCommandFn = deps.runCommandFn ?? runCommand;

  if (!commandExistsFn("claude")) {
    return null;
  }

  // Check if installed via npm
  const npmCheck = await runCommandFn(
    ["npm", "list", "-g", "@anthropic-ai/claude-code", "--depth=0"],
    { check: false, timeoutMs: 15_000 },
  );

  if (npmCheck.exitCode === 0 && npmCheck.stdout.includes("claude-code")) {
    return "npm";
  }

  return "native";
}

export async function showClaudeStatus(
  onProgress: (msg: string) => void,
  deps: ClaudeManagerDeps = {},
): Promise<{ type: ClaudeInstallType; version: string | null }> {
  const runCommandFn = deps.runCommandFn ?? runCommand;
  const type = await getClaudeInstallType(deps);

  if (type === null) {
    showInstallInstructions(onProgress);
    return { type: null, version: null };
  }

  // Get version
  const versionResult = await runCommandFn(["claude", "--version"], {
    check: false,
    timeoutMs: 10_000,
  });
  const version = versionResult.exitCode === 0
    ? versionResult.stdout.trim().split(/\r?\n/)[0] ?? null
    : null;

  if (type === "npm") {
    onProgress("⚠ Claude Code 透過 npm 安裝，建議改用原生安裝方式");
    onProgress("  移除 npm 版本: npm uninstall -g @anthropic-ai/claude-code");
    showInstallInstructions(onProgress);
  } else {
    onProgress(`✓ Claude Code (native) ${version ?? ""}`);
  }

  return { type, version };
}

export async function updateClaudeCode(
  onProgress: (msg: string) => void,
  deps: ClaudeManagerDeps = {},
): Promise<{ success: boolean; message?: string }> {
  const runCommandFn = deps.runCommandFn ?? runCommand;
  const type = await getClaudeInstallType(deps);

  if (type === null) {
    onProgress("Claude Code 未安裝");
    showInstallInstructions(onProgress);
    return { success: false, message: "not installed" };
  }

  if (type === "npm") {
    onProgress("更新 Claude Code (npm)...");
    const result = await runCommandFn(
      ["npm", "install", "-g", "@anthropic-ai/claude-code@latest"],
      { check: false, timeoutMs: 120_000 },
    );
    if (result.exitCode === 0) {
      onProgress("⚠ 建議改用原生安裝方式以取得最佳體驗");
    }
    return {
      success: result.exitCode === 0,
      message: result.exitCode === 0 ? undefined : result.stderr,
    };
  }

  // native
  onProgress("更新 Claude Code...");
  const result = await runCommandFn(["claude", "update"], {
    check: false,
    timeoutMs: 120_000,
  });
  return {
    success: result.exitCode === 0,
    message: result.exitCode === 0 ? undefined : result.stderr,
  };
}

export function showInstallInstructions(
  onProgress: (msg: string) => void,
): void {
  onProgress("安裝 Claude Code:");
  onProgress("  macOS/Linux: curl -fsSL https://claude.ai/install.sh | sh");
  onProgress("  macOS (Homebrew): brew install claude");
  onProgress("  Windows: winget install Anthropic.Claude");
}
```

**Step 4: Run test to verify it passes**

Run: `bun test tests/core/claude-code-manager.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add src/core/claude-code-manager.ts tests/core/claude-code-manager.test.ts
git commit -m "功能(core): 新增 claude-code-manager 模組（安裝類型偵測/更新/安裝指引）"
```

---

## Task 10: Integrate Claude Code into install flow

**Files:**
- Modify: `src/core/installer.ts`
- Modify: `src/utils/i18n.ts` (add install-specific Claude Code keys)

**Step 1: Add Claude Code step into `runInstall()`**

After prerequisites check and before NPM packages, add:

```typescript
import { showClaudeStatus } from "./claude-code-manager";

// In runInstall(), after prerequisiteDetails section:
onProgress("檢查 Claude Code 安裝狀態...");
const claudeStatus = await showClaudeStatus(onProgress, {
  commandExistsFn,
  runCommandFn,
});
result.claudeCode = {
  installed: claudeStatus.type !== null,
  version: claudeStatus.version,
};
```

**Step 2: Run smoke test**

Run: `bun test tests/cli/smoke.test.ts -t "install"`
Expected: PASS

**Step 3: Commit**

```bash
git add src/core/installer.ts src/utils/i18n.ts
git commit -m "功能(install): 整合 Claude Code 安裝狀態檢查至 install 流程"
```

---

## Task 11: Integrate Claude Code into update flow

**Files:**
- Modify: `src/core/updater.ts`

**Step 1: Replace simple `claude update` with `updateClaudeCode()`**

In `runUpdate()`, replace the existing Claude Code section (lines 257-268) with:

```typescript
import { updateClaudeCode } from "./claude-code-manager";

// Replace the claude update section:
onProgress("更新 Claude Code...");
const claudeResult = await updateClaudeCode(onProgress, {
  commandExistsFn,
  runCommandFn,
});
result.claudeCode = {
  name: "claude-code",
  success: claudeResult.success,
  message: claudeResult.message,
};
```

**Step 2: Run smoke test**

Run: `bun test tests/cli/smoke.test.ts -t "update"`
Expected: PASS

**Step 3: Commit**

```bash
git add src/core/updater.ts
git commit -m "功能(update): 整合 claude-code-manager 至 update 流程"
```

---

## Task 12: Final — Run full test suite and fix any regressions

**Files:**
- Modify: `tests/cli/smoke.test.ts` (update any broken assertions)
- Modify: Various test files as needed

**Step 1: Run all tests**

Run: `bun test`
Expected: All tests pass. If any fail, fix the assertions.

**Step 2: Run lint and type check**

Run: `bun run lint && bunx tsc --noEmit`
Expected: Clean

**Step 3: Manual smoke test**

Run key commands to verify visual output:
```bash
bun run src/cli.ts status
bun run src/cli.ts list --target claude --type skills
bun run src/cli.ts --help
bun run src/cli.ts install --help
bun run src/cli.ts update --help
bun run src/cli.ts sync status
bun run src/cli.ts mem status
bun run src/cli.ts standards status
bun run src/cli.ts standards overlaps
```

Verify:
- All output is in Chinese by default
- Tables have thick borders (━┃┏┓)
- Tables have colored titles
- status shows 4 grouped tables
- list groups by Target+Type
- sync status and mem status use table format

**Step 4: Commit final fixes**

```bash
git add -A
git commit -m "修正(v2): 修復全對齊後的測試回歸與 lint 問題"
```

---

## Summary

| Task | What | Files | Est. Keys |
|------|------|-------|-----------|
| 1 | i18n default + keys | i18n.ts | ~150 keys |
| 2 | Wire all CLI commands | 18 CLI files | 0 |
| 3 | Formatter title + borders | formatter.ts | 0 |
| 4 | status grouped tables | status.ts, i18n.ts | ~15 keys |
| 5 | list grouped tables | list.ts, i18n.ts | ~3 keys |
| 6 | sync status table | sync/index.ts, i18n.ts | ~7 keys |
| 7 | mem status table | mem/index.ts, i18n.ts | ~8 keys |
| 8 | install/update output | install.ts, update.ts, i18n.ts | ~6 keys |
| 9 | Claude Code Manager | NEW claude-code-manager.ts | 0 |
| 10 | Integrate into install | installer.ts | 0 |
| 11 | Integrate into update | updater.ts | 0 |
| 12 | Final regression fix | various | 0 |

**Total: 12 tasks, ~189 i18n keys, 1 new module, ~25 files modified**
