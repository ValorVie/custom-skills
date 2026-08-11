# 複製架構文檔

> **版本**: 2.2.0
> **更新日期**: 2026-08-11

---

## 概述

本專案透過三階段複製流程，將各來源的 skills、commands、agents、workflows 整合並分發到不同 AI 工具的配置目錄。
---

## 支援的 AI 工具與目標目錄

| 工具 | 資源類型 | 目標目錄 |
|------|----------|----------|
| **Claude Code** | skills | `~/.claude/skills/` |
| | commands | `~/.claude/commands/` |
| | agents | `~/.claude/agents/` |
| | workflows | `~/.claude/workflows/` |
| **Antigravity** | skills | `~/.gemini/antigravity/global_skills/` |
| | workflows | `~/.gemini/antigravity/global_workflows/` |
| **OpenCode** | skills | `~/.config/opencode/skills/` |
| | commands | `~/.config/opencode/commands/` |
| | agents | `~/.config/opencode/agents/` |
| **Codex** | skills | `~/.agents/skills/` |
| **Gemini CLI** | skills | `~/.gemini/skills/` |
| | commands | `~/.gemini/commands/` |

Codex 與其他支援 Agent Skills 標準的工具共用 `~/.agents/skills`。只有 Skills
共用；Codex 的設定、agents、hooks、prompts、認證與 sessions 仍在 `.codex`。
install、update、clone 會先備份並遷移舊版 `~/.codex/skills`；內容衝突時保留
兩份、寫入 audit 並在其他 phase 前停止，不會覆蓋。

---

## 外部來源 Git Repositories

| 名稱 | Repository URL | 本地路徑 |
|------|----------------|----------|
| custom-skills | https://github.com/ValorVie/custom-skills.git | `~/.config/custom-skills/` |
| superpowers | https://github.com/obra/superpowers.git | `~/.config/superpowers/` |
| universal-dev-standards | https://github.com/AsiaOstrich/universal-dev-standards.git | `~/.config/universal-dev-standards/` |
| obsidian-skills | https://github.com/kepano/obsidian-skills.git | `~/.config/obsidian-skills/` |
| anthropic-skills | https://github.com/anthropics/skills.git | `~/.config/anthropic-skills/` |
| everything-claude-code | https://github.com/affaan-m/everything-claude-code.git | `~/.config/everything-claude-code/` |

### 上游追蹤系統

所有第三方 repo 的同步狀態記錄在 `upstream/` 目錄：

```
upstream/
├── sources.yaml          # 上游來源註冊表
├── ecc/                   # everything-claude-code
│   ├── last-sync.yaml    # 最後同步資訊
│   └── mapping.yaml      # 檔案對照表
├── uds/                   # universal-dev-standards
├── obsidian-skills/
├── anthropic-skills/
└── superpowers/
```

使用 `/custom-skills-upstream-ops` skill 進行上游同步分析與審核（預設 audit mode）。

---

## 三階段複製流程

### Stage 1: Clone 外部套件
由 `install` 或 `update` 指令執行，將外部 Git repositories clone 到本地。

### Stage 2: 整合到 custom-skills
將各來源整合到 `~/.config/custom-skills/` 作為統一的中繼站。

#### 來源對應表

| 來源 | 來源路徑 | 目標路徑 |
|------|----------|----------|
| **UDS skills** | `~/.config/universal-dev-standards/skills/claude-code/*` | `~/.config/custom-skills/skills/` |
| **UDS agents** | `~/.config/universal-dev-standards/skills/claude-code/agents/` | `~/.config/custom-skills/agents/claude/` 和 `~/.config/custom-skills/agents/opencode/` |
| **UDS workflows** | `~/.config/universal-dev-standards/skills/claude-code/workflows/` | `~/.config/custom-skills/commands/workflows/` |
| **UDS commands** | `~/.config/universal-dev-standards/skills/claude-code/commands/` | `~/.config/custom-skills/commands/claude/` |
| **Obsidian skills** | `~/.config/obsidian-skills/skills/` | `~/.config/custom-skills/skills/` |
| **Anthropic skill-creator** | `~/.config/anthropic-skills/skills/skill-creator/` | `~/.config/custom-skills/skills/skill-creator/` |

### Stage 3: 分發到各工具目錄
將 `~/.config/custom-skills/` 的內容分發到各 AI 工具的配置目錄。

#### 分發對應表

| 來源路徑 | 目標工具 | 目標路徑 |
|----------|----------|----------|
| `custom-skills/skills/` | Claude Code | `~/.claude/skills/` |
| | Antigravity | `~/.gemini/antigravity/global_skills/` |
| | OpenCode | `~/.config/opencode/skills/` |
| | Codex | `~/.agents/skills/` |
| | Gemini CLI | `~/.gemini/skills/` |
| `custom-skills/commands/claude/` | Claude Code | `~/.claude/commands/` |
| `custom-skills/commands/antigravity/` | Antigravity | `~/.gemini/antigravity/global_workflows/` |
| `custom-skills/commands/opencode/` | OpenCode | `~/.config/opencode/commands/` |
| `custom-skills/commands/gemini/` | Gemini CLI | `~/.gemini/commands/` |
| `custom-skills/commands/workflows/` | Claude Code | `~/.claude/workflows/` |
| `custom-skills/agents/claude/` | Claude Code | `~/.claude/agents/` |
| `custom-skills/agents/opencode/` | OpenCode | `~/.config/opencode/agents/` |

---

## Git Repo 目錄結構

```
custom-skills/
├── skills/                    # 共用 skills（所有工具共用）
│   ├── ai-collaboration-standards/
│   ├── changelog-guide/
│   ├── skill-creator/
│   └── ...
├── commands/                  # 工具專屬 commands
│   ├── claude/               # Claude Code commands
│   ├── antigravity/          # Antigravity workflows
│   ├── opencode/             # OpenCode commands
│   ├── gemini/               # Gemini CLI commands
│   └── workflows/            # Claude Code workflows
├── agents/                    # 工具專屬 agents
│   ├── claude/               # Claude Code agents（來自 UDS）
│   │   ├── code-architect.md
│   │   ├── doc-writer.md
│   │   ├── reviewer.md
│   │   ├── spec-analyst.md
│   │   └── test-specialist.md
│   └── opencode/             # OpenCode agents（來自 UDS + 自訂）
│       ├── code-architect.md      # 來自 UDS
│       ├── doc-writer.md          # 來自 UDS
│       ├── reviewer.md            # 來自 UDS
│       ├── spec-analyst.md        # 來自 UDS
│       ├── test-specialist.md     # 來自 UDS
│       └── code-simplifier-opencode.md  # 自訂
└── script/                    # CLI 腳本
    ├── commands/
    │   ├── install.py
    │   ├── update.py
    │   └── ...
    └── utils/
        ├── paths.py
        └── shared.py
```

---

## 複製邏輯流程圖

```
┌─────────────────────────────────────────────────────────────────┐
│                        Stage 1: Clone                           │
├─────────────────────────────────────────────────────────────────┤
│  GitHub Repos                                                   │
│  ├── universal-dev-standards  ──→  ~/.config/universal-dev-standards/
│  ├── obsidian-skills          ──→  ~/.config/obsidian-skills/   │
│  ├── anthropic-skills         ──→  ~/.config/anthropic-skills/  │
│  └── superpowers              ──→  ~/.config/superpowers/       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                  Stage 2: 整合到 custom-skills                  │
├─────────────────────────────────────────────────────────────────┤
│  ~/.config/custom-skills/                                       │
│  ├── skills/        ←── UDS + Obsidian + Anthropic               │
│  ├── commands/                                                  │
│  │   ├── claude/    ←── UDS commands                            │
│  │   └── workflows/ ←── UDS workflows                           │
│  └── agents/                                                    │
│      ├── claude/    ←── UDS agents                              │
│      └── opencode/  ←── UDS agents                              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    Stage 3: 分發到各工具                        │
├─────────────────────────────────────────────────────────────────┤
│  Claude Code    ──→  ~/.claude/{skills,commands,agents,workflows}
│  Antigravity    ──→  ~/.gemini/antigravity/{global_skills,global_workflows}
│  OpenCode       ──→  ~/.config/opencode/{skills,commands,agents}│
│  Codex          ──→  ~/.agents/skills/                           │
│  Gemini CLI     ──→  ~/.gemini/{skills,commands}                │
└─────────────────────────────────────────────────────────────────┘
```

---

## 相關檔案

| 檔案 | 說明 |
|------|------|
| `script/utils/paths.py` | 定義所有路徑取得函式 |
| `script/utils/shared.py` | 複製邏輯、來源配置、目標配置 |
| `script/commands/install.py` | 首次安裝流程 |
| `script/commands/update.py` | 更新流程 |

---

## ecc (everything-claude-code) 整合

ecc 資源放在 `sources/ecc/` 目錄，保持 Claude Code 原生格式：

```
sources/ecc/
├── agents/         # 6 個 agents
├── commands/       # 10 個 commands
├── skills/         # 7 個 skills
├── hooks/          # Python hooks
├── contexts/       # 3 個工作情境
├── rules/          # 5 個規則檔
├── scripts/lib/    # Python 工具腳本
├── examples/       # 配置範例
├── mcp-configs/    # MCP 配置
└── .claude-plugin/ # Plugin 格式
```

### 格式說明

| 系統 | 格式 | 目錄 |
|------|------|------|
| **UDS** | YAML frontmatter + Markdown | `.standards/`, `skills/agents/` |
| **ecc** | 純 Markdown（無 frontmatter） | `sources/ecc/` |

ecc 資源不轉換為 UDS 格式，保持原始狀態以便於上游同步。

---

## 版本歷史

| 版本 | 日期 | 變更 |
|------|------|------|
| 2.2.0 | 2026-08-11 | 退役 auto-skill；歷史內容移至 `archive/auto-skill/` |
| 2.1.0 | 2026-02-12 | 新增 auto-skill 上游來源（已退役） |
| 2.0.0 | 2026-01-24 | 新增 ecc 整合、上游追蹤系統 |
| 1.0.0 | 2026-01-24 | 初版，新增 Claude agents 和 workflows 支援 |
