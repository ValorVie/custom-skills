# Design: 重構 install/update 流程

## Context

本專案管理 AI 輔助開發工具的 skills、commands 和 agents。需要將多個外部來源的資源整合後分發到多個目標工具。

**當前問題：**
- 複製邏輯散落在 `copy_skills()` 函式中，有大量重複
- 每次新增來源或目標都需要修改多處程式碼
- OpenCode 支援不完整
- Claude Code 安裝方式過時

**利害關係人：**
- 使用此 CLI 工具的開發者
- 支援的 AI 工具使用者（Claude Code、Antigravity、OpenCode、Codex、Gemini CLI）

## Goals / Non-Goals

### Goals
- 將複製邏輯標準化為三階段流程
- 使新增來源或目標更容易
- 支援 OpenCode 完整目錄結構
- 支援 Claude Code native 安裝
- 支援專案目錄同步

### Non-Goals
- 不改變使用者介面（CLI 指令維持不變）
- 不改變外部儲存庫的 clone 位置
- 不自動將 Claude Code 從 npm 遷移到 native

## Decisions

### Decision 1: 三階段複製架構

```
外部來源                    統一來源                     目標目錄
┌─────────────────┐        ┌────────────────────┐       ┌──────────────────┐
│ superpowers     │───┐    │                    │   ┌──►│ ~/.claude/       │
│ ~/.config/...   │   │    │ ~/.config/         │   │   │   skills/        │
├─────────────────┤   │    │   custom-skills/   │   │   │   commands/      │
│ UDS             │───┼───►│   skills/          │───┼──►├──────────────────┤
│ ~/.config/...   │   │    │   command/         │   │   │ ~/.gemini/       │
├─────────────────┤   │    │   agent/           │   │   │   antigravity/   │
│ obsidian-skills │───┤    │                    │   │   │   skills/        │
│ ~/.config/...   │   │    └────────────────────┘   │   ├──────────────────┤
├─────────────────┤   │                             │   │ ~/.config/       │
│ anthropic-skills│───┘                             ├──►│   opencode/      │
│ ~/.config/...   │                                 │   │   skills/        │
└─────────────────┘                                 │   │   commands/      │
                                                    │   │   agent/         │
                                                    │   ├──────────────────┤
                                                    │   │ ~/.codex/skills/ │
                                                    │   ├──────────────────┤
                                                    │   │ ~/.gemini/       │
                                                    │   │   skills/        │
                                                    │   │   commands/      │
                                                    │   ├──────────────────┤
                                                    └──►│ <project>/       │
                                                        │   skills/        │
                                                        │   command/       │
                                                        │   agent/         │
                                                        └──────────────────┘
```

**理由：**
- 單一真相來源（`~/.config/custom-skills`）方便管理
- 階段清晰，易於除錯
- 新增來源只需修改 Stage 1→2
- 新增目標只需修改 Stage 3

### Decision 2: OpenCode 目錄結構

```
~/.config/opencode/
├── agent/          # 現有，維持
├── skills/         # 新增
└── commands/       # 新增
```

來源對應：
- `skills/` ← `~/.config/custom-skills/skills/`
- `commands/` ← `~/.config/custom-skills/command/opencode/`（若存在）
- `agent/` ← `~/.config/custom-skills/agent/opencode/`

### Decision 3: Claude Code 安裝處理

```python
def check_claude_installed() -> bool:
    """檢查 Claude Code CLI 是否已安裝。"""
    return shutil.which("claude") is not None

def show_claude_install_instructions():
    """顯示 Claude Code 安裝指引。"""
    console.print("[yellow]Claude Code CLI 尚未安裝。[/yellow]")
    console.print()
    console.print("推薦安裝方式（自動更新）：")
    console.print("[cyan]curl -fsSL https://claude.ai/install.sh | bash[/cyan]")
    console.print()
    console.print("其他安裝方式：")
    console.print("- Homebrew: [dim]brew install --cask claude-code[/dim]")
    console.print("- 參考文件: https://code.claude.com/docs")
```

**理由：**
- Native 安裝是 Anthropic 官方推薦方式
- 避免 npm 全域安裝的權限問題
- 支援自動更新

### Decision 4: 目標目錄配置表

使用配置驅動而非硬編碼：

```python
COPY_TARGETS = {
    "claude": {
        "skills": Path.home() / ".claude" / "skills",
        "commands": Path.home() / ".claude" / "commands",
    },
    "antigravity": {
        "skills": Path.home() / ".gemini" / "antigravity" / "skills",
        "workflows": Path.home() / ".gemini" / "antigravity" / "global_workflows",
    },
    "opencode": {
        "skills": Path.home() / ".config" / "opencode" / "skills",
        "commands": Path.home() / ".config" / "opencode" / "commands",
        "agent": Path.home() / ".config" / "opencode" / "agent",
    },
    "codex": {
        "skills": Path.home() / ".codex" / "skills",
    },
    "gemini": {
        "skills": Path.home() / ".gemini" / "skills",
        "commands": Path.home() / ".gemini" / "commands",
    },
}
```

## Risks / Trade-offs

| Risk | Impact | Mitigation |
|------|--------|------------|
| 複製時間增加 | 低 | 三階段中第一階段只在 install 執行 |
| 磁碟空間增加 | 低 | skills 檔案很小，重複佔用空間可忽略 |
| 現有使用者遷移 | 中 | 新目錄會自動建立，不影響現有檔案 |
| Claude Code 未安裝 | 中 | 顯示明確安裝指引，不阻擋其他工具 |

## Migration Plan

1. **向後相容**：現有目錄結構和檔案不刪除
2. **新增目錄**：OpenCode 的 skills/commands 目錄在首次執行時自動建立
3. **無破壞性**：update 指令維持原有行為，只新增 OpenCode 支援

## Open Questions

1. ~~OpenCode 的 commands 目錄應該來自哪裡？~~ → 來自 `custom-skills/command/opencode/`（若存在）
2. ~~是否需要支援 OpenCode 的 workflows？~~ → 暫不支援，OpenCode 目前無此概念
