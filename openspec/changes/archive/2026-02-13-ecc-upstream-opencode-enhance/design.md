## Context

本專案已有完整的 OpenCode 支援（41 commands、11 agents、`.opencode/` 配置目錄），但缺少三項能力：

1. **OpenCode plugin hooks**：現有 `plugins/ecc-hooks-opencode/` 只處理 tool.execute.before/after 和 session 事件，未利用 OpenCode 獨有的 file.edited / file.watcher.updated 等逐檔粒度事件
2. **Agent orchestration**：無預定義的多 agent 協調工作流模板
3. **PM2 管理**：無自動化的多服務行程管理命令

ECC 上游在 commit `6d440c0`、`6b424e3` 中提供了這些功能的實作。

## Goals / Non-Goals

**Goals:**

- 移植 ECC 的 OpenCode plugin hooks，擴充現有 plugin 支援 file.edited / file.watcher / session.idle / permission.asked / todo.updated 事件
- 移植 ECC 的 3 個自訂工具（run-tests / check-coverage / security-audit）
- 新增 orchestrate 命令（claude + opencode 雙版本），提供 feature / bugfix / refactor / security 工作流模板
- 新增 pm2 命令（claude + opencode 雙版本），自動偵測專案結構生成 PM2 配置

**Non-Goals:**

- 不移植 multi-plan / multi-execute / multi-backend / multi-frontend / multi-workflow（依賴 ECC 私有基礎設施 codeagent-wrapper）
- 不移植 ECC rules 結構（本專案使用 UDS `.standards/` 體系）
- 不移植 configure-ecc 安裝精靈（ECC 專用）
- 不改變現有 `.opencode/` 的 commands 和 agents 結構

## Decisions

### D1: Hooks 擴充策略 — 擴充現有 plugin vs 新增獨立 plugin

**決定**：擴充現有 `plugins/ecc-hooks-opencode/plugin.ts`

**理由**：
- 現有 plugin 已處理 tool.execute 和 session 事件
- 新增事件是同類型的擴充，不是獨立功能
- 避免多個 plugin 之間的狀態共享問題
- 替代方案（新增獨立 plugin）會增加維護成本且無法共享編輯追蹤狀態

### D2: 自訂工具放置位置 — `.opencode/tools/` vs `plugins/ecc-hooks-opencode/tools/`

**決定**：放在 `.opencode/tools/`

**理由**：
- OpenCode 的工具載入機制從 `.opencode/tools/` 掃描
- 與 ECC 上游保持一致的目錄結構
- 工具是獨立的，不依賴 hooks plugin 狀態

### D3: Agent 名稱對映策略

**決定**：在 orchestrate 命令中使用本專案的 agent 名稱，並提供對映表

**對映表**：
| ECC Agent | Custom-Skills Agent | 備註 |
|-----------|-------------------|------|
| planner | code-architect | 最接近的規劃角色 |
| tdd-guide | test-specialist | TDD 相關 |
| code-reviewer | reviewer | 程式碼審查 |
| security-reviewer | security-reviewer | 名稱一致 |
| architect | code-architect | 架構設計 |
| doc-updater | doc-writer / doc-updater | 文件更新 |

### D4: PM2 命令路徑適配

**決定**：將 ECC 的 `.claude/commands/` 和 `.claude/scripts/` 路徑替換為本專案的 `commands/` 結構

**理由**：本專案使用 `commands/claude/` 和 `commands/opencode/` 分離式結構，不使用 `.claude/commands/`

### D5: Hooks 中的格式化工具處理

**決定**：hooks 中的格式化呼叫改為條件式執行（檢查工具是否安裝）

**理由**：
- ECC 假設 Prettier 已安裝，但本專案可能在非 JS 專案中使用
- 條件式執行避免因缺少工具而報錯
- 替代方案（移除格式化）會損失 file.edited 的核心價值

## Risks / Trade-offs

- **[Risk] OpenCode plugin API 可能變更** → hooks 以事件名稱為介面，OpenCode 更新時需確認事件名稱是否相容。Mitigation：鎖定 OpenCode 版本，定期追蹤上游
- **[Risk] file.watcher 事件在大專案中可能產生噪音** → Mitigation：加入 debounce 機制和可配置的忽略 pattern
- **[Risk] orchestrate 命令中的 agent 可能在某些環境不可用** → Mitigation：工作流模板中加入 fallback 說明
- **[Trade-off] hooks 擴充增加 plugin.ts 複雜度** → 接受，因為統一入口比分散 plugin 更易維護
