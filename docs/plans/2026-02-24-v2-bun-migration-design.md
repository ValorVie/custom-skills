# ai-dev v2：Python/uv → Bun/TypeScript 重構設計

**日期**: 2026-02-24
**版本**: v1.2.5 → v2.0.0
**套件名稱**: `@valorvie/ai-dev`

---

## 1. 動機

- **統一技術棧**：claude-mem-sync 已是 Bun/TS，CLI 從 Python 遷移到同一 runtime
- **效能提升**：Bun 啟動速度和 I/O 效能優於 Python，改善 CLI 體驗
- **npm 生態整合**：發佈為 npm 全域套件，簡化安裝與更新流程

## 2. 技術棧

| 層級 | 技術 | 取代 |
|------|------|------|
| Runtime | Bun | Python 3.13 + uv |
| CLI 框架 | Commander.js | Typer |
| TUI 框架 | Ink (React for CLI) | Textual |
| 終端美化 | Chalk | Rich |
| YAML | yaml | PyYAML |
| SQLite | better-sqlite3 | sqlite3 |
| 互動提示 | inquirer | typer.confirm/prompt |
| Spinner | ora | Rich.progress |
| Lint/Format | Biome | ruff + black |
| 測試 | bun test (內建) | pytest |
| 類型檢查 | TypeScript | mypy |

## 3. 專案結構

```
@valorvie/ai-dev
├── package.json
├── tsconfig.json
├── bunfig.toml
├── src/
│   ├── cli.ts                # 入口點 (#!/usr/bin/env bun)
│   ├── cli/                  # Commander.js 指令定義
│   │   ├── index.ts          # 註冊所有子命令
│   │   ├── install.ts
│   │   ├── update.ts
│   │   ├── clone.ts
│   │   ├── status.ts
│   │   ├── list.ts
│   │   ├── toggle.ts
│   │   ├── add-repo.ts
│   │   ├── add-custom-repo.ts
│   │   ├── update-custom-repo.ts
│   │   ├── test.ts
│   │   ├── coverage.ts
│   │   ├── derive-tests.ts
│   │   ├── project/          # 子命令組
│   │   ├── standards/
│   │   ├── hooks/
│   │   ├── sync/
│   │   └── mem/
│   ├── tui/                  # Ink 元件
│   │   ├── App.tsx
│   │   ├── components/
│   │   └── hooks/
│   ├── core/                 # 業務邏輯（純函式，無 UI 依賴）
│   │   ├── installer.ts
│   │   ├── updater.ts
│   │   ├── sync-engine.ts
│   │   ├── mem-sync.ts
│   │   ├── standards-manager.ts
│   │   └── project-manager.ts
│   └── utils/                # 工具函式
│       ├── paths.ts
│       ├── system.ts
│       ├── git.ts
│       ├── manifest.ts
│       ├── config.ts
│       └── shared.ts
├── tests/                    # bun test
├── skills/                   # 保留（非程式碼）
├── commands/                 # 保留
├── agents/                   # 保留
├── docs/                     # 保留
├── services/                 # 保留（claude-mem-sync 已是 Bun/TS）
└── dist/                     # 建置輸出
```

**關鍵設計**：`core/` 與 `cli/` 分離，業務邏輯不依賴 Commander.js 或 Ink，方便測試。

## 4. 指令映射

所有 v1 指令保持相同名稱和參數，內部重寫：

```
ai-dev --version
ai-dev install
ai-dev update
ai-dev clone
ai-dev status
ai-dev list
ai-dev toggle
ai-dev add-repo
ai-dev add-custom-repo
ai-dev update-custom-repo
ai-dev test
ai-dev coverage
ai-dev derive-tests
ai-dev tui

ai-dev project init|update
ai-dev standards status|list|switch|show|overlaps
ai-dev hooks install|uninstall|status
ai-dev sync init|push|pull|status|add|remove
ai-dev mem register|push|pull|status|reindex
```

新功能僅在 v2 加入，不回移到 v1。

### CLI 架構模式

```typescript
// src/cli/index.ts
const program = new Command()
  .name('ai-dev')
  .version(version)
  .description('AI Development Environment Setup CLI');

// 頂層指令
program.command('install').description('安裝環境').action(install);

// 子命令組
const syncCmd = program.command('sync').description('跨裝置同步');
syncCmd.command('init').option('--remote <url>').action(syncInit);
syncCmd.command('push').action(syncPush);
syncCmd.command('pull').option('--no-delete').option('--force').action(syncPull);
```

### 核心業務邏輯層

```typescript
// src/core/installer.ts
interface InstallResult {
  npmPackages: { name: string; success: boolean }[];
  repos: { name: string; success: boolean }[];
  skills: { name: string; copied: boolean }[];
}

export async function runInstall(options: InstallOptions): Promise<InstallResult> {
  // 純邏輯，不印任何東西
}
```

CLI 層呼叫 core 並用 chalk/ora 美化輸出。

## 5. 資料流

### 同步引擎

資料流不變：
```
本地目錄 → sync-repo (git) → remote
         ← sync-repo (git) ← remote
```

關鍵技術替換：
- `subprocess.run()` → `Bun.spawn()`
- `pathlib.Path` → Node.js `path` + `fs`
- `shutil.copytree` → `fs.cp()` (遞迴複製)

### Mem Sync 客戶端

資料流不變：
```
本地 SQLite (claude-mem.db) → HTTP POST → PostgreSQL (server)
本地 SQLite ← HTTP GET + import ← PostgreSQL (server)
```

關鍵技術替換：
- `urllib.request` → `fetch()` (Bun 原生)
- `sqlite3` → `better-sqlite3`
- `hashlib` → `Bun.CryptoHasher`

### 設定檔

所有 YAML 設定檔格式不變（sync.yaml, sync-server.yaml, toggle configs）。

## 6. TUI 架構 (Ink)

### 元件樹

```
<App>
├── <Header />
├── <TabBar />          # 目標選擇
├── <FilterBar />       # 類型+來源篩選
├── <ResourceList>      # 可捲動資源列表
│   └── <ResourceItem />
├── <ActionBar />       # 底部快捷鍵
```

### 導航模式：視圖切換

Ink 不支援圖層疊加（非全螢幕 TUI），使用視圖切換取代 Modal：

```typescript
type Screen = 'main' | 'preview' | 'confirm' | 'edit' | 'settings';

function App() {
  const [screen, setScreen] = useState<Screen>('main');
  const [screenProps, setScreenProps] = useState<any>(null);

  switch (screen) {
    case 'main':     return <MainScreen navigate={setScreen} />;
    case 'preview':  return <PreviewScreen data={screenProps} onBack={() => setScreen('main')} />;
    case 'confirm':  return <ConfirmScreen data={screenProps} onBack={() => setScreen('main')} />;
    case 'settings': return <SettingsScreen onBack={() => setScreen('main')} />;
  }
}
```

### 狀態管理

使用 React `useReducer` + Context：

```typescript
interface AppState {
  target: 'claude' | 'opencode' | 'codex' | 'gemini';
  typeFilter: string;
  sourceFilter: string;
  resources: Resource[];
  selectedIndex: number;
}
```

### 鍵盤快捷鍵

使用 Ink `useInput` hook，保持 v1 按鍵配置：
q(退出) space(切換) a(全選) n(新增) s(儲存) p(預覽) e(編輯器) f(檔案管理器) c(設定) t(切換目標)

## 7. 測試策略

### 框架

bun test (內建)，無需額外安裝。

### 測試結構

| v1 (pytest) | v2 (bun test) |
|-------------|---------------|
| `tests/test_sync_command.py` | `tests/cli/sync.test.ts` |
| `tests/test_mem_command.py` | `tests/cli/mem.test.ts` |
| `tests/test_sync_config.py` | `tests/core/sync-config.test.ts` |
| `tests/test_sync_engine.py` | `tests/core/sync-engine.test.ts` |
| `tests/test_mem_sync_hash.py` | `tests/core/mem-sync-hash.test.ts` |
| `tests/test_pulled_hashes.py` | `tests/core/pulled-hashes.test.ts` |
| `tests/test_clone_policy.py` | `tests/core/clone-policy.test.ts` |
| `tests/test_metadata_detection.py` | `tests/utils/metadata-detection.test.ts` |

### Mock 策略

- 檔案系統：`mock.module()` mock `fs`
- Git 操作：mock `Bun.spawn()`
- HTTP：mock `fetch()`

## 8. Git 工作流與發佈

### 分支策略

```
main (目前 v1)
  ├── v1    ← 保存 v1 快照
  └── v2    ← 重構工作，完成後合併回 main
```

步驟：
1. `git branch v1` — 保存 v1
2. `git checkout -b v2` — 建立 v2 分支
3. 移除 `script/`、`pyproject.toml`、`uv.lock`，新建 `src/`、`package.json`
4. 開發完成、測試通過後合併回 main
5. main 打 `v2.0.0` tag

### npm 發佈

```json
{
  "name": "@valorvie/ai-dev",
  "version": "2.0.0",
  "type": "module",
  "bin": { "ai-dev": "./dist/cli.js" },
  "files": ["dist/", "skills/", "commands/", "agents/"],
  "publishConfig": { "access": "public" }
}
```

### 版本規則

- v2.0.0：首個 Bun/TS 版本
- 後續遵循 semver

## 9. 移除項目

v2 中移除的 Python 檔案/目錄：
- `script/` — 整個 Python CLI 程式碼
- `pyproject.toml` — Python 專案配置
- `uv.lock` — uv lock 檔
- `ai_dev.egg-info/` — Python 打包產物
- `tests/` — Python 測試（以 TS 測試取代）

## 10. 保留項目（不動）

- `skills/` — AI 技能檔案
- `commands/` — Claude Code commands
- `agents/` — Agent 配置
- `docs/` — 文件
- `services/` — claude-mem-sync (已是 Bun/TS)
- `settings/` — 設定檔
- `project-template/` — 專案模板
- `openspec/` — OpenSpec 規格
- `.standards/` — 標準檔案
- 所有 `.md` 檔案 (README, CLAUDE, IDENTITY 等)
