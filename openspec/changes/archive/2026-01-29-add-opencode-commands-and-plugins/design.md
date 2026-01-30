## Context

custom-skills 專案管理多個 AI 平台的 skills、commands、agents 和 plugins。目前透過 `ai-dev clone` 分發到 Claude Code、OpenCode、Gemini、Codex、Antigravity 等目標。

OpenCode 的分發已支援 skills 和 agents，但 commands 缺少來源目錄（`commands/opencode/` 不存在），plugins 也沒有 OpenCode 版本。

現有架構：
- `commands/claude/` → 41 個 .md 檔案，使用 Claude Code frontmatter 格式
- `plugins/ecc-hooks/` → Claude Code hooks.json 格式，包含 code quality、memory persistence、strategic compact 腳本
- `script/utils/shared.py` → 分發邏輯，已有 `src_cmd_opencode` 變數但目錄不存在

## Goals / Non-Goals

**Goals:**
- `ai-dev clone` 後 OpenCode 使用者可取得與 Claude Code 對等的 commands
- OpenCode 版 ecc-hooks plugin 能觸發同一批 scripts（code quality、memory persistence、strategic compact）
- 分發流程自動包含 OpenCode plugin

**Non-Goals:**
- 不重寫底層 scripts（JS/Python），只寫 TypeScript wrapper 層
- 不修改 Claude Code 現有的 hooks.json 格式
- 不為 OpenCode plugin 新增 Claude Code 沒有的功能
- 不處理 OpenCode 的 experimental config-based hooks（只用 plugin 系統）

## Decisions

### Decision 1: Commands 格式策略 — 直接複製並清理 frontmatter

**選擇**: 從 `commands/claude/` 複製所有 .md 檔案到 `commands/opencode/`，移除 Claude 特有的 `allowed-tools` 和 `argument-hint` frontmatter 欄位，保留 `description`。

**替代方案**:
- A) 共用 `commands/shared/`，分發時動態轉換 → 需改分發邏輯，增加複雜度
- B) 原封不動複製（OpenCode 忽略不認識的欄位）→ 雖可行但不乾淨

**理由**: OpenCode 確實會忽略不認識的欄位，但維護兩份各自乾淨的 commands 更符合現有的多平台分離模式（如 `agents/claude/` 和 `agents/opencode/` 就是分開維護的）。

### Decision 2: Plugin 架構 — TypeScript wrapper 呼叫現有 scripts

**選擇**: 建立 `plugins/ecc-hooks-opencode/`，內含一個 TypeScript plugin 檔案，透過 OpenCode 的 hook 事件（`tool.execute.before`、`tool.execute.after`、`session.created` 等）呼叫 `plugins/ecc-hooks/scripts/` 中的現有腳本。

**替代方案**:
- A) 完全用 TypeScript 重寫所有邏輯 → 工作量大，且需雙重維護
- B) 暫不支援 OpenCode plugins → 功能缺失

**理由**: 共用 scripts 層可確保兩個平台行為一致，只需維護一份核心邏輯。TypeScript wrapper 只負責事件路由。

### Decision 3: Plugin scripts 路徑解析

**選擇**: OpenCode plugin 執行時，透過相對路徑引用同級 `scripts/` 目錄。分發時將 `plugins/ecc-hooks/scripts/` 一併複製到 OpenCode plugin 目錄下。

**理由**: OpenCode plugin 的工作目錄是 plugin 所在目錄，可以用 `import.meta.dir` 取得路徑。分發時複製 scripts 確保獨立運作，不依賴 Claude Code plugin 的安裝。

### Decision 4: 分發路徑

**選擇**: 在 `COPY_TARGETS["opencode"]` 新增 `"plugins"` 項目，目標為 `~/.config/opencode/plugin/ecc-hooks/`。在 `paths.py` 新增 `get_opencode_plugin_dir()` 函式。

**理由**: 遵循現有的分發架構模式，一致性高。

## Risks / Trade-offs

- **[Risk] Scripts 路徑在 OpenCode 環境中不同** → 使用 `import.meta.dir` 動態取得，不寫死路徑
- **[Risk] OpenCode plugin API 可能變更**（部分 hook 標記為 experimental）→ 使用穩定的 `tool.execute.before/after` 和 `event` hook，minimise experimental API 依賴
- **[Risk] Commands 內容漂移** → 未來可考慮自動化同步腳本，目前手動維護
- **[Trade-off] Scripts 複製到兩個地方** → 雖有重複，但確保各平台 plugin 獨立運作
