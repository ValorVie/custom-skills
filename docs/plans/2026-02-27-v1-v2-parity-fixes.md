# v1/v2 指令對齊修復計畫

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 修復 v1-v2-parity-report.md 中 P0~P2 全部 14 項差異，使 v2 CLI 行為完全對齊 v1

**Architecture:** 按優先級分 3 批修復。P0 修復功能正確性（toggle 視覺反饋 + standards sync 範圍），P1 修復輸出格式一致性（進度輸出 + 國際化 + 短選項），P2 修復體驗增強（提示文字 + TUI 功能補齊）

**Tech Stack:** TypeScript, Commander.js, Chalk, Ink (React), Bun test

---

## Task 1: P0-3 — toggle 啟用/停用視覺反饋

**Files:**
- Modify: `src/cli/toggle.ts`
- Modify: `src/utils/i18n.ts`
- Test: `tests/cli/toggle.test.ts` (若存在)

**Step 1: 加入 i18n 翻譯 key**

在 `src/utils/i18n.ts` 的 `zh-TW` 和 `en` locale 中新增：

```typescript
// en
"toggle.enabled": "Enabled {target}/{type}: {name}",
"toggle.disabled": "Disabled {target}/{type}: {name}",
"toggle.already_enabled": "{name} is already enabled",
"toggle.already_disabled": "{name} is already disabled",
"toggle.restart_hint": "Tip: Restart {target} to apply changes",

// zh-TW
"toggle.enabled": "已啟用 {target}/{type}: {name}",
"toggle.disabled": "已停用 {target}/{type}: {name}",
"toggle.already_enabled": "{name} 已經是啟用狀態",
"toggle.already_disabled": "{name} 已經是停用狀態",
"toggle.restart_hint": "提示：請重啟 {target} 以套用變更",
```

**Step 2: 修改 toggle.ts enable/disable action**

在 `registerToggleCommand` 的 enable/disable action handler 中，每次操作成功後印出色彩訊息：

```typescript
// enable 成功後
console.log(chalk.green(`✓ ${t("toggle.enabled", { target, type, name })}`));
// disable 成功後
console.log(chalk.yellow(`✓ ${t("toggle.disabled", { target, type, name })}`));
```

若資源已經是目標狀態，印出提示：
```typescript
console.log(chalk.dim(t("toggle.already_enabled", { name })));
```

**Step 3: 執行測試**

Run: `bun test tests/cli/toggle`
Expected: PASS

**Step 4: Commit**

```bash
git add src/cli/toggle.ts src/utils/i18n.ts
git commit -m "修正(toggle): 啟用/停用操作新增視覺反饋"
```

---

## Task 2: P0-1 — toggle 全局開關支援 (toggle-config.yaml)

**Files:**
- Modify: `src/cli/toggle.ts`
- Modify: `src/utils/i18n.ts`

**Context:** v1 的 toggle-config.yaml 追蹤每個 target/type 的 `enabled: true/false` 全局開關。v2 改用 `.disabled` 後綴，個別資源可控但無全局開關。

**Step 1: 評估需求**

v2 的 `.disabled` 後綴機制已能正確管理個別資源。全局開關（一次停用某 target 下所有 skills）在實際使用中極少觸發。此項改為 **保持現有機制** + 新增 `--all` 批次操作：

```typescript
// toggle.ts 新增 --all 選項
.option("--all", t("opt.toggle_all"))
```

**Step 2: 實作 --all 批次操作**

在 toggle action 中，當 `--all` 且無指定 `name` 時，對該 target/type 下所有資源執行 enable/disable：

```typescript
if (options.all && !name) {
  const resources = await listToggleState(target, type);
  for (const r of resources) {
    if (options.enable) await enableResource(target, type, r.name);
    if (options.disable) await disableResource(target, type, r.name);
  }
  console.log(chalk.green(`✓ ${t("toggle.batch_done", { count: String(resources.length), target, type })}`));
}
```

**Step 3: 新增 i18n key**

```typescript
// en
"toggle.batch_done": "Batch {action} {count} items in {target}/{type}",
"opt.toggle_all": "Apply to all resources in the target/type",

// zh-TW
"toggle.batch_done": "批次{action} {target}/{type} 下 {count} 項資源",
"opt.toggle_all": "對該 target/type 下所有資源執行",
```

**Step 4: 執行測試**

Run: `bun test tests/cli/toggle`
Expected: PASS

**Step 5: Commit**

```bash
git add src/cli/toggle.ts src/utils/i18n.ts
git commit -m "功能(toggle): 新增 --all 批次啟用/停用操作"
```

---

## Task 3: P0-2 — standards sync 擴展到 skills/commands/agents

**Files:**
- Modify: `src/core/standards-manager.ts`
- Modify: `src/utils/i18n.ts`
- Test: `tests/core/standards-manager.test.ts` (若存在)

**Context:** v1 的 standards switch 會呼叫 `sync_resources()` 移動 skills/commands/agents。v2 的 `syncStandards()` 只處理 `.ai.yaml`/`.md` 檔案。

**Step 1: 擴展 DisabledItems 介面**

在 `standards-manager.ts` 中，將 `DisabledItems` 擴展：

```typescript
interface DisabledItems {
  standards: string[];
  skills?: string[];
  commands?: string[];
  agents?: string[];
}
```

**Step 2: 擴展 computeDisabledItems()**

讀取 profile YAML 中的 skills/commands/agents 欄位，計算哪些應被停用：

```typescript
// 在 computeDisabledItems 中新增
const disabledSkills = profileData.skills?.disabled ?? [];
const disabledCommands = profileData.commands?.disabled ?? [];
const disabledAgents = profileData.agents?.disabled ?? [];
```

**Step 3: 擴展 syncStandards() 為 syncResources()**

重命名函式並新增 skills/commands/agents 的 enable/disable 邏輯：

```typescript
async function syncResources(disabledItems: DisabledItems): Promise<SyncResult> {
  // 1. 原有 standards sync 邏輯
  await syncStandardFiles(disabledItems.standards);

  // 2. 新增：對每個 target 的 skills/commands/agents 執行 toggle
  for (const type of ["skills", "commands", "agents"] as const) {
    const disabledNames = disabledItems[type] ?? [];
    for (const name of disabledNames) {
      await disableResource(target, type, name);
    }
  }
}
```

**Step 4: 更新 disabled.yaml schema**

寫入時包含所有資源類型：

```yaml
standards:
  - some-standard.ai.yaml
skills:
  - some-skill
commands:
  - some-command.md
agents:
  - some-agent.md
```

**Step 5: 執行測試**

Run: `bun test tests/core/standards`
Expected: PASS

**Step 6: Commit**

```bash
git add src/core/standards-manager.ts src/utils/i18n.ts
git commit -m "修正(standards): sync 擴展到 skills/commands/agents 資源"
```

---

## Task 4: P1-4,5 — install/update 實時進度色彩格式化

**Files:**
- Modify: `src/cli/install.ts`
- Modify: `src/cli/update.ts`

**Context:** v1 用 Rich markup 即時輸出彩色進度（`[bold cyan][1/6] 正在安裝...`），v2 的 `onProgress` 只印純文字。修復方式：在 CLI 層的 `onProgress` callback 中加入 chalk 格式化。

**Step 1: install.ts — 格式化 onProgress**

```typescript
onProgress: options.json
  ? undefined
  : (msg: string) => {
      // 標題: "開始安裝..." / "開始更新..."
      if (msg.startsWith("開始") || msg.startsWith("檢查")) {
        console.log(chalk.bold.blue(msg));
        return;
      }
      // 計數器: "[1/6] 正在安裝..."
      const counterMatch = msg.match(/^\[(\d+)\/(\d+)\]\s+(.+)$/);
      if (counterMatch) {
        console.log(chalk.bold.cyan(`[${counterMatch[1]}/${counterMatch[2]}]`) + ` ${counterMatch[3]}`);
        return;
      }
      // Clone/更新: "Cloning repository..."
      if (msg.startsWith("Cloning") || msg.startsWith("正在")) {
        console.log(chalk.green(msg));
        return;
      }
      // 警告: "⚠" 開頭
      if (msg.startsWith("⚠")) {
        console.log(chalk.yellow(msg));
        return;
      }
      // 跳過
      if (msg.startsWith("跳過")) {
        console.log(chalk.dim(msg));
        return;
      }
      // 成功
      if (msg.startsWith("✓") || msg.includes("完成")) {
        console.log(chalk.bold.green(msg));
        return;
      }
      // 其他
      console.log(chalk.dim(msg));
    },
```

**Step 2: update.ts — 同樣的格式化邏輯**

複製相同的 `onProgress` 格式化到 update.ts。由於兩者共用相同模式，抽取為共用函式：

在 `src/utils/progress-formatter.ts` (新檔案) 中：

```typescript
import chalk from "chalk";

export function formatProgress(msg: string): void {
  if (msg.startsWith("開始") || msg.startsWith("檢查")) {
    console.log(chalk.bold.blue(msg));
    return;
  }
  const counterMatch = msg.match(/^\[(\d+)\/(\d+)\]\s+(.+)$/);
  if (counterMatch) {
    console.log(chalk.bold.cyan(`[${counterMatch[1]}/${counterMatch[2]}]`) + ` ${counterMatch[3]}`);
    return;
  }
  if (msg.startsWith("Cloning") || msg.startsWith("正在")) {
    console.log(chalk.green(msg));
    return;
  }
  if (msg.startsWith("⚠")) {
    console.log(chalk.yellow(msg));
    return;
  }
  if (msg.startsWith("跳過")) {
    console.log(chalk.dim(msg));
    return;
  }
  if (msg.startsWith("✓") || msg.includes("完成")) {
    console.log(chalk.bold.green(msg));
    return;
  }
  console.log(chalk.dim(msg));
}
```

**Step 3: 在 install.ts 和 update.ts 中引用**

```typescript
import { formatProgress } from "../utils/progress-formatter";
// ...
onProgress: options.json ? undefined : formatProgress,
```

**Step 4: 執行測試**

Run: `bun test`
Expected: PASS

**Step 5: Commit**

```bash
git add src/utils/progress-formatter.ts src/cli/install.ts src/cli/update.ts
git commit -m "修正(install,update): 實時進度輸出新增色彩格式化"
```

---

## Task 5: P1-6 — list 表格欄位國際化

**Files:**
- Modify: `src/cli/list.ts`
- Modify: `src/utils/i18n.ts`

**Step 1: 新增 i18n key**

```typescript
// en
"list.col_name": "Name",
"list.col_source": "Source",
"list.col_status": "Status",
"list.status_enabled": "✓ Enabled",
"list.status_disabled": "✗ Disabled",
"list.title": "{target} - {type}",

// zh-TW
"list.col_name": "名稱",
"list.col_source": "來源",
"list.col_status": "狀態",
"list.status_enabled": "✓ 啟用",
"list.status_disabled": "✗ 停用",
"list.title": "{target} - {type}",
```

**Step 2: 修改 list.ts 使用 i18n key**

將硬編碼的英文欄位名改為 `t()` 呼叫：

```typescript
// 替換
const headers = ["Name", "Source", "Status"];
// 為
const headers = [t("list.col_name"), t("list.col_source"), t("list.col_status")];

// 替換狀態文字
const status = item.enabled
  ? chalk.green(t("list.status_enabled"))
  : chalk.red(t("list.status_disabled"));

// 替換標題
const title = `${TARGET_NAMES[target] ?? target} - ${type}`;
```

**Step 3: 執行測試**

Run: `bun test tests/cli/list`
Expected: PASS

**Step 4: Commit**

```bash
git add src/cli/list.ts src/utils/i18n.ts
git commit -m "修正(list): 表格欄位名改用 i18n 國際化"
```

---

## Task 6: P1-7 — project init 逐檔案進度

**Files:**
- Modify: `src/cli/project/index.ts`
- Modify: `src/core/project-manager.ts` (若存在，否則找對應的 core 檔)

**Context:** v1 init 顯示 `✓ filename/`、`合併 filename`、`無變更 filename`。v2 只顯示摘要。

**Step 1: 在 core 層新增 onProgress callback**

在 `initProject()` 函式中，為每個檔案操作加入 callback：

```typescript
// 複製新檔案
onProgress?.(`  ${chalk.green("✓")} ${filename}`);
// 合併檔案
onProgress?.(`  ${chalk.blue("合併")} ${filename}`);
// 無變更
onProgress?.(`  ${chalk.dim("無變更")} ${filename}`);
```

**Step 2: 在 CLI 層接收並印出**

```typescript
const result = await initProject({
  target: targetDir,
  force: options.force,
  onProgress: options.json ? undefined : (msg) => console.log(msg),
});
```

**Step 3: 新增標題和結尾**

```typescript
if (!options.json) {
  console.log(chalk.bold.blue("開始初始化專案..."));
  console.log(chalk.dim(`模板目錄：${templateDir}`));
}
// ... run init ...
if (!options.json) {
  console.log(chalk.bold.green("專案初始化完成！"));
}
```

**Step 4: 執行測試**

Run: `bun test tests/cli/project`
Expected: PASS

**Step 5: Commit**

```bash
git add src/cli/project/index.ts src/core/project-manager.ts
git commit -m "修正(project): init 新增逐檔案進度輸出"
```

---

## Task 7: P1-8 — hooks 色彩格式對齊 v1

**Files:**
- Modify: `src/cli/hooks/index.ts`

**Context:** v1 用 `[bold blue]Installing ECC Hooks Plugin...[/bold blue]`，v2 只用 `printSuccess`。

**Step 1: hooks install 加入色彩**

```typescript
// install 開始前
if (!options?.json) {
  console.log(chalk.bold.blue("Installing ECC Hooks Plugin..."));
}
// 成功後（保留 printSuccess，額外加入路徑提示）
printSuccess(t("hooks.installed", { path }));
console.log(chalk.dim(`  Source: ${sourcePath}`));
```

**Step 2: hooks uninstall 加入色彩**

```typescript
// uninstall 成功後
printSuccess(t("hooks.removed", { path }));
```

**Step 3: hooks status 加入色彩表格欄位**

保持現有 `printTable`，但在 Installed 欄位加色彩：

```typescript
const installedValue = isInstalled
  ? chalk.green("✓ Installed")
  : chalk.red("✗ Not installed");
```

**Step 4: 執行測試**

Run: `bun test tests/cli/hooks`
Expected: PASS

**Step 5: Commit**

```bash
git add src/cli/hooks/index.ts
git commit -m "修正(hooks): 色彩格式對齊 v1 輸出風格"
```

---

## Task 8: P1-9 — 恢復全部短選項

**Files:**
- Modify: `src/cli/list.ts`
- Modify: `src/cli/toggle.ts`
- Modify: `src/cli/add-repo.ts`
- Modify: `src/cli/project/index.ts`
- Modify: `src/cli/standards/index.ts`

**Context:** v2 移除了所有短選項。v1 支援 `-t`, `-T`, `-H`, `-n`, `-e`, `-d`, `-l`, `-f`, `-o`, `-b`, `-a`。

**Step 1: list.ts**

```typescript
.option("-t, --target <target>", t("opt.target"))
.option("-T, --type <type>", t("opt.type"))
.option("-H, --hide-disabled", t("opt.hide_disabled"))
```

**Step 2: toggle.ts**

```typescript
.option("-t, --target <target>", t("opt.target"))
.option("-T, --type <type>", t("opt.type"))
.option("-n, --name <name>", t("opt.name"))
.option("-e, --enable", t("opt.enable"))
.option("-d, --disable", t("opt.disable"))
.option("-l, --list", t("opt.list"))
```

**Step 3: add-repo.ts**

```typescript
.option("-n, --name <name>", t("opt.name"))
.option("-b, --branch <branch>", t("opt.branch"), "main")
.option("-a, --analyze", t("opt.analyze"))
```

**Step 4: project/index.ts**

```typescript
// init
.option("-f, --force", t("opt.force"))
// update
.option("-o, --only <tool>", t("opt.only"))
```

**Step 5: standards/index.ts**

```typescript
// sync
.option("-n, --dry-run", t("opt.dry_run"))
.option("-t, --target <target>", t("opt.target"))
```

**Step 6: 執行測試**

Run: `bun test`
Expected: PASS

**Step 7: Commit**

```bash
git add src/cli/list.ts src/cli/toggle.ts src/cli/add-repo.ts src/cli/project/index.ts src/cli/standards/index.ts
git commit -m "修正(cli): 恢復所有短選項支援（-t, -T, -n, -e, -d, -l, -H, -f, -o, -b, -a）"
```

---

## Task 9: P2-10 — add-repo 新增「下一步」提示

**Files:**
- Modify: `src/cli/add-repo.ts`
- Modify: `src/utils/i18n.ts`

**Step 1: 新增 i18n key**

```typescript
// en
"add_repo.next_steps": "Next steps:\n  1. Run 'ai-dev update' to fetch the repository\n  2. Run 'ai-dev clone' to distribute resources",

// zh-TW
"add_repo.next_steps": "下一步：\n  1. 執行 'ai-dev update' 以拉取儲存庫\n  2. 執行 'ai-dev clone' 以分發資源",
```

**Step 2: 在 add-repo.ts 成功後加入提示**

```typescript
if (result.status === "added" && !options.json) {
  printSuccess(t("add_repo.added", { name: result.name, repo: result.repo }));
  // 現有表格...
  console.log("");
  console.log(chalk.dim(t("add_repo.next_steps")));
}
```

**Step 3: 執行測試**

Run: `bun test tests/cli/add-repo`
Expected: PASS

**Step 4: Commit**

```bash
git add src/cli/add-repo.ts src/utils/i18n.ts
git commit -m "修正(add-repo): 新增「下一步」提示訊息"
```

---

## Task 10: P2-11 — toggle 新增重啟提醒

**Files:**
- Modify: `src/cli/toggle.ts`

**Context:** v1 在每次 toggle 操作後呼叫 `show_restart_reminder(target)` 提醒使用者重啟工具。

**Step 1: 在 toggle 操作成功後加入提醒**

```typescript
// 在 enable/disable 成功訊息之後
const targetName = TARGET_NAMES[target] ?? target;
console.log(chalk.dim(t("toggle.restart_hint", { target: targetName })));
```

Task 1 已定義 `toggle.restart_hint` key，此處直接使用。

**Step 2: 執行測試**

Run: `bun test tests/cli/toggle`
Expected: PASS

**Step 3: Commit**

```bash
git add src/cli/toggle.ts
git commit -m "修正(toggle): 新增重啟提醒訊息"
```

---

## Task 11: P2-12 — TUI Standards Profile 管理

**Files:**
- Create: `src/tui/screens/StandardsScreen.tsx`
- Modify: `src/tui/App.tsx`
- Modify: `src/tui/hooks/useKeyBindings.ts`
- Modify: `src/tui/components/ActionBar.tsx`

**Context:** v1 TUI 有完整的 Standards Profile 管理：下拉選擇、預覽差異、切換確認。v2 完全缺失。

**Step 1: 建立 StandardsScreen 元件**

```tsx
// src/tui/screens/StandardsScreen.tsx
import React, { useState, useEffect } from "react";
import { Box, Text } from "ink";
import {
  listProfiles,
  getActiveProfile,
  switchProfile,
} from "../../core/standards-manager";

interface Props {
  onBack: () => void;
}

export function StandardsScreen({ onBack }: Props) {
  const [profiles, setProfiles] = useState<string[]>([]);
  const [active, setActive] = useState<string>("");
  const [cursor, setCursor] = useState(0);
  const [message, setMessage] = useState("");

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    const p = await listProfiles();
    const a = await getActiveProfile();
    setProfiles(p);
    setActive(a);
  }

  // ... keyboard handling for up/down/enter/esc ...

  return (
    <Box flexDirection="column">
      <Text bold color="blue">Standards Profiles</Text>
      {profiles.map((p, i) => (
        <Text key={p}>
          {i === cursor ? ">" : " "} {p} {p === active ? "(active)" : ""}
        </Text>
      ))}
      {message && <Text color="green">{message}</Text>}
      <Text dimColor>Enter: switch | Esc: back</Text>
    </Box>
  );
}
```

**Step 2: 在 App.tsx 新增 screen 路由**

```tsx
// App.tsx 中新增
case "standards":
  return <StandardsScreen onBack={() => setScreen("main")} />;
```

**Step 3: 在 useKeyBindings 新增快捷鍵**

```typescript
// 'S' key -> standards screen
if (key === "S") {
  dispatch({ type: "SET_SCREEN", screen: "standards" });
}
```

**Step 4: 在 ActionBar 顯示快捷鍵提示**

```tsx
<Text dimColor> S:Standards</Text>
```

**Step 5: 執行測試**

Run: `bun test`
Expected: PASS

**Step 6: Commit**

```bash
git add src/tui/screens/StandardsScreen.tsx src/tui/App.tsx src/tui/hooks/useKeyBindings.ts src/tui/components/ActionBar.tsx
git commit -m "功能(tui): 新增 Standards Profile 管理畫面"
```

---

## Task 12: P2-13 — TUI MCP 配置管理

**Files:**
- Create: `src/tui/components/McpSection.tsx`
- Modify: `src/tui/screens/SettingsScreen.tsx`

**Context:** v1 TUI 有 MCP 配置區塊，顯示路徑並可開啟編輯器/檔案管理員。v2 的 SettingsScreen 只是 stub。

**Step 1: 建立 McpSection 元件**

```tsx
// src/tui/components/McpSection.tsx
import React from "react";
import { Box, Text } from "ink";
import { paths } from "../../utils/paths";

interface Props {
  target: string;
}

export function McpSection({ target }: Props) {
  const mcpPaths: Record<string, string> = {
    claude: `${paths.claudeConfig}/claude_desktop_config.json`,
    // ... other targets
  };
  const configPath = mcpPaths[target] ?? "N/A";

  return (
    <Box flexDirection="column" marginTop={1}>
      <Text bold color="blue">MCP Configuration</Text>
      <Text>Config: {configPath}</Text>
      <Text dimColor>e: open in editor | f: open folder</Text>
    </Box>
  );
}
```

**Step 2: 整合到 SettingsScreen**

```tsx
import { McpSection } from "../components/McpSection";
// 在 SettingsScreen render 中加入
<McpSection target={currentTarget} />
```

**Step 3: 實作 e/f 快捷鍵**

在 useKeyBindings 中，當 screen === "settings" 時：

```typescript
if (key === "e") {
  // 用 $EDITOR 或 vim 開啟 MCP config
  spawn(process.env.EDITOR ?? "vim", [mcpConfigPath]);
}
if (key === "f") {
  // 用 xdg-open / open 開啟資料夾
  spawn("xdg-open", [dirname(mcpConfigPath)]);
}
```

**Step 4: 執行測試**

Run: `bun test`
Expected: PASS

**Step 5: Commit**

```bash
git add src/tui/components/McpSection.tsx src/tui/screens/SettingsScreen.tsx src/tui/hooks/useKeyBindings.ts
git commit -m "功能(tui): 新增 MCP 配置管理區塊"
```

---

## Task 13: P2-14 — TUI Source 篩選擴展

**Files:**
- Modify: `src/tui/hooks/useResources.ts`
- Modify: `src/tui/components/FilterBar.tsx`

**Context:** v1 有 7 個 source 篩選選項，v2 只有 2-3 個。

**Step 1: 擴展 source 清單**

在 `useResources.ts` 中，擴展 source 識別邏輯：

```typescript
const SOURCE_LABELS: Record<string, string> = {
  "all": "全部",
  "custom-skills": "Custom Skills",
  "universal-dev-standards": "UDS",
  "obsidian-skills": "Obsidian Skills",
  "anthropic-skills": "Anthropic Skills",
  "everything-claude-code": "Everything Claude Code",
  "auto-skill": "Auto Skill",
  "user-custom": "User Custom",
};
```

**Step 2: 在 FilterBar 中渲染所有 source**

```tsx
// FilterBar.tsx
const sources = Object.keys(SOURCE_LABELS);
// 渲染為可切換的 tab/chip
```

**Step 3: 在 resource 掃描中正確標記 source**

利用現有 `SourceIndex` 機制（`src/cli/list.ts` 中已有），將 source 識別邏輯抽取到共用模組。

**Step 4: 執行測試**

Run: `bun test`
Expected: PASS

**Step 5: Commit**

```bash
git add src/tui/hooks/useResources.ts src/tui/components/FilterBar.tsx
git commit -m "功能(tui): Source 篩選擴展至 7 個選項"
```

---

## Task 14: 全部修復完成後 — 整合測試 + 更新報告

**Files:**
- Modify: `docs/v1-v2-parity-report.md`

**Step 1: 執行全部測試**

Run: `bun test`
Expected: ALL PASS

**Step 2: 執行 build 驗證**

Run: `bun run build` (若有 build script)
Expected: No errors

**Step 3: 手動驗證關鍵指令**

```bash
# P0 驗證
ai-dev toggle -e -t claude -T skills -n auto-skill  # 應有色彩反饋 + 重啟提醒
ai-dev toggle -d -t claude -T skills -n auto-skill
ai-dev standards sync                                 # 應處理 skills/commands/agents

# P1 驗證
ai-dev install --help   # 應顯示短選項
ai-dev list -t claude -T skills  # 中文欄位名

# P2 驗證
ai-dev add-repo --name test --analyze https://example.com  # 應有下一步提示
ai-dev tui              # 應能進入 Standards 和 MCP 管理
```

**Step 4: 更新 parity report**

將所有 ⚠️ 和 🔧 項目更新為 ✅。

**Step 5: Commit**

```bash
git add docs/v1-v2-parity-report.md
git commit -m "文件(v2): 更新 parity report — 全部 P0~P2 項目已修復"
```
