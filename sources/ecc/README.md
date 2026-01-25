# Everything Claude Code (ECC) 資源

來源: [affaan-m/everything-claude-code](https://github.com/affaan-m/everything-claude-code)
整合日期: 2026-01-24
授權: MIT

## 概述

本目錄包含從 Everything Claude Code 專案整合的資源，經過調整以適應 custom-skills 的架構，並重寫 hooks 為 Python 以確保跨平台相容性。

## 目錄結構

```
sources/ecc/
├── hooks/               # Python hooks（原 Node.js 重寫）
│   ├── utils.py        # 共用工具函式
│   ├── hooks.json      # Hook 配置
│   ├── memory-persistence/
│   │   ├── session-start.py
│   │   ├── session-end.py
│   │   ├── pre-compact.py
│   │   └── evaluate-session.py
│   └── strategic-compact/
│       └── suggest-compact.py
├── skills/              # Claude Code Skills
│   ├── continuous-learning/
│   ├── strategic-compact/
│   ├── eval-harness/
│   ├── security-review/
│   └── tdd-workflow/
├── agents/              # Specialized Agents
│   ├── build-error-resolver.md
│   ├── e2e-runner.md
│   ├── doc-updater.md
│   └── security-reviewer.md
├── commands/            # Slash Commands
│   ├── checkpoint.md
│   ├── build-fix.md
│   ├── e2e.md
│   ├── learn.md
│   ├── test-coverage.md
│   └── eval.md
├── plugins/             # Plugin 安裝指南
│   └── README.md
└── mcp-configs/         # MCP 伺服器配置
    ├── mcp-servers.json
    └── README.md
```

## Hooks 系統

### 安裝方式

1. 將 `hooks/` 目錄複製到 `~/.claude/plugins/ecc-hooks/`
2. 在 `~/.claude.json` 中加入以下配置：

```json
{
  "hooks": {
    "includes": ["~/.claude/plugins/ecc-hooks/hooks.json"]
  }
}
```

### 可用 Hooks

| Hook | 觸發時機 | 功能 |
|------|---------|------|
| `session-start` | SessionStart | 載入上次會話狀態，偵測 package manager |
| `session-end` | SessionEnd, Stop | 保存會話狀態 |
| `pre-compact` | PreCompact | 壓縮前保存關鍵資訊 |
| `evaluate-session` | SessionEnd | 評估並萃取可重用模式 |
| `suggest-compact` | PostToolUse | 追蹤工具呼叫次數，建議壓縮時機 |

### 環境變數

| 變數 | 說明 | 預設值 |
|------|------|--------|
| `CLAUDE_PLUGIN_ROOT` | Hook 根目錄 | 自動偵測 |
| `COMPACT_THRESHOLD` | 建議壓縮的工具呼叫閾值 | 50 |
| `CLAUDE_PACKAGE_MANAGER` | 強制指定 package manager | 自動偵測 |

## Skills

| Skill | 說明 |
|-------|------|
| `continuous-learning` | 從會話中萃取可重用模式 |
| `strategic-compact` | 手動壓縮指南 |
| `eval-harness` | Eval-driven development 框架 |
| `security-review` | OWASP Top 10 安全審查 |
| `tdd-workflow` | TDD 工作流程（Jest/Vitest/Playwright） |

## Agents

| Agent | 用途 |
|-------|------|
| `build-error-resolver` | TypeScript 建置錯誤修復專家 |
| `e2e-runner` | Playwright E2E 測試執行器 |
| `doc-updater` | 文件與 Codemap 產生器 |
| `security-reviewer` | OWASP 漏洞掃描器 |

## Commands

| Command | 說明 |
|---------|------|
| `/checkpoint` | 建立 Git 檢查點（stash + tag） |
| `/build-fix` | 迭代修復建置錯誤 |
| `/e2e` | 產生並執行 E2E 測試 |
| `/learn` | 從會話萃取模式 |
| `/test-coverage` | 分析測試覆蓋率 |
| `/eval` | Eval-driven development 工作流程 |

## MCP 配置

`mcp-configs/mcp-servers.json` 包含常用 MCP 伺服器的配置範例：

- GitHub, Supabase, Vercel, Railway
- Cloudflare Workers, ClickHouse
- Context7, Firecrawl, Memory

詳見 `mcp-configs/README.md`。

## 與 UDS 標準的整合

ECC 資源與 Universal Dev Standards (UDS) 互補：

- **UDS**: 提供標準化的開發規範和流程
- **ECC**: 提供實作工具和自動化 hooks

切換標準體系：
```bash
# 查看目前狀態
python script/commands/standards.py status

# 切換到 ECC profile
python script/commands/standards.py switch ecc

# 查看 profile 內容
python script/commands/standards.py show ecc
```

## 上游同步

同步狀態記錄於 `upstream/ecc/last-sync.yaml`。

檔案對照表位於 `upstream/ecc/mapping.yaml`。

## 注意事項

1. **所有 hooks 已重寫為 Python** - 原始 Node.js 版本不包含在內
2. **僅使用 Python 標準庫** - 無需額外安裝套件
3. **跨平台支援** - Windows, macOS, Linux
4. **每個檔案包含 upstream 標頭** - 記錄來源和同步日期
