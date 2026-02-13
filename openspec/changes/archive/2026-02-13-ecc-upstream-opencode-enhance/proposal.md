## Why

Everything Claude Code (ECC) 上游在 2026-02-03 至 02-06 期間新增了 OpenCode plugin hooks 架構、multi-agent orchestration 命令、以及 PM2 服務管理命令。本專案雖已有 41 個 OpenCode commands 和 11 個 agents，但缺少三項能力：(1) OpenCode plugin hooks（利用 file.edited / file.watcher 等 20+ 事件提供逐檔粒度自動化），(2) agent orchestration 工作流模板，(3) PM2 自動化服務管理。這些功能可直接強化本專案的 OpenCode 支援層。

## What Changes

- **新增 OpenCode plugin hooks**：移植 ECC 的 `ecc-hooks.ts` 到 `.opencode/plugins/`，適配本專案結構，提供 file.edited 自動格式化、session.idle 彙總稽核、file.watcher 外部變更偵測等能力
- **新增 OpenCode 自訂工具**：移植 run-tests / check-coverage / security-audit 三個 TypeScript 工具到 `.opencode/tools/`
- **新增 orchestrate 命令**：移植 `orchestrate.md` 到 `commands/claude/` 和 `commands/opencode/`，提供 feature / bugfix / refactor / security 四種工作流模板，對映本專案現有 agent 名稱
- **新增 pm2 命令**：移植 `pm2.md` 到 `commands/claude/` 和 `commands/opencode/`，提供自動偵測框架/埠口並生成 PM2 配置的能力

## Capabilities

### New Capabilities

- `opencode-hooks`: OpenCode plugin hooks 架構，提供逐檔粒度的自動化事件處理（file.edited / session.idle / file.watcher / permission.asked / todo.updated）
- `opencode-tools`: OpenCode 自訂工具（run-tests / check-coverage / security-audit），自動偵測測試框架與套件管理器
- `orchestrate-command`: Multi-agent orchestration 命令，提供 4 種預定義工作流模板與自訂工作流支援
- `pm2-command`: PM2 服務管理命令，自動分析專案結構並生成 PM2 配置

### Modified Capabilities

- `opencode-plugin`: 需更新 `.opencode/` 目錄結構以容納新的 plugins 和 tools

## Impact

- **檔案新增**：`.opencode/plugins/hooks.ts`、`.opencode/tools/*.ts`、`commands/claude/orchestrate.md`、`commands/claude/pm2.md`、`commands/opencode/orchestrate.md`、`commands/opencode/pm2.md`
- **檔案修改**：`.opencode/package.json`（新增依賴）、`.opencode/index.ts`（匯出 hooks 和 tools）
- **依賴**：無外部依賴，所有功能自含於 TypeScript 和 Markdown
- **風險**：hooks 中的格式化工具（Prettier）需確認本專案是否已安裝；agent 名稱對映需驗證
