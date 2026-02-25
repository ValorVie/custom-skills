# ai-dev CLI 框架技術架構

> **版本**: 2.0.0
> **更新日期**: 2026-02-25

---

## 概述

`ai-dev` 是 custom-skills 專案的核心 CLI 工具，負責管理多 AI 工具的 Skills、Commands、Agents、Workflows 的安裝、更新與分發。v2 版從 Python 遷移至 Bun/TypeScript，採用四層分離架構。

---

## 技術堆疊

| 元件 | 技術 | 用途 |
|------|------|------|
| Runtime | [Bun](https://bun.sh/) 1.3+ | JavaScript/TypeScript 執行環境 |
| CLI 框架 | [Commander.js](https://github.com/tj/commander.js) | 指令定義與參數解析 |
| TUI 介面 | [Ink](https://github.com/vadimdemedes/ink) + React | 互動式終端 UI |
| 終端輸出 | [Chalk](https://github.com/chalk/chalk) + [ora](https://github.com/sindresorhus/ora) | 彩色輸出與 spinner |
| 配置格式 | [yaml](https://github.com/eemeli/yaml) | YAML 讀寫 |
| SQLite | [better-sqlite3](https://github.com/WiseLibs/better-sqlite3) | mem-sync 本地資料庫 |
| Lint/Format | [Biome](https://biomejs.dev/) | 程式碼風格與靜態分析 |
| 型別檢查 | TypeScript 5.9+ (`tsc --noEmit`) | 編譯期型別安全 |
| 測試 | `bun test` | 內建測試框架，相容 Jest API |
| 追蹤機制 | SHA-256 Manifest | 檔案分發追蹤與衝突檢測 |

---

## 架構原則

### 四層分離

```
src/
├── cli/       ← 指令定義層：Commander.js 註冊、參數解析、輸出格式化
├── core/      ← 業務邏輯層：純函式，不依賴任何 UI 框架
├── utils/     ← 工具函式層：路徑、系統、Git、YAML、Manifest
└── tui/       ← TUI 層：Ink/React 元件，視圖切換路由
```

**核心規則**：

- `core/` 為純函式，**禁止** import `commander`、`chalk`、`ink`、`ora`、`inquirer`
- `core/` 回傳結構化資料（interface/type），由 `cli/` 負責呈現
- `utils/` 為無狀態工具函式，可被任何層呼叫
- `tui/` 獨立於 `cli/`，透過 `cli/tui.ts` 橋接

### 依賴方向

```
cli/ ──→ core/ ──→ utils/
 │                   ↑
tui/ ────────────────┘
```

禁止反向依賴：`utils/` 不可 import `core/`，`core/` 不可 import `cli/`。

---

## 專案結構

```
src/
├── cli.ts                      # 入口點 (#!/usr/bin/env bun)
├── cli/
│   ├── index.ts                # Commander.js 主程式，註冊所有指令
│   ├── install.ts              # install 指令
│   ├── update.ts               # update 指令
│   ├── clone.ts                # clone 指令（分發 Skills）
│   ├── status.ts               # status 指令
│   ├── list.ts                 # list 指令
│   ├── toggle.ts               # toggle 指令
│   ├── add-repo.ts             # add-repo 指令
│   ├── add-custom-repo.ts      # add-custom-repo 指令
│   ├── update-custom-repo.ts   # update-custom-repo 指令
│   ├── test.ts                 # test 指令
│   ├── coverage.ts             # coverage 指令
│   ├── derive-tests.ts         # derive-tests 指令
│   ├── tui.ts                  # tui 指令（橋接到 Ink）
│   ├── project/index.ts        # project 子命令組 (init, update)
│   ├── standards/index.ts      # standards 子命令組 (status, list, switch, show, overlaps)
│   ├── hooks/index.ts          # hooks 子命令組 (install, uninstall, status)
│   ├── sync/index.ts           # sync 子命令組 (init, push, pull, status, add, remove)
│   └── mem/index.ts            # mem 子命令組 (register, push, pull, status, reindex, cleanup)
├── core/
│   ├── status-checker.ts       # 環境狀態檢查
│   ├── installer.ts            # 安裝邏輯
│   ├── updater.ts              # 更新邏輯
│   ├── sync-engine.ts          # 跨裝置同步引擎
│   ├── mem-sync.ts             # claude-mem HTTP sync 客戶端
│   ├── standards-manager.ts    # 標準 profile 管理
│   └── project-manager.ts      # 專案模板管理
├── utils/
│   ├── paths.ts                # 所有配置路徑常數
│   ├── system.ts               # OS 偵測、指令執行
│   ├── config.ts               # YAML 讀寫
│   ├── git.ts                  # Git 操作
│   ├── manifest.ts             # Hash 計算 + ManifestTracker
│   ├── shared.ts               # 常數、型別、複製函式
│   └── custom-repos.ts         # 自訂 repo 管理
└── tui/
    ├── index.tsx               # Ink render 入口
    ├── App.tsx                 # 根元件，useState<Screen> 視圖路由
    ├── screens/
    │   ├── MainScreen.tsx      # 主畫面（Header + TabBar + FilterBar + ResourceList + ActionBar）
    │   ├── PreviewScreen.tsx   # 資源預覽
    │   ├── ConfirmScreen.tsx   # 確認操作
    │   └── SettingsScreen.tsx  # 設定畫面
    ├── components/
    │   ├── Header.tsx          # 標題列
    │   ├── TabBar.tsx          # 目標切換列
    │   ├── FilterBar.tsx       # 篩選列
    │   ├── ResourceList.tsx    # 資源列表
    │   ├── ResourceItem.tsx    # 單一資源項目
    │   └── ActionBar.tsx       # 快捷鍵提示列
    └── hooks/
        ├── useResources.ts     # 資源狀態管理
        └── useKeyBindings.ts   # 鍵盤快捷鍵綁定
```

### 設定檔

| 檔案 | 用途 |
|------|------|
| `package.json` | 套件定義、bin、scripts、dependencies |
| `tsconfig.json` | TypeScript 設定（ES2022, ESNext, react-jsx, bun-types） |
| `biome.json` | Biome lint/format 設定（2-space indent, double quotes, semicolons） |
| `bunfig.toml` | Bun 設定（coverage 啟用） |

### 測試結構

```
tests/
├── cli/
│   └── smoke.test.ts           # CLI 冒煙測試 (--version, --help, status)
├── core/
│   ├── status-checker.test.ts
│   ├── installer.test.ts
│   ├── updater.test.ts
│   ├── sync-engine.test.ts
│   ├── mem-sync.test.ts
│   ├── project-manager.test.ts
│   └── standards-manager.test.ts
└── utils/
    ├── paths.test.ts
    ├── system.test.ts
    ├── config.test.ts
    ├── git.test.ts
    ├── manifest.test.ts
    ├── manifest-tracker.test.ts
    ├── shared.test.ts
    └── copy-skills.test.ts
```

---

## 開發指南

### 新增一個頂層指令

以新增 `ai-dev foo` 為例：

**1. 建立 core 模組（如有業務邏輯）**

```typescript
// src/core/foo.ts
export interface FooResult {
  success: boolean;
  message: string;
}

export async function runFoo(options: { verbose: boolean }): Promise<FooResult> {
  // 純業務邏輯，不引入 CLI/UI 依賴
  return { success: true, message: "done" };
}
```

**2. 建立 CLI 指令**

```typescript
// src/cli/foo.ts
import type { Command } from "commander";
import { runFoo } from "../core/foo";

export function registerFooCommand(program: Command): void {
  program
    .command("foo")
    .description("Do something useful")
    .option("--verbose, -v", "Verbose output")
    .action(async (options: { verbose?: boolean }) => {
      const result = await runFoo({ verbose: options.verbose ?? false });

      if (options.verbose) {
        console.log(JSON.stringify(result, null, 2));
      } else {
        console.log(result.message);
      }
    });
}
```

**3. 註冊到主程式**

```typescript
// src/cli/index.ts
import { registerFooCommand } from "./foo";

// 在 createProgram() 中加入：
registerFooCommand(program);
```

**4. 撰寫測試**

```typescript
// tests/core/foo.test.ts
import { describe, expect, it } from "bun:test";
import { runFoo } from "../../src/core/foo";

describe("foo", () => {
  it("returns success", async () => {
    const result = await runFoo({ verbose: false });
    expect(result.success).toBe(true);
  });
});
```

### 新增一個子命令組

以新增 `ai-dev bar init` 和 `ai-dev bar reset` 為例：

```typescript
// src/cli/bar/index.ts
import type { Command } from "commander";

export function registerBarCommands(program: Command): void {
  const bar = program.command("bar").description("Bar operations");

  bar
    .command("init")
    .description("Initialize bar")
    .action(async () => {
      // ...
    });

  bar
    .command("reset")
    .description("Reset bar")
    .action(async () => {
      // ...
    });
}
```

### 新增一個 TUI 畫面

**1. 建立 Screen 元件**

```tsx
// src/tui/screens/FooScreen.tsx
import { Box, Text } from "ink";

interface Props {
  data: string;
}

export function FooScreen({ data }: Props) {
  return (
    <Box flexDirection="column">
      <Text bold>Foo Screen</Text>
      <Text>{data}</Text>
    </Box>
  );
}
```

**2. 在 App.tsx 加入路由**

```tsx
// src/tui/App.tsx
// 1. 擴充 Screen type
export type Screen = "main" | "preview" | "confirm" | "settings" | "foo";

// 2. 加入條件渲染
if (screen === "foo") {
  return <FooScreen data="hello" />;
}
```

**3. 綁定快捷鍵（可選）**

在 `useKeyBindings.ts` 的 callbacks 加入 `onFoo`，在 `App.tsx` 傳入 `onFoo: () => setScreen("foo")`。

### 新增上游來源

1. **`src/utils/paths.ts`** — 新增路徑常數：
   ```typescript
   newRepo: join(config, "new-repo"),
   ```

2. **`src/utils/shared.ts`** — 新增到 `REPOS` 陣列：
   ```typescript
   {
     name: "new-repo",
     url: "https://github.com/org/new-repo.git",
     dir: paths.newRepo,
   },
   ```

3. **`upstream/sources.yaml`** — 註冊上游來源

---

## 指令架構與職責分工

### 指令總覽

```
ai-dev
├── install          # 首次安裝（冪等）
├── update           # 日常更新
├── clone            # 分發到各工具目錄
├── status           # 環境狀態檢查
├── list             # 列出已安裝資源
├── toggle           # 啟用/停用特定資源
├── add-repo         # 新增上游 repo
├── add-custom-repo  # 新增自訂 repo
├── update-custom-repo # 更新自訂 repo
├── test             # 執行測試
├── coverage         # 覆蓋率分析
├── derive-tests     # 測試推導
├── tui              # 互動式 TUI 介面
├── project          # 專案子命令組 (init, update)
├── standards        # Standards 子命令組 (status, list, switch, show, overlaps)
├── hooks            # Hooks 子命令組 (install, uninstall, status)
├── sync             # Sync 子命令組 (init, push, pull, status, add, remove)
└── mem              # Mem 子命令組 (register, push, pull, status, reindex, cleanup)
```

### install vs update 設計決策

| 面向 | `install` | `update` |
|------|-----------|----------|
| **定位** | 首次環境建置 | 日常更新 |
| **冪等性** | 完全冪等（已存在即跳過） | 冪等（只更新有差異的） |
| **前置檢查** | Node.js、Git、Bun、gh | 無 |
| **目錄建立** | 建立所有必要目錄 | 不建立目錄 |
| **缺失 repo** | 自動 clone | 顯示警告，提示執行 install |
| **已有 repo** | 跳過 | fetch + reset --hard |
| **NPM/Bun 套件** | install | install（同效果） |
| **Skills 分發** | 自動執行 `copySkills()` | 不執行，提示手動跑 `clone` |
| **Custom repos** | clone 缺失的 | 缺失時顯示警告 |

**設計原則**：
- `install` 是完整的環境建置，可安全重複執行
- `update` 只負責「拉取最新」，不改變環境結構
- 如果 `update` 發現缺失 repo，應引導使用者回到 `install` 補齊

---

## 資源管理系統

### 資源類型

| 類型 | 說明 | 支援的目標工具 |
|------|------|---------------|
| Skills | 行為規範與知識 | claude, antigravity, opencode, codex, gemini |
| Commands | 可呼叫的指令 | claude, opencode, gemini |
| Agents | 自主代理定義 | claude, opencode, gemini |
| Workflows | 工作流程 | claude, antigravity |
| Plugins | 擴充功能 | opencode |

### 目標工具路徑對應

定義於 `src/utils/shared.ts` 的 `COPY_TARGETS`：

| 目標 | Skills | Commands | Agents | 其他 |
|------|--------|----------|--------|------|
| claude | `~/.claude/skills/` | `~/.claude/commands/` | `~/.claude/agents/` | workflows |
| antigravity | `~/.gemini/antigravity/global_skills/` | — | — | global_workflows |
| opencode | `~/.config/opencode/skills/` | `~/.config/opencode/commands/` | `~/.config/opencode/agents/` | plugins |
| codex | `~/.codex/skills/` | — | — | — |
| gemini | `~/.gemini/skills/` | `~/.gemini/commands/` | `~/.gemini/agents/` | — |

### 三階段複製架構

```
Stage 1: Clone     GitHub repos → ~/.config/<repo>/
Stage 2: Integrate ~/.config/<repos> → custom-skills/skills/  (僅開發目錄)
Stage 3: Distribute custom-skills/ → ~/.claude/, ~/.gemini/, etc.
```

詳見 [copy-architecture.md](copy-architecture.md)。

---

## TUI 架構

### 視圖切換模式

Ink 不支援 Modal overlay（與 Textual 不同），改用 `useState<Screen>` 切換整個畫面：

```tsx
type Screen = "main" | "preview" | "confirm" | "settings";

const [screen, setScreen] = useState<Screen>("main");

// 條件渲染
if (screen === "preview") return <PreviewScreen ... />;
if (screen === "confirm") return <ConfirmScreen ... />;
if (screen === "settings") return <SettingsScreen ... />;
return <MainScreen ... />;
```

### 鍵盤快捷鍵

定義於 `src/tui/hooks/useKeyBindings.ts`，使用 Ink 的 `useInput` hook：

| 按鍵 | 功能 | Callback |
|------|------|----------|
| `q` | 退出 | `onQuit` |
| `Space` | 切換選中項目 | `onToggleSelection` |
| `a` | 全選/取消全選 | `onToggleAll` |
| `n` | 新增 | `onAdd` |
| `s` | 儲存 | `onSave` |
| `p` | 預覽 | `onPreview` |
| `e` | 開啟編輯器 | `onOpenEditor` |
| `f` | 開啟檔案管理器 | `onOpenFileManager` |
| `c` | 設定 | `onSettings` |
| `t` | 切換目標 | `onSwitchTarget` |
| `↑/↓` | 上下移動 | `onPrevious/onNext` |
| `ESC/Backspace` | 返回 | `onBack` |

---

## Manifest 追蹤機制

定義於 `src/utils/manifest.ts`：

| 函式 | 用途 |
|------|------|
| `computeFileHash(path)` | 計算檔案 SHA-256 hash，回傳 `sha256:<hex>` |
| `computeDirHash(path)` | 計算目錄 hash（排序所有檔案 hash 後再 hash） |
| `ManifestTracker` | 維護 `.manifest.yaml`，追蹤分發狀態 |
| `detectConflicts()` | 比對 hash，偵測使用者手動修改 |
| `findOrphans()` | 找出已從來源刪除但仍存在於目標的資源 |
| `cleanupOrphans()` | 移除孤兒資源 |
| `backupFile()` | 備份衝突檔案 |

---

## 測試規範

### 執行指令

```bash
bun test                    # 執行全部測試
bun test tests/core/        # 執行特定目錄
bun test --watch            # 監聽模式
bun test --coverage         # 含覆蓋率
```

### 測試慣例

- 測試檔案放在 `tests/` 下，目錄結構鏡像 `src/`
- 命名：`<module>.test.ts`（如 `paths.test.ts`）
- 使用 `describe` + `it` 組織，`expect` 斷言
- `core/` 模組可直接單元測試（純函式，無 UI 依賴）
- `cli/` 層用冒煙測試（`tests/cli/smoke.test.ts`）驗證指令註冊
- Mock 外部呼叫（如 `runCommand`）使用 `bun:test` 的 `mock` API

### 測試範例

```typescript
import { afterEach, beforeEach, describe, expect, it, mock } from "bun:test";
import { mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

describe("myModule", () => {
  let tempDir: string;

  beforeEach(async () => {
    tempDir = await mkdtemp(join(tmpdir(), "test-"));
  });

  afterEach(async () => {
    await rm(tempDir, { recursive: true, force: true });
  });

  it("does something", async () => {
    await writeFile(join(tempDir, "test.txt"), "hello");
    const result = await myFunction(tempDir);
    expect(result).toBe("hello");
  });
});
```

---

## 程式碼風格

由 Biome 統一管理，設定檔為 `biome.json`：

| 項目 | 設定 |
|------|------|
| 縮排 | 2 spaces |
| 引號 | 雙引號 (`"`) |
| 分號 | 必須 (`;`) |
| Lint | recommended rules |
| 涵蓋範圍 | `src/**`、`tests/**`、設定檔 |

```bash
bun run lint          # 檢查
bun run format        # 自動修正格式
```

---

## 建置與發佈

### 建置

```bash
bun run build
# 輸出: dist/cli.js (single bundle, ~2.2 MB)
```

建置指令：`bun build ./src/cli.ts --outfile ./dist/cli.js --target bun`

### 安裝方式

```bash
# 從 Git（推薦，免發佈）
bun add -g github:ValorVie/custom-skills
bun add -g github:ValorVie/custom-skills#v2.0.0  # 指定版本

# 從 npm registry
bun add -g @valorvie/ai-dev

# 本地開發（symlink，改了立刻生效）
bun link
```

### 發佈到 npm

套件以 `@valorvie/ai-dev` scoped name 發佈，`publishConfig.access` 設為 `public`。

**首次發佈前置：**

```bash
# 登入 npm（只需一次）
npm login

# 確認 scope 可用
npm whoami
npm access list packages
```

**發佈流程：**

```bash
# 1. 確保所有檢查通過
bun test && bun run lint && bunx tsc --noEmit

# 2. 建置
bun run build

# 3. 更新版本號（遵循 semver）
npm version patch    # 修正 (2.0.0 → 2.0.1)
npm version minor    # 功能 (2.0.0 → 2.1.0)
npm version major    # 重大 (2.0.0 → 3.0.0)

# 4. 發佈
npm publish

# 5. 推送 tag
git push && git push --tags
```

**package.json 關鍵設定：**

```json
{
  "name": "@valorvie/ai-dev",
  "version": "2.0.0",
  "bin": { "ai-dev": "./src/cli.ts" },
  "files": ["src/", "dist/", "skills/", "commands/", "agents/"],
  "publishConfig": { "access": "public" }
}
```

| 欄位 | 用途 |
|------|------|
| `bin` | 全域安裝後的可執行指令名稱與入口 |
| `files` | 發佈到 npm 時包含的檔案（排除 tests/、docs/ 等） |
| `publishConfig.access` | scoped package 預設為 restricted，需設為 `public` |

**注意**：`bin` 指向 `./src/cli.ts`（原始碼），Bun runtime 直接執行 TypeScript，不需要先建置。若使用者環境為 Node.js，則需改為指向 `./dist/cli.js`（建置產物）。

### 開發流程

```bash
# 日常開發
bun run src/cli.ts --help          # 直接執行原始碼
bun test                           # 測試
bun run lint                       # Lint
bunx tsc --noEmit                  # 型別檢查

# 發佈前驗證
bun test && bun run lint && bunx tsc --noEmit && bun run build
```

---

## 與 v1 的差異對照

| 面向 | v1 (Python) | v2 (Bun/TypeScript) |
|------|-------------|---------------------|
| Runtime | Python 3.13 + uv | Bun 1.3+ |
| CLI 框架 | Typer | Commander.js |
| TUI 框架 | Textual | Ink (React) |
| 終端輸出 | Rich | Chalk + ora |
| 配置讀寫 | PyYAML | yaml (npm) |
| SQLite | sqlite3 (Python stdlib) | better-sqlite3 |
| 測試 | pytest | bun test |
| Lint/Format | ruff + black | Biome |
| 型別檢查 | mypy | tsc |
| 架構 | commands/ + utils/ (兩層) | cli/ + core/ + utils/ + tui/ (四層) |
| Modal | Textual ModalScreen | useState\<Screen\> 視圖切換 |
| 套件發佈 | pip install -e . | bun add -g / npm i -g |

---

## 相關文件

| 文件 | 說明 |
|------|------|
| [copy-architecture.md](copy-architecture.md) | 三階段複製流程詳細說明 |
| [DEVELOPMENT-WORKFLOW.md](DEVELOPMENT-WORKFLOW.md) | 開發工作流程 |
| [v2 設計文件](../../plans/2026-02-24-v2-bun-migration-design.md) | v2 遷移設計決策 |
| [v2 實作計畫](../../plans/2026-02-24-v2-bun-migration-impl.md) | v2 實作步驟與 TDD 計畫 |
| `upstream/sources.yaml` | 上游來源註冊表 |
| `package.json` | 專案配置與版本定義 |

---

## 版本歷史

| 版本 | 日期 | 變更 |
|------|------|------|
| 2.0.0 | 2026-02-25 | 重寫：Python → Bun/TypeScript，四層架構，Commander.js + Ink |
| 1.0.0 | 2026-02-12 | 初版：Python/Typer 框架架構 |
