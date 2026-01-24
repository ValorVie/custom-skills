# Design: 全面整合 everything-claude-code 並擴展標準體系

## Context

本專案已完成 everything-claude-code (ecc) 的初步評估，識別出多項有價值的資源。此設計文件規劃如何：
1. 完整整合 High Priority 項目
2. 擴展參考資源（OpenCode, MCP Configs）
3. 建立可切換的標準體系架構
4. 整合 TDD 最佳實踐

### 約束條件

- ecc 資源保持 Claude Code 原生格式，不轉換為 UDS 格式
- Hooks 需從 Node.js 重寫為 Python 以確保跨平台相容
- 標準體系切換必須是非破壞性的（switching doesn't delete user customizations）

## Goals / Non-Goals

### Goals

1. **完整整合 ecc 優先項目** — 6 hooks, 4 skills, 4 agents, 6 commands
2. **建立標準體系架構** — 支援 UDS, ECC, Minimal 三種 profile
3. **TDD 實踐整合** — 保留 UDS 理論深度，補充 ecc 實戰範例
4. **OpenCode/MCP 參考** — 提供配置範例

### Non-Goals

- 不將 ecc 格式轉換為 UDS 格式
- 不整合 ecc 專案特定內容（clickhouse-io, project-guidelines-example）
- 不整合 Claude Plugin System（本專案採用 skill-based 發布）
- 不自動同步 ecc 更新（保持 `ai-dev update --sync-upstream` 手動觸發）

## Decisions

### 決策 1：Hook 實作語言

**決策**: 將 ecc 的 Node.js hooks 重寫為 Python

**理由**:
- 本專案 CLI (`ai-dev`) 已使用 Python
- Python 在 Windows 上的支援更穩定
- 減少 Node.js 依賴
- 便於與 `ai-dev` 指令整合

**替代方案考慮**:
- 保持 Node.js：需要使用者安裝 Node.js，增加依賴
- 使用 Shell scripts：Windows 相容性差

### 決策 2：標準體系切換架構

**決策**: 使用 YAML profile 檔案控制標準載入

```yaml
# .standards/profiles/ecc.yaml
name: everything-claude-code
description: TypeScript/React 專注的實戰導向標準
inherits: minimal  # 繼承基礎標準

includes:
  - coding-standards.md
  - testing.ai.yaml
  - checkin-standards.md

overrides:
  commit-message:
    type-language: english  # feat/fix/docs instead of 功能/修正/文件
  testing:
    coverage-threshold: 80%
    tdd-required: true
```

**理由**:
- 宣告式配置易於理解和維護
- 支援繼承減少重複
- 可擴展新 profile

**替代方案考慮**:
- 環境變數切換：不夠直觀
- 目錄結構切換：需要複製大量檔案

### 決策 3：ecc 資源目錄結構

**決策**: 使用 `sources/ecc/` 獨立目錄

```
sources/
└── ecc/                         # everything-claude-code
    ├── agents/
    ├── commands/
    ├── skills/
    ├── hooks/
    │   ├── memory-persistence/
    │   ├── strategic-compact/
    │   └── hooks.json
    ├── plugins/                 # OpenCode 整合
    ├── mcp-configs/
    └── README.md
```

**理由**:
- 與 UDS 資源（`skills/`, `.standards/`）明確分離
- 保持 ecc 原生格式不需轉換
- 便於追蹤 upstream 更新

### 決策 4：TDD 整合策略

**決策**: 保留 UDS TDD 標準為主體，ecc 作為實戰補充

**具體實作**:

```markdown
# .standards/test-driven-development.md（新增章節）

## 附錄：實戰範例

詳細的 Jest/Vitest/Playwright 範例請參考：
- [ecc TDD Workflow](../sources/ecc/skills/tdd-workflow/SKILL.md)
- [Mock 範例](../sources/ecc/skills/tdd-workflow/SKILL.md#mocking-external-services)
- [測試檔案組織](../sources/ecc/skills/tdd-workflow/SKILL.md#test-file-organization)
```

**理由**:
- UDS 理論深度高，不應被取代
- ecc 實戰範例價值高，應保留完整
- 交叉引用而非合併，保持各自完整性

## Component Architecture

### 標準體系架構

```
┌─────────────────────────────────────────────────────────────────┐
│                    Standards Profile System                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐        │
│  │  UDS       │    │    ECC      │    │  Minimal    │        │
│  │  Profile   │    │   Profile   │    │  Profile    │        │
│  └─────┬──────┘    └─────┬───────┘    └─────┬───────┘        │
│        │                 │                   │                 │
│        └────────────┬────┴───────────────────┘                 │
│                     ▼                                          │
│              ┌──────────────┐                                  │
│              │ active-      │                                  │
│              │ profile.yaml │                                  │
│              └──────┬───────┘                                  │
│                     │                                          │
│                     ▼                                          │
│           ┌──────────────────┐                                 │
│           │  Standards Loader │                                │
│           │  (ai-dev CLI)    │                                │
│           └──────────────────┘                                 │
│                     │                                          │
│                     ▼                                          │
│           ┌──────────────────┐                                 │
│           │ Active Standards │                                 │
│           │ (loaded to AI)   │                                 │
│           └──────────────────┘                                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Hook 系統架構

```
┌─────────────────────────────────────────────────────────────────┐
│                    Claude Code Hook Integration                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Claude Code Events                                             │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐              │
│  │SessionStart │ │ PreToolUse  │ │ SessionEnd  │              │
│  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘              │
│         │               │               │                       │
│         ▼               ▼               ▼                       │
│  ┌─────────────────────────────────────────────────────┐       │
│  │                   hooks.json                         │       │
│  │  (事件 → 腳本對應表)                                  │       │
│  └─────────────────────────────────────────────────────┘       │
│         │               │               │                       │
│         ▼               ▼               ▼                       │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐               │
│  │session-    │  │suggest-    │  │session-    │               │
│  │start.py    │  │compact.py  │  │end.py      │               │
│  └────────────┘  └────────────┘  └────────────┘               │
│         │                               │                       │
│         ▼                               ▼                       │
│  ┌─────────────────────────────────────────────────────┐       │
│  │              Session State Storage                    │       │
│  │  (~/.claude/sessions/ or project-local)               │       │
│  └─────────────────────────────────────────────────────┘       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Risks / Trade-offs

| 風險 | 影響 | 機率 | 緩解措施 |
|------|------|------|----------|
| Python hooks 效能不如 Node.js | 低 | 低 | Hooks 執行頻率低，效能差異可忽略 |
| 標準體系切換導致配置混亂 | 中 | 低 | 預設使用 UDS，切換前顯示變更預覽 |
| ecc 更新後格式不相容 | 中 | 低 | 手動 `--sync-upstream` 審核後合併 |
| 使用者分不清 UDS vs ecc 資源 | 中 | 中 | 明確的目錄結構與 README 說明 |

## Migration Plan

### Phase 1: Hook 系統（優先）

1. 建立 `sources/ecc/hooks/` 目錄結構
2. 重寫 `session-start.py`, `session-end.py`, `pre-compact.py`
3. 重寫 `suggest-compact.py`
4. 建立 `hooks.json` 配置（保持 ecc 原格式）
5. 測試 Windows/macOS/Linux 相容性

### Phase 2: Skills, Agents, Commands

1. 複製 ecc skills 到 `sources/ecc/skills/`
2. 複製 ecc agents 到 `sources/ecc/agents/`
3. 複製 ecc commands 到 `sources/ecc/commands/`
4. 更新 `upstream/ecc/mapping.yaml`

### Phase 3: 標準體系架構

1. 建立 `.standards/profiles/` 目錄
2. 定義 `uds.yaml`, `ecc.yaml`, `minimal.yaml`
3. 實作 `script/commands/standards.py`
4. 整合至 `ai-dev` CLI

### Phase 4: TDD 整合 & 文件

1. 更新 `.standards/test-driven-development.md` 新增附錄
2. 建立 `sources/ecc/skills/tdd-workflow/` 連結
3. 更新 README 說明

### Rollback

- 每個 Phase 獨立，可單獨回滾
- Phase 3 標準體系可透過刪除 `active-profile.yaml` 回到預設
- Phase 1-2 複製的資源不影響現有功能

## Open Questions

1. **hooks.json 格式統一？**
   - 目前 ecc 使用特定格式，是否需要統一為本專案格式？
   - 建議：保持 ecc 原格式，在 README 中說明使用方式

2. **profile 繼承層級？**
   - 目前設計為單層繼承（ecc inherits minimal）
   - 是否需要支援多層繼承？
   - 建議：先實作單層，需求明確後再擴展

3. **ai-dev standards 子命令範圍？**
   - `use`, `list` 是否足夠？
   - 是否需要 `show`, `diff`, `export`？
   - 建議：先實作 `use`, `list`，根據使用反饋擴展
