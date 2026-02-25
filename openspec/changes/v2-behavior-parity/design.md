# Design: v2 行為對齊 v1

## Context

v2 ai-dev CLI 從 Python (Typer + Rich) 遷移到 TypeScript (Commander.js + Bun)，目前已完成 CLI 骨架和基礎 core 層，但 17 個指令中有 80 項功能缺失（P0: 32, P1: 31, P2: 12, P3: 5）。

**現有架構：**

```
src/
├── cli/          # Commander.js 指令註冊（薄層，呼叫 core）
├── core/         # 業務邏輯（installer, updater, sync-engine 等）
├── tui/          # Ink (React) 終端 UI
└── utils/        # 共用工具（paths, shared, system）
```

**v1 架構（對照）：**

```
script/
├── commands/     # Typer + Rich 指令（邏輯混在 CLI 層）
├── utils/        # 共用工具
└── tui/          # Textual TUI
```

v2 已有的良好分層（CLI → core → utils）應該保留並強化。主要工作是補齊 core 層缺失邏輯和 CLI 層格式化輸出。

## Goals / Non-Goals

**Goals:**
- 所有 17 個指令行為與 v1 完全一致
- 格式化輸出品質與 v1 Rich 相當（表格、色彩、進度條）
- 輸出語言可配置（預設 English，可切換 zh-TW）
- 保持 v2 的 CLI/core 分層架構
- 新增程式碼有測試覆蓋

**Non-Goals:**
- 不遷移 v1 的 Textual TUI（v2 已有 Ink TUI）
- 不改變 CLI 框架（保留 Commander.js）
- 不新增 v1 沒有的功能
- 不重構已正常運作的 core 模組

## Decisions

### D1: 格式化輸出方案 — chalk + ora + cli-table3

**選擇：** 使用 `chalk`（已有）+ `ora`（已有）+ `cli-table3`（新增）

| 需求 | v1 Rich | v2 方案 |
|------|---------|---------|
| 彩色文字 | `rich.print("[green]OK[/]")` | `chalk.green("OK")` |
| 表格 | `rich.Table()` | `cli-table3` |
| 進度條/spinner | `rich.Progress()` | `ora` |
| 互動選單 | — | `inquirer`（已有） |
| 面板/樹 | `rich.Panel()` / `rich.Tree()` | chalk 框線 + 縮排（簡化） |

**替代方案考慮：**
- `tty-table`：功能更多但 dependencies 較多，overkill
- `columnify`：過於簡陋，無邊框
- 自行實作：維護成本高，不值得
- 全部用 Ink：Ink 是 React-based，不適合一次性 CLI 輸出

**封裝：** 建立 `src/utils/formatter.ts` 統一封裝，避免各指令直接依賴 cli-table3。

```typescript
// src/utils/formatter.ts
export function printTable(headers: string[], rows: string[][]): void;
export function printSuccess(msg: string): void;
export function printError(msg: string): void;
export function printWarning(msg: string): void;
export function createSpinner(text: string): ora.Ora;
export function printPanel(title: string, content: string): void;
```

### D2: i18n 方案 — 輕量 key-value 字典

**選擇：** 自行實作簡單 i18n，不使用 i18next 等重量級框架。

**理由：** CLI 工具的字串量有限（估計 200-300 條），不需要複數形式、日期格式等高級功能。

```typescript
// src/utils/i18n.ts
type Locale = "en" | "zh-TW";

const messages: Record<Locale, Record<string, string>> = {
  en: { "install.checking_prerequisites": "Checking prerequisites..." },
  "zh-TW": { "install.checking_prerequisites": "檢查前置需求..." },
};

export function t(key: string, params?: Record<string, string>): string;
export function setLocale(locale: Locale): void;
export function getLocale(): Locale;
```

**配置來源優先順序：**
1. `--lang` 全域 CLI 選項（最高優先）
2. `~/.config/ai-dev/config.yaml` 中的 `locale` 設定
3. 預設 `en`

**替代方案考慮：**
- `i18next`：功能強大但對 CLI 工具來說過重
- `@formatjs/intl`：ICU 格式，過度設計

### D3: core 層修復策略 — 漸進式補強

**選擇：** 不重寫 core 模組，而是在現有介面上逐步補齊缺失功能。

**理由：**
- v2 core 已有良好的介面設計（`InstallOptions`, `UpdateOptions` 等）
- `onProgress` callback 模式已證明有效
- 避免大規模重寫帶來的風險

**具體做法：**
- **installer.ts**：在現有 `runInstall()` 中按 v1 順序插入缺失步驟
- **updater.ts**：同上
- **sync-engine.ts**：將 `fs.cp` 改為 git operations
- **mem-sync.ts**：將 stub 改為實際 HTTP API 呼叫
- **project-manager.ts**：補充 .gitignore 合併和備份邏輯
- **standards-manager.ts**：補充 `compute_disabled_items()` 和 `sync` 方法

### D4: copy_skills 分發機制

**選擇：** 新建 `src/core/skill-distributor.ts` 模組

**v1 行為：**
1. 掃描所有 skills/commands/agents/workflows 目錄
2. 對每個 target（claude/opencode/gemini/codex/antigravity）建立目標目錄
3. 複製檔案到目標目錄
4. 偵測命名衝突並警告
5. 開發者模式下使用 symlink 而非 copy

**v2 設計：**
```typescript
// src/core/skill-distributor.ts
export interface DistributeOptions {
  force?: boolean;
  skipConflicts?: boolean;
  backup?: boolean;
  devMode?: boolean;  // 使用 symlink
  onProgress?: (msg: string) => void;
}

export interface DistributeResult {
  distributed: { name: string; target: string; type: string }[];
  conflicts: { name: string; sources: string[] }[];
  errors: string[];
}

export async function distributeSkills(opts?: DistributeOptions): Promise<DistributeResult>;
```

### D5: 備份機制

**選擇：** 新建 `src/utils/backup.ts` 共用模組

v1 的 `backup_dirty_files` 用於 update 和 update-custom-repo，在 `git reset --hard` 前自動備份已修改的檔案。

```typescript
// src/utils/backup.ts
export async function hasLocalChanges(repoDir: string): Promise<boolean>;
export async function backupDirtyFiles(repoDir: string): Promise<string>; // returns backup dir path
export async function restoreBackup(backupDir: string, targetDir: string): Promise<void>;
```

### D6: hooks install 實作

**選擇：** 實際複製 ECC hooks plugin 檔案，而非只建立 README。

v1 的 hooks install 會從 everything-claude-code repo 複製 hooks plugin 到 `.claude/plugins/`。v2 目前只建立一個 README.md，需要改為實際功能。

## Risks / Trade-offs

### [Risk] cli-table3 在 Bun 相容性 → Mitigation: cli-table3 是純 JS，無 native bindings，Bun 相容性良好

### [Risk] i18n 字串量大，初始開發成本高 → Mitigation: Phase 0 只建立框架，Phase 1-3 逐步補充字串。可先用英文開發，最後統一翻譯

### [Risk] mem push/pull 需要後端 API，如果 API 不可用則功能無法測試 → Mitigation: 使用 dependency injection（已有 `MemSyncDeps`），測試時 mock HTTP client

### [Risk] sync push/pull 改用 git operations 後行為變複雜 → Mitigation: 保持 v1 的 git 指令順序，逐步測試每個子命令

### [Risk] 80 項缺失量大，一次全改風險高 → Mitigation: 嚴格按 Phase 0 → 1 → 2 → 3 順序執行，每個 Phase 完成後跑全部測試

### [Trade-off] Panel/Tree 簡化為 chalk 框線

v1 的 Rich Panel 和 Tree 在 TypeScript 生態中沒有直接對等套件。選擇用 chalk + 手動排版模擬，視覺效果可能略有差異，但資訊傳達相同。如果未來需要更豐富的 TUI，可以考慮在 Ink 中實作。

## Open Questions

1. **mem sync 後端 API endpoint** — v1 的 HTTP API URL 和認證方式需要從 v1 程式碼或文件確認
2. **shell completion 安裝** — Commander.js 是否有內建 completion 支援，或需要額外套件？
3. **Plugin Marketplace 更新** — v1 的 Plugin Marketplace 更新邏輯需要確認是否仍然適用
