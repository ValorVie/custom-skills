# 開發指南 (Dev Guide)

本資料夾收錄專案開發過程中常用的工具指南、工作流程與參考文件。

---

## 架構原則 (`principles/`)

| 文件 | 說明 |
|------|------|
| [GOLDEN-STANDARDS.md](principles/GOLDEN-STANDARDS.md) | 軟體工程黃金標準與架構原則（涵蓋 SDLC 全面向） |

## AI 開發工具 (`ai-tools/`)

| 文件 | 說明 |
|------|------|
| [CLAUDE-CODE-SECURITY.md](ai-tools/CLAUDE-CODE-SECURITY.md) | Claude Code 安全配置指南 |
| [OPENCODE-SECURITY.md](ai-tools/OPENCODE-SECURITY.md) | OpenCode 安全配置指南 |
| [CLAUDE-MEM-TROUBLESHOOTING.md](ai-tools/CLAUDE-MEM-TROUBLESHOOTING.md) | Claude-mem 除錯指南 |
| [MEMORY-PLUGINS-GUIDE.md](ai-tools/MEMORY-PLUGINS-GUIDE.md) | 記憶外掛並用指南 (ecc-hooks + claude-mem) |
| [opencode-使用指南.md](ai-tools/opencode-使用指南.md) | OpenCode TUI 使用指南 |
| [oh-my-opencode-guide.md](ai-tools/oh-my-opencode-guide.md) | Oh My OpenCode 指南 |
| [OPENCODE-VS-CLAUDE-CODE.md](ai-tools/OPENCODE-VS-CLAUDE-CODE.md) | OpenCode 與 Claude Code 比較 |
| [SKILLS-CLI.md](ai-tools/SKILLS-CLI.md) | Skills CLI 使用說明 |
| [CODEX-GUIDE.md](ai-tools/CODEX-GUIDE.md) | Codex 安裝、設定與管理指南 |
| [MCP-SERVER-GUIDE.md](ai-tools/MCP-SERVER-GUIDE.md) | MCP Server 設定指南（Claude Code / OpenCode 通用） |
| [CLAUDE-CODE-SYNC.md](ai-tools/CLAUDE-CODE-SYNC.md) | Claude Code 跨裝置同步指南（Syncthing / Git） |
| [CLAUDE-CODE-AGENT-TEAMS.md](ai-tools/CLAUDE-CODE-AGENT-TEAMS.md) | Claude Code Agent Teams 指南（多實例協作 vs Subagents） |

## Git 操作 (`git/`)

| 文件 | 說明 |
|------|------|
| [GIT-WORKFLOW.md](git/GIT-WORKFLOW.md) | Git 工作流程指南 |
| [LAZYGIT-GUIDE.md](git/LAZYGIT-GUIDE.md) | Lazygit 終端 Git UI 教學（安裝/設定/工作流） |
| [GIT-REMOVE-SENSITIVE-FILES.md](git/GIT-REMOVE-SENSITIVE-FILES.md) | 從 Git 歷史移除敏感檔案 |
| [GIT-SHARED-ACCOUNT-IDENTITY.md](git/GIT-SHARED-ACCOUNT-IDENTITY.md) | 共用帳號 Git 身分管理（SSH Key 分離 + Commit 身分） |
| [GIT-SUBMODULE-PERFORMANCE.md](git/GIT-SUBMODULE-PERFORMANCE.md) | Git Submodule 效能優化 |
| [Git Submodule 操作指南.md](git/Git%20Submodule%20操作指南.md) | Git Submodule 操作指南 |

## 終端工具 (`terminal/`)

| 文件 | 說明 |
|------|------|
| [ALACRITTY-GUIDE.md](terminal/ALACRITTY-GUIDE.md) | Alacritty GPU 加速終端模擬器指南 |
| [WEZTERM-GUIDE.md](terminal/WEZTERM-GUIDE.md) | WezTerm 終端模擬器指南 |
| [YAZI-GUIDE.md](terminal/YAZI-GUIDE.md) | Yazi 終端檔案管理器教學（安裝/設定/使用） |
| [ZELLIJ-GUIDE.md](terminal/ZELLIJ-GUIDE.md) | Zellij 終端多工器指南 |

## 測試 (`testing/`)

| 文件 | 說明 |
|------|------|
| [TESTING-FLOW-ARCHITECTURE.md](testing/TESTING-FLOW-ARCHITECTURE.md) | 完整測試流程架構（測試金字塔 + CI/CD Pipeline） |
| [MANUAL-TESTING-FRAMEWORK.md](testing/MANUAL-TESTING-FRAMEWORK.md) | 手動測試框架（文件、工具與方法論） |

## 開發流程與架構 (`workflow/`)

| 文件 | 說明 |
|------|------|
| [DEVELOPMENT-WORKFLOW.md](workflow/DEVELOPMENT-WORKFLOW.md) | 開發工作流程 |
| [VIBE-CODING-DEV-STACK-FRAMEWORK.md](workflow/VIBE-CODING-DEV-STACK-FRAMEWORK.md) | Vibe Coding 開發堆疊框架與工作流 |
| [CODE-QUALITY-TOOLS.md](workflow/CODE-QUALITY-TOOLS.md) | 程式碼品質工具 |
| [LSP-INSTALLATION-GUIDE.md](workflow/LSP-INSTALLATION-GUIDE.md) | PHP/Python/Rust/JS/TS LSP 安裝指南 |
| [ai-dev-framework-architecture.md](workflow/ai-dev-framework-architecture.md) | ai-dev CLI 框架技術架構（指令設計、職責分工、資源管理） |
| [AI-DEV-SYNC-GUIDE.md](workflow/AI-DEV-SYNC-GUIDE.md) | ai-dev sync 跨裝置同步教學（Git backend） |
| [copy-architecture.md](workflow/copy-architecture.md) | Copy 架構說明 |
| [WSL-WINDOWS-SYNC-GUIDE.md](workflow/WSL-WINDOWS-SYNC-GUIDE.md) | WSL ↔ Windows 檔案同步指南（rsync / watchman） |

## 範例檔案 (`examples/`)

| 檔案 | 說明 |
|------|------|
| [sync-exclude.example.txt](examples/sync-exclude.example.txt) | WSL ↔ Windows 同步排除規則範例 |
| [wsl-sync-daemon.sh](examples/wsl-sync-daemon.sh) | watchman 即時同步腳本 |
| [wsl-sync-golem.service](examples/wsl-sync-golem.service) | systemd 服務範例（開機自啟） |
