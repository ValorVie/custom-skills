# 複製架構文檔

> **版本**: 1.0.0
> **更新日期**: 2026-01-24

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
| **Codex** | skills | `~/.codex/skills/` |
| **Gemini CLI** | skills | `~/.gemini/skills/` |
| | commands | `~/.gemini/commands/` |

---

## 外部來源 Git Repositories

| 名稱 | Repository URL | 本地路徑 |
|------|----------------|----------|
| custom-skills | https://github.com/ValorVie/custom-skills.git | `~/.config/custom-skills/` |
| superpowers | https://github.com/obra/superpowers.git | `~/.config/superpowers/` |
| universal-dev-standards | https://github.com/AsiaOstrich/universal-dev-standards.git | `~/.config/universal-dev-standards/` |
| obsidian-skills | https://github.com/kepano/obsidian-skills.git | `~/.config/obsidian-skills/` |
| anthropic-skills | https://github.com/anthropics/skills.git | `~/.config/anthropic-skills/` |

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
| **UDS workflows** | `~/.config/universal-dev-standards/skills/claude-code/workflows/` | `~/.config/custom-skills/command/workflows/` |
| **UDS commands** | `~/.config/universal-dev-standards/skills/claude-code/commands/` | `~/.config/custom-skills/command/claude/` |
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
| | Codex | `~/.codex/skills/` |
| | Gemini CLI | `~/.gemini/skills/` |
| `custom-skills/command/claude/` | Claude Code | `~/.claude/commands/` |
| `custom-skills/command/antigravity/` | Antigravity | `~/.gemini/antigravity/global_workflows/` |
| `custom-skills/command/opencode/` | OpenCode | `~/.config/opencode/commands/` |
| `custom-skills/command/gemini/` | Gemini CLI | `~/.gemini/commands/` |
| `custom-skills/command/workflows/` | Claude Code | `~/.claude/workflows/` |
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
├── command/                   # 工具專屬 commands
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
│  ├── skills/        ←── UDS skills + Obsidian + Anthropic       │
│  ├── command/                                                   │
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
│  Codex          ──→  ~/.codex/skills/                           │
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

## 版本歷史

| 版本 | 日期 | 變更 |
|------|------|------|
| 1.0.0 | 2026-01-24 | 初版，新增 Claude agents 和 workflows 支援 |
