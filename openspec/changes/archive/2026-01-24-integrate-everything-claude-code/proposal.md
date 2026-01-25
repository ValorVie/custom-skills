# Change: 整合 everything-claude-code 專案

## Why

[everything-claude-code](https://github.com/affaan-m/everything-claude-code) 是經過實戰驗證的 Claude Code 配置套件（21.8k stars, MIT License）。透過詳細評估後，選擇性整合有價值的內容到本專案。

## 格式說明

**重要區分：**

| 系統 | 格式 | 目錄 | 說明 |
|------|------|------|------|
| **UDS** | YAML frontmatter + Markdown | `.standards/`, `skills/agents/` | 本專案自有標準格式 |
| **Claude Code 原生** | 純 Markdown（無 frontmatter） | `sources/ecc/` | ecc 等第三方 repo 格式 |

- ecc 資源**保持 Claude Code 原生格式**，不轉換為 UDS 格式
- ecc 資源放在 `sources/ecc/` 目錄，與 UDS 資源分開
- 不將 ecc rules 放入 `.standards/` 目錄

## 整合評估

### Agents 評估

| ecc Agent | UDS 對應 | 決策 | 目標位置 |
|-----------|----------|------|----------|
| `architect.md` | `code-architect.md` | **參考** | 保持分離，作為補充參考 |
| `code-reviewer.md` | `reviewer.md` | **參考** | 保持分離，作為補充參考 |
| `doc-updater.md` | `doc-writer.md` | **參考** | 保持分離，作為補充參考 |
| `tdd-guide.md` | - | **新增** | `sources/ecc/agents/` |
| `build-error-resolver.md` | - | **新增** | `sources/ecc/agents/` |
| `e2e-runner.md` | - | **新增** | `sources/ecc/agents/` |
| `planner.md` | - | **新增** | `sources/ecc/agents/` |
| `refactor-cleaner.md` | - | **新增** | `sources/ecc/agents/` |
| `security-reviewer.md` | - | **新增** | `sources/ecc/agents/` |

### Commands 評估

| ecc Command | UDS 對應 | 決策 | 目標位置 |
|-------------|----------|------|----------|
| `tdd.md` | `tdd.md` | **參考** | 保持分離，作為補充參考 |
| `code-review.md` | `review.md` | **參考** | 保持分離，作為補充參考 |
| `test-coverage.md` | `coverage.md` | **參考** | 保持分離，作為補充參考 |
| `build-fix.md` | - | **新增** | `sources/ecc/commands/` |
| `e2e.md` | - | **新增** | `sources/ecc/commands/` |
| `plan.md` | - | **新增** | `sources/ecc/commands/` |
| `learn.md` | - | **新增** | `sources/ecc/commands/` |
| `verify.md` | - | **新增** | `sources/ecc/commands/` |
| `setup-pm.md` | - | **新增** | `sources/ecc/commands/` |
| `refactor-clean.md` | - | **新增** | `sources/ecc/commands/` |
| `checkpoint.md` | - | **新增** | `sources/ecc/commands/` |
| `orchestrate.md` | - | **新增** | `sources/ecc/commands/` |
| `eval.md` | - | **新增** | `sources/ecc/commands/` |
| `update-codemaps.md` | - | **不採用** | 較專案特定 |
| `update-docs.md` | - | **不採用** | 與 UDS doc-writer 重疊 |

### Skills 評估

| ecc Skill | UDS 對應 | 決策 | 目標位置 |
|-----------|----------|------|----------|
| `coding-standards/` | `.standards/` | **參考** | 保持分離，作為補充參考 |
| `tdd-workflow/` | `bdd-assistant/` | **參考** | 保持分離，作為補充參考 |
| `backend-patterns/` | - | **新增** | `sources/ecc/skills/` |
| `frontend-patterns/` | - | **新增** | `sources/ecc/skills/` |
| `security-review/` | - | **新增** | `sources/ecc/skills/` |
| `eval-harness/` | - | **新增** | `sources/ecc/skills/` |
| `continuous-learning/` | - | **新增** | `sources/ecc/skills/` |
| `verification-loop/` | - | **新增** | `sources/ecc/skills/` |
| `strategic-compact/` | - | **新增** | `sources/ecc/skills/` |
| `clickhouse-io/` | - | **不採用** | 專案特定 |
| `project-guidelines-example/` | - | **不採用** | 範例，非核心功能 |

### Hooks 評估

| ecc Hook | 決策 | 目標位置 |
|----------|------|----------|
| `memory-persistence/` | **新增 (Python)** | `sources/ecc/hooks/` - 需重寫為 Python |
| `strategic-compact/` | **新增 (Python)** | `sources/ecc/hooks/` - 需重寫為 Python |
| `hooks.json` | **新增** | `sources/ecc/hooks/` - 配置檔參考 |
| PreToolUse hooks | **參考** | 4 個 hooks：Dev Server Blocker 等 |
| PostToolUse hooks | **參考** | 4 個 hooks：Prettier、TypeScript 等 |
| SessionStart/End hooks | **新增 (Python)** | `sources/ecc/hooks/` - 狀態持久化 |

### Rules 評估

| ecc Rule | UDS 對應 | 決策 | 目標位置 |
|----------|----------|------|----------|
| `security.md` | `.standards/` 相關 | **新增** | `sources/ecc/rules/` |
| `performance.md` | - | **新增** | `sources/ecc/rules/` |
| `agents.md` | - | **新增** | `sources/ecc/rules/` |
| `hooks.md` | - | **新增** | `sources/ecc/rules/` |
| `coding-style.md` | `.standards/` 相關 | **參考** | 保持分離，作為補充參考 |
| `git-workflow.md` | `.standards/` 相關 | **參考** | 保持分離，作為補充參考 |
| `testing.md` | `.standards/` 相關 | **參考** | 保持分離，作為補充參考 |
| `patterns.md` | - | **新增** | `sources/ecc/rules/` |

### Contexts 評估（工作情境配置）

| ecc Context | 決策 | 目標位置 |
|-------------|------|----------|
| `dev.md` | **新增** | `sources/ecc/contexts/` - Implementation-first |
| `research.md` | **新增** | `sources/ecc/contexts/` - Exploration-based |
| `review.md` | **新增** | `sources/ecc/contexts/` - 系統化審查 |

### Scripts/Lib 評估（工具函式庫）

| ecc Script | 決策 | 目標位置 |
|------------|------|----------|
| `setup-package-manager.js` | **新增 (Python)** | `sources/ecc/scripts/` - 需重寫為 Python |
| `lib/package-manager.js` | **新增 (Python)** | `sources/ecc/scripts/lib/` - 需重寫為 Python |
| `lib/utils.js` | **參考** | 通用工具函式參考 |

### Tests 評估（測試框架）

| ecc Test | 決策 | 目標位置 |
|----------|------|----------|
| `run-all.js` | **參考** | 測試執行器架構參考 |
| `tests/hooks/` | **新增** | `sources/ecc/tests/hooks/` |
| `tests/lib/` | **新增** | `sources/ecc/tests/lib/` |

### Examples 評估（範例配置）

| ecc Example | 決策 | 目標位置 |
|-------------|------|----------|
| `CLAUDE.md` | **新增** | `sources/ecc/examples/` - 專案級配置範例 |
| `user-CLAUDE.md` | **新增** | `sources/ecc/examples/` - 使用者級配置範例 |
| `statusline.json` | **新增** | `sources/ecc/examples/` - 狀態列配置範例 |

### MCP Configs 評估

| ecc MCP Server | 決策 | 目標位置 |
|----------------|------|----------|
| `mcp-servers.json` | **新增** | `sources/ecc/mcp-configs/` - 完整配置參考 |
| 專案特定服務 | **不採用** | firecrawl, supabase, vercel 等為專案特定 |

### Plugin System 評估

| ecc Plugin 元件 | 決策 | 目標位置 |
|-----------------|------|----------|
| `plugin.json` | **新增** | `sources/ecc/.claude-plugin/` - Plugin 格式參考 |
| `marketplace.json` | **不採用** | 市集發布不在範圍 |

## 整合摘要

### 目標目錄結構

```
sources/
└── ecc/                         # everything-claude-code
    ├── agents/                  # 6 個 agents
    ├── commands/                # 10 個 commands
    ├── skills/                  # 7 個 skills
    ├── hooks/                   # Python hooks + 配置
    ├── contexts/                # 3 個工作情境
    ├── rules/                   # 5 個規則檔
    ├── scripts/                 # Python 工具腳本
    │   └── lib/
    ├── tests/                   # 測試框架
    ├── examples/                # 配置範例
    ├── mcp-configs/             # MCP 服務配置
    └── .claude-plugin/          # Plugin 格式參考
```

### 新增項目（保持 Claude Code 原生格式）

| 類型 | 數量 | 目標位置 |
|------|------|----------|
| Agents | 6 | `sources/ecc/agents/` |
| Commands | 10 | `sources/ecc/commands/` |
| Skills | 7 | `sources/ecc/skills/` |
| Hooks | 3+ | `sources/ecc/hooks/` (Python) |
| Contexts | 3 | `sources/ecc/contexts/` |
| Rules | 5 | `sources/ecc/rules/` |
| Scripts | 2 | `sources/ecc/scripts/` (Python) |
| Examples | 3 | `sources/ecc/examples/` |
| MCP Configs | 1 | `sources/ecc/mcp-configs/` |
| Plugin | 1 | `sources/ecc/.claude-plugin/` |

### 參考項目（UDS 可借鑒但保持分離）

| ecc 資源 | UDS 對應 | 說明 |
|----------|----------|------|
| `architect.md` | `code-architect.md` | 補充 UDS agent |
| `code-reviewer.md` | `reviewer.md` | 補充 UDS agent |
| `tdd.md` | `tdd.md` | 補充 UDS command |
| `coding-standards/` | `.standards/` | 補充 UDS 標準 |

### 不採用項目

| 類型 | 數量 | 說明 |
|------|------|------|
| Skills | 2 | clickhouse-io、project-guidelines-example（專案特定） |
| Commands | 2 | update-codemaps、update-docs（與 UDS 重疊） |
| MCP Configs | 多個 | 專案特定服務配置 |

## 架構調整：ai-dev 指令重構

### 1. ai-dev project init 改變

| 項目 | 之前 | 之後 |
|------|------|------|
| 行為 | 調用 UDS + OpenSpec 初始化 | 複製 custom-skills 的 project 模板到目標專案 |
| 依賴 | 需要 UDS CLI | 直接使用 custom-skills 內容 |

**新流程：**
```
ai-dev project init
    └── 複製 project-template/ → 目標專案/
```

### 2. ai-dev update 改變

| 模式 | 行為 |
|------|------|
| **預設 `ai-dev update`** | 只檢查軟體更新 + 拉取 custom-skills + 使用 custom-skills 內容 |
| **`ai-dev update --sync-upstream`** | 拉取所有第三方 repo → 檢查更新 → 比較差異 → 合併審核 |

**預設更新流程：**
```
ai-dev update
    ├── 1. 檢查 ai-dev CLI 版本更新
    ├── 2. git pull custom-skills
    └── 3. 複製 custom-skills 內容到各工具目錄
```

**上游同步流程（--sync-upstream）：**
```
ai-dev update --sync-upstream
    ├── 1. 拉取所有第三方 repo（UDS, obsidian-skills, anthropic-skills, superpowers, ecc）
    ├── 2. 檢查每個 repo 是否有新 commits
    ├── 3. 比較 upstream 與 custom-skills 的差異
    ├── 4. 產生差異報告
    └── 5. 透過 OpenSpec 建立變更提案供審核
```

### 3. 角色定義

| 層級 | 角色 | 說明 |
|------|------|------|
| **custom-skills** | 審核後穩定版 | 使用者直接使用的內容 |
| **第三方 repo** | 上游來源 | UDS, obsidian-skills, anthropic-skills, superpowers, ecc |
| **upstream/** | 追蹤資料 | 記錄上游版本、對照表 |

---

## 上游追蹤機制

### 設計

建立 `upstream/` 目錄追蹤上游專案變更：

```
upstream/
├── sources.yaml          # 上游來源註冊表（所有第三方 repo）
├── ecc/                   # everything-claude-code
│   ├── last-sync.yaml    # 最後同步資訊
│   └── mapping.yaml      # 檔案對照表
├── uds/                   # universal-dev-standards
│   ├── last-sync.yaml
│   └── mapping.yaml
├── obsidian-skills/
│   ├── last-sync.yaml
│   └── mapping.yaml
├── anthropic-skills/
│   ├── last-sync.yaml
│   └── mapping.yaml
├── superpowers/
│   ├── last-sync.yaml
│   └── mapping.yaml
└── README.md
```

### sources.yaml 格式

```yaml
sources:
  everything-claude-code:
    repo: affaan-m/everything-claude-code
    branch: main
    local_path: ~/.config/everything-claude-code/
    last_synced_commit: <commit-hash>
    last_synced_date: 2026-01-24
    tracked_paths:
      - agents/
      - commands/
      - skills/
      - hooks/
      - contexts/
      - rules/
    target_dir: sources/ecc/

  universal-dev-standards:
    repo: AsiaOstrich/universal-dev-standards
    branch: main
    local_path: ~/.config/universal-dev-standards/
    last_synced_commit: <commit-hash>
    last_synced_date: 2026-01-24
    tracked_paths:
      - skills/claude-code/
    target_dir: skills/  # UDS 使用專屬格式

  obsidian-skills:
    repo: kepano/obsidian-skills
    branch: main
    local_path: ~/.config/obsidian-skills/
    last_synced_commit: <commit-hash>
    last_synced_date: 2026-01-24
    tracked_paths:
      - skills/
    target_dir: skills/

  anthropic-skills:
    repo: anthropics/skills
    branch: main
    local_path: ~/.config/anthropic-skills/
    last_synced_commit: <commit-hash>
    last_synced_date: 2026-01-24
    tracked_paths:
      - skills/skill-creator/
    target_dir: skills/skill-creator/

  superpowers:
    repo: obra/superpowers
    branch: main
    local_path: ~/.config/superpowers/
    last_synced_commit: <commit-hash>
    last_synced_date: 2026-01-24
    tracked_paths:
      - skills/
    target_dir: skills/
```

### 檔案對照表 (ecc/mapping.yaml)

```yaml
# ecc 檔案 → custom-skills 檔案的對照
agents:
  build-error-resolver.md: sources/ecc/agents/build-error-resolver.md
  e2e-runner.md: sources/ecc/agents/e2e-runner.md
  planner.md: sources/ecc/agents/planner.md
  # ...

commands:
  build-fix.md: sources/ecc/commands/build-fix.md
  e2e.md: sources/ecc/commands/e2e.md
  # ...

# 參考對照（不直接複製，僅供 UDS 參考）
references:
  agents/architect.md: skills/agents/code-architect.md
  agents/code-reviewer.md: skills/agents/reviewer.md
```

### --sync-upstream 流程

```
ai-dev update --sync-upstream
    │
    ├─► 1. 拉取所有第三方 repo
    │       git pull ~/.config/everything-claude-code/
    │       git pull ~/.config/universal-dev-standards/
    │       git pull ~/.config/obsidian-skills/
    │       ...
    │
    ├─► 2. 檢查版本差異
    │       foreach repo in sources.yaml:
    │           current_commit = git rev-parse HEAD
    │           if current_commit != last_synced_commit:
    │               mark as "有更新"
    │
    ├─► 3. 產生差異報告
    │       diff 上游檔案 vs custom-skills 對應檔案
    │       輸出 upstream/diff-report.md
    │
    ├─► 4. 建立 OpenSpec 變更提案
    │       openspec proposal upstream-sync-YYYY-MM-DD
    │       包含：新增/修改/刪除的檔案清單
    │
    └─► 5. 等待人工審核
            openspec apply upstream-sync-YYYY-MM-DD
```

## Impact

### 受影響的檔案

**新增（ecc 資源，保持 Claude Code 原生格式）：**
- `sources/ecc/agents/`: 6 個 agents
- `sources/ecc/commands/`: 10 個 commands
- `sources/ecc/skills/`: 7 個 skills
- `sources/ecc/hooks/`: Python hooks + 配置
- `sources/ecc/contexts/`: 3 個工作情境
- `sources/ecc/rules/`: 5 個規則檔
- `sources/ecc/scripts/`: Python 工具腳本
- `sources/ecc/examples/`: 配置範例
- `sources/ecc/mcp-configs/`: MCP 配置
- `sources/ecc/.claude-plugin/`: Plugin 格式

**新增（上游追蹤系統）：**
- `upstream/sources.yaml`: 所有第三方 repo 註冊
- `upstream/ecc/mapping.yaml`: ecc 檔案對照
- `upstream/uds/mapping.yaml`: UDS 檔案對照
- `upstream/*/last-sync.yaml`: 各 repo 同步狀態

**使用現有（project 模板）：**
- `project-template/`: ai-dev project init 使用的模板（已重新命名）

**新增（upstream-sync skill + command）：**
- `skills/upstream-sync/`: 上游同步 skill
- `commands/claude/upstream-sync.md`: 上游同步 command

**修改（CLI 指令）：**
- `script/commands/install.py`: 移除 UDS/OpenSpec 初始化依賴
- `script/commands/update.py`: 新增 `--sync-upstream` 選項
- `script/utils/shared.py`: 新增 ecc 到 REPOS，調整複製邏輯

**不修改（UDS 資源保持獨立）：**
- `skills/agents/` - UDS 格式 agents 保持不變
- `commands/claude/` - UDS 格式 commands 保持不變
- `.standards/` - UDS 標準保持不變

### 風險評估

| 風險 | 等級 | 緩解措施 |
|------|------|----------|
| UDS/ecc 格式混淆 | 低 | 分離目錄結構，`sources/ecc/` 獨立 |
| Hooks 跨平台 | 中 | Node.js hooks 重寫為 Python |
| 上游更新衝突 | 低 | 保持原生格式，降低合併複雜度 |

## 授權

來源專案採用 MIT License，與本專案相容。

整合時需在檔案頭部標注來源：

```markdown
<!--
Upstream: everything-claude-code
Source: https://github.com/affaan-m/everything-claude-code/blob/main/agents/xxx.md
Synced: 2026-01-24
Commit: <hash>
License: MIT
-->
```
