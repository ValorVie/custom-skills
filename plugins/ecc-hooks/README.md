# ECC Hooks Plugin

Everything Claude Code - Memory Persistence & Strategic Compact Hooks

## Features

- **SessionStart**: Load previous context and detect package manager on new session
- **SessionEnd**: Persist session state and evaluate for extractable patterns
- **PreCompact**: Save state before context compaction
- **PreToolUse**:
  - Block dev servers outside tmux
  - Reminder for long-running commands
  - Git push review reminder
  - Strategic compact suggestions
- **PostToolUse**: Log PR URL after creation
- **Stop**: Check for console.log in modified files

## Requirements

- Python 3.x（腳本僅使用標準函式庫）
  - Linux/macOS: `python3` 應已預裝
  - Windows: 安裝 Python 3.6+ 會自動加入 `python3.exe` 到 PATH

## Installation

### 方式 1：從 Marketplace 安裝（推薦）

```bash
# 1. 添加 marketplace
claude plugin marketplace add https://github.com/ValorVie/custom-skills.git

# 2. 安裝 plugin
claude plugin install ecc-hooks@custom-skills
```

或在 Claude Code 會話中使用 slash command：

```
/plugin install ecc-hooks@custom-skills
```

### 方式 2：本地開發測試

直接載入本地 plugin 進行測試，無需推送到 GitHub：

```bash
claude --plugin-dir "/path/to/custom-skills/plugins/ecc-hooks"
```

## Structure

```
ecc-hooks/
├── .claude-plugin/
│   └── plugin.json
├── hooks/
│   └── hooks.json
├── scripts/
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

## License

MIT
