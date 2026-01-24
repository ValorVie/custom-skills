# Design: ECC Hooks 與 MCP 配置整合設計

## Context

### 現有架構（來源）

```
sources/ecc/hooks/
├── hooks.json                    # Hook 配置
├── utils.py                      # 共用工具
├── README.md
├── memory-persistence/
│   ├── session-start.py
│   ├── session-end.py
│   ├── pre-compact.py
│   └── evaluate-session.py
└── strategic-compact/
    └── suggest-compact.py
```

### 目標結構（符合官方 Plugin 規範）

```
~/.claude/plugins/ecc-hooks/
├── .claude-plugin/
│   └── plugin.json              # 必要：Plugin manifest
├── hooks/
│   └── hooks.json               # Hook 配置（移至 hooks/ 子目錄）
├── scripts/                     # 腳本目錄（官方建議位置）
│   ├── utils.py
│   ├── memory-persistence/
│   │   ├── session-start.py
│   │   ├── session-end.py
│   │   ├── pre-compact.py
│   │   └── evaluate-session.py
│   └── strategic-compact/
│       └── suggest-compact.py
└── README.md
```

### Claude Code Plugin 官方規範

根據 [Claude Code 文件](https://github.com/anthropics/claude-code)：

```
plugin-name/
├── .claude-plugin/
│   └── plugin.json          # Required: Plugin manifest
├── hooks/
│   └── hooks.json           # Event handler configuration
├── scripts/                 # Helper scripts and utilities
├── commands/                # Slash commands (.md files)
├── agents/                  # Subagent definitions (.md files)
├── skills/                  # Agent skills (subdirectories)
└── .mcp.json               # MCP server definitions (optional)
```

## Goals / Non-Goals

### Goals

1. **符合官方規範**：建構標準 Claude Code plugin 結構
2. 自動化 hooks 分發到正確位置
3. 提供 MCP 配置範本的存取路徑
4. 在 TUI 中提供可視化管理
5. 保持非破壞性更新原則

### Non-Goals

1. 自動合併使用者的 hooks 配置
2. 自動覆蓋使用者的 MCP 配置
3. 管理 MCP 伺服器的啟停

## Decisions

### Decision 1: 來源結構重構

**選擇**：在 `sources/ecc/hooks/` 建立符合官方規範的結構

**變更內容**：

1. 新增 `.claude-plugin/plugin.json`
2. 將 `hooks.json` 移至 `hooks/hooks.json`
3. 將腳本移至 `scripts/` 目錄
4. 更新 `hooks.json` 中的路徑

**新增檔案 - plugin.json**：
```json
{
  "name": "ecc-hooks",
  "version": "1.0.0",
  "description": "Everything Claude Code - Memory Persistence & Strategic Compact Hooks",
  "author": "custom-skills",
  "hooks": "./hooks/hooks.json"
}
```

**調整後的來源結構**：
```
sources/ecc/hooks/
├── .claude-plugin/
│   └── plugin.json              # 新增
├── hooks/
│   └── hooks.json               # 從根目錄移入
├── scripts/                     # 新增目錄
│   ├── utils.py                 # 從根目錄移入
│   ├── memory-persistence/      # 保持結構
│   │   ├── session-start.py
│   │   ├── session-end.py
│   │   ├── pre-compact.py
│   │   └── evaluate-session.py
│   └── strategic-compact/       # 保持結構
│       └── suggest-compact.py
└── README.md
```

### Decision 2: hooks.json 路徑更新

**選擇**：使用 `${CLAUDE_PLUGIN_ROOT}/scripts/...` 路徑格式

**變更前**：
```json
"command": "python \"${CLAUDE_PLUGIN_ROOT}/sources/ecc/hooks/memory-persistence/session-start.py\""
```

**變更後**：
```json
"command": "python \"${CLAUDE_PLUGIN_ROOT}/scripts/memory-persistence/session-start.py\""
```

**完整 hooks.json 範例**：
```json
{
  "hooks": {
    "SessionStart": [{
      "matcher": "*",
      "hooks": [{
        "type": "command",
        "command": "python \"${CLAUDE_PLUGIN_ROOT}/scripts/memory-persistence/session-start.py\""
      }],
      "description": "Load previous context and detect package manager on new session"
    }],
    "SessionEnd": [{
      "matcher": "*",
      "hooks": [{
        "type": "command",
        "command": "python \"${CLAUDE_PLUGIN_ROOT}/scripts/memory-persistence/session-end.py\""
      }],
      "description": "Persist session state on end"
    }],
    "PreCompact": [{
      "matcher": "*",
      "hooks": [{
        "type": "command",
        "command": "python \"${CLAUDE_PLUGIN_ROOT}/scripts/memory-persistence/pre-compact.py\""
      }],
      "description": "Save state before context compaction"
    }],
    "PreToolUse": [{
      "matcher": "tool == \"Edit\" || tool == \"Write\"",
      "hooks": [{
        "type": "command",
        "command": "python \"${CLAUDE_PLUGIN_ROOT}/scripts/strategic-compact/suggest-compact.py\""
      }],
      "description": "Suggest manual compaction at logical intervals"
    }]
  }
}
```

### Decision 3: 分發策略

**選擇**：直接複製整個重構後的目錄到 `~/.claude/plugins/ecc-hooks/`

**理由**：
- 來源結構已符合官方規範，無需在分發時轉換
- 簡化分發邏輯
- 便於維護和除錯

**實作方式**：
```python
def distribute_ecc_hooks():
    source = CUSTOM_SKILLS_DIR / "sources/ecc/hooks"
    target = Path.home() / ".claude/plugins/ecc-hooks"

    # 確保目標目錄存在
    target.mkdir(parents=True, exist_ok=True)

    # 複製整個 plugin 結構
    shutil.copytree(source, target, dirs_exist_ok=True)

    print(f"✓ ECC Hooks plugin 已安裝至 {target}")
    print("  Plugin 會自動被 Claude Code 載入")
```

### Decision 4: MCP 配置策略

**選擇**：範本 + 手動合併（不自動分發）

**理由**：
- MCP 配置包含敏感資訊（API keys, tokens）
- 每個使用者的 MCP 需求不同
- 自動合併可能導致配置衝突

### Decision 5: TUI 整合設計

**UI 設計**：
```
┌─ Skill Manager ──────────────────────────────────────────┐
│ Target: [Claude Code ▼]                                  │
│                                                          │
│ ─── Resources ───────────────────────────────────────────│
│ [✓] commit-standards    [✓] ai-collaboration-standards   │
│ ...                                                      │
│                                                          │
│ ─── ECC Hooks Plugin ────────────────────────────────────│
│ Status: ● Installed (v1.0.0)                             │
│ Location: ~/.claude/plugins/ecc-hooks/                   │
│ [I] Install/Update  [U] Uninstall  [V] View Config       │
│                                                          │
│ ─── MCP Config ──────────────────────────────────────────│
│ Template: ~/.config/custom-skills/sources/ecc/mcp-configs│
│ Target:   ~/.claude.json                                 │
│ [E] Edit Target  [T] View Template                       │
└──────────────────────────────────────────────────────────┘
```

## Risks / Trade-offs

### Risk 1: 來源結構變更的向後相容

- **風險**：重構來源結構可能影響現有使用者
- **緩解**：
  1. 在 CHANGELOG 中記錄 breaking change
  2. 提供遷移指引
  3. 舊結構的安裝會被新結構覆蓋

### Risk 2: Plugin 自動載入

- **風險**：Claude Code 可能不會自動發現 `~/.claude/plugins/` 中的 plugin
- **緩解**：
  1. 確認 Claude Code 的 plugin 搜尋路徑
  2. 如需手動啟用，在安裝後輸出指引

### Risk 3: 版本同步問題

- **風險**：`sources/ecc/hooks` 更新後，已分發的版本未更新
- **緩解**：
  1. 在 plugin.json 中維護版本號
  2. TUI 顯示版本比對
  3. `ai-dev update` 時檢查版本差異

## Migration Plan

### Phase 0: 來源結構重構（前置作業）

1. 建立 `.claude-plugin/plugin.json`
2. 建立 `hooks/` 子目錄並移動 `hooks.json`
3. 建立 `scripts/` 目錄並移動所有 Python 腳本
4. 更新 `hooks.json` 中的路徑
5. 更新 `README.md` 說明新結構

### Phase 1: 基礎分發（此提案範圍）

1. 新增 hooks plugin 分發到 Stage 3
2. 更新 TUI 顯示 hooks 狀態
3. 提供安裝/更新 CLI

### Phase 2: 進階整合（未來）

1. 自動偵測 hooks 版本
2. 提供 diff 比對功能
3. 支援選擇性 hooks 啟用

### Phase 3: Hooks 選用/開關機制（未來計畫）

提供細粒度的 hooks 控制，讓使用者可以：

1. **個別 Hook 開關**
   - 在 TUI 中顯示所有可用 hooks 列表
   - 允許使用者啟用/停用個別 hook（如只啟用 memory-persistence，停用 strategic-compact）
   - 產生客製化的 `hooks.json` 只包含啟用的 hooks

2. **Hook 事件類型篩選**
   - 按事件類型（SessionStart, SessionEnd, PreToolUse 等）分組顯示
   - 允許停用整類事件的所有 hooks

3. **配置持久化**
   - 將使用者的 hooks 偏好儲存至 `~/.claude/plugins/ecc-hooks/.user-config.json`
   - 更新時保留使用者的開關設定

4. **CLI 支援**
   - `ai-dev hooks enable <hook-name>` 啟用特定 hook
   - `ai-dev hooks disable <hook-name>` 停用特定 hook
   - `ai-dev hooks list` 列出所有 hooks 及其啟用狀態

## Open Questions

1. **Q**: Claude Code 是否自動載入 `~/.claude/plugins/` 中的 plugin？
   - **待確認**：需測試驗證

2. **Q**: 是否需要支援 hooks 的選擇性安裝（只安裝部分 hooks）？
   - **建議**：第一版先實作全量安裝，後續根據使用者反饋決定

3. **Q**: MCP 範本是否需要提供互動式合併工具？
   - **建議**：暫不實作，因 MCP 配置高度個人化，手動合併更安全
