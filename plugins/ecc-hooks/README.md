# ECC Hooks Plugin

Everything Claude Code - Memory Persistence, Strategic Compact & Code Quality Hooks

## Features

### Memory & Session Management
- **SessionStart**: Load previous context, detect package manager, and display session aliases on new session
- **SessionEnd**: Persist session state and evaluate for extractable patterns
- **PreCompact**: Save state before context compaction
- **Session Management**: `/sessions` command for listing, loading, and querying session history
- **Session Aliases**: Create memorable aliases for sessions (`/sessions alias <id> <name>`)

### Development Workflow
- **PreToolUse**:
  - Block dev servers outside tmux
  - Reminder for long-running commands
  - Git push review reminder
  - Strategic compact suggestions
- **PostToolUse**: Log PR URL after creation

### Code Quality (JS/TS, PHP, Python)
- **PostToolUse**:
  - Auto-format JS/TS files with Prettier
  - Auto-format PHP files with Pint/PHP-CS-Fixer
  - Auto-format Python files with Ruff/Black
  - TypeScript type check (requires tsconfig.json)
  - PHPStan static analysis (requires vendor/bin/phpstan)
  - mypy type check (requires pyproject.toml or mypy.ini)
  - Warn about debug code (console.log, var_dump/dd, print/breakpoint)
- **Stop**: Check for debug code in all modified files before session end

## Requirements

- **Python 3.x** - 腳本僅使用標準函式庫
  - Linux/macOS: `python3` 應已預裝
  - Windows: 安裝 Python 3.6+ 會自動加入 `python3.exe` 到 PATH
- **Node.js** - Code quality hooks 使用 Node.js
  - 建議 Node.js 18+

### Optional (for code quality features)
- **Prettier** - JS/TS formatting (`npx prettier`)
- **Pint** or **PHP-CS-Fixer** - PHP formatting
- **Ruff** or **Black** - Python formatting
- **TypeScript** - TS type checking (`npx tsc`)
- **PHPStan** - PHP static analysis
- **mypy** - Python type checking

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
claude --plugin-dir ./plugins/ecc-hooks
```

可同時載入多個 plugin：

```bash
claude --plugin-dir ./plugin-one --plugin-dir ./plugin-two
```

> **注意**：`claude plugin install` 只能從 marketplace 安裝，不支援本地路徑。本地測試請使用 `--plugin-dir`。

### 注意事項

根據 [Claude Code 官方文件](https://code.claude.com/docs/en/plugins)：
- `commands/`, `agents/`, `skills/`, `hooks/` 目錄應直接放在 plugin 根目錄。
- 只有 `plugin.json` 需放在 `.claude-plugin/` 目錄內。


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
│   ├── strategic-compact/
│   │   └── suggest-compact.py
│   └── code-quality/
│       ├── format-js.js
│       ├── format-php.js
│       ├── format-python.js
│       ├── check-typescript.js
│       ├── check-phpstan.js
│       ├── check-mypy.js
│       ├── warn-console-log.js
│       ├── warn-php-debug.js
│       ├── warn-python-debug.js
│       ├── check-debug-code.js
│       └── lib/
│           └── *.js (core logic modules)
├── tests/
│   └── code-quality/
│       └── *.test.js
└── README.md
```

## Testing

```bash
cd plugins/ecc-hooks
npm install
npm test
```

## License

MIT
