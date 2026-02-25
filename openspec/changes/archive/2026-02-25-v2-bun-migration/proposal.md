## Why

ai-dev CLI 目前以 Python (Typer + Rich + Textual) 實作，而 claude-mem-sync 服務已是 Bun/TypeScript。維護兩套語言增加認知負擔與工具鏈成本。遷移到 Bun/TypeScript 可統一技術棧、提升 CLI 啟動速度與 I/O 效能，並以 `@valorvie/ai-dev` npm 套件發佈，簡化安裝與更新。

詳細設計與實作計畫參見：
- [設計文件](../../docs/plans/2026-02-24-v2-bun-migration-design.md)
- [實作計畫](../../docs/plans/2026-02-24-v2-bun-migration-impl.md)

## What Changes

- **BREAKING** 移除整個 Python CLI (`script/`、`pyproject.toml`、`uv.lock`)，以 TypeScript 重寫
- **BREAKING** 執行環境從 Python 3.13 + uv 改為 Bun runtime
- CLI 框架從 Typer 遷移到 Commander.js，保持所有指令名稱與參數相容
- TUI 框架從 Textual 遷移到 Ink (React for CLI)，Modal 改為視圖切換模式
- 終端輸出從 Rich 改為 Chalk + ora
- 測試框架從 pytest 改為 bun test
- Lint/Format 從 ruff + black 改為 Biome
- 發佈為 `@valorvie/ai-dev` scoped npm 套件
- 版本號從 v1.2.5 跳至 v2.0.0
- 架構重新分層：`src/cli/`（指令定義）、`src/core/`（業務邏輯）、`src/utils/`（工具函式）、`src/tui/`（Ink 元件）

## Capabilities

### New Capabilities

- `ts-cli-framework`: TypeScript CLI 骨架 — Commander.js 主程式、入口點 (`src/cli.ts`)、版本管理
- `ts-utils-layer`: TypeScript 工具層 — paths、system、config (YAML)、git、manifest、shared constants
- `ts-core-layer`: TypeScript 核心業務邏輯層 — installer、updater、status-checker、sync-engine、mem-sync、standards-manager、project-manager（純函式，無 UI 依賴）
- `ts-tui`: Ink TUI — App 根元件、視圖切換路由、MainScreen、PreviewScreen、ConfirmScreen、SettingsScreen、所有子元件 (Header, TabBar, FilterBar, ResourceList, ActionBar)
- `npm-publish`: npm 發佈配置 — package.json bin/files 設定、建置腳本、scoped package 發佈

### Modified Capabilities

- `setup-script`: 安裝腳本改為 Bun/npm 全域安裝方式
- `cli-distribution`: 分發機制從 `pip install -e .` 改為 `bun add -g @valorvie/ai-dev`
- `skill-tui`: TUI 框架從 Textual 改為 Ink，Modal 改為視圖切換

## Impact

- **程式碼**：移除約 9,200 行 Python，新增等量 TypeScript
- **依賴**：移除 Python 依賴 (typer, rich, textual, pyyaml)；新增 npm 依賴 (commander, ink, react, chalk, yaml, better-sqlite3, ora, inquirer)
- **開發工具**：從 ruff + black + mypy + pytest 改為 biome + tsc + bun test
- **使用者影響**：需要 Bun runtime（取代 Python 3.13 + uv）；CLI 指令介面保持相容
- **非程式碼資源不受影響**：skills/、commands/、agents/、docs/、services/、.standards/ 全部保留
- **Git 分支**：v1 保存為 `v1` 分支，v2 開發於 `v2` 分支，完成後合併回 main
