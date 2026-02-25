## ADDED Requirements

### Requirement: CLI 入口點使用 Bun shebang
系統 SHALL 提供 `src/cli.ts` 作為 CLI 入口點，使用 `#!/usr/bin/env bun` shebang。

#### Scenario: 直接執行入口點
- **WHEN** 使用者執行 `bun run src/cli.ts --help`
- **THEN** 顯示所有可用指令的說明文字

### Requirement: Commander.js 主程式註冊所有指令
系統 SHALL 使用 Commander.js 建立主程式，註冊所有頂層指令和子命令組。

#### Scenario: 版本查詢
- **WHEN** 使用者執行 `ai-dev --version`
- **THEN** 輸出 `2.0.0`

#### Scenario: 所有指令可見
- **WHEN** 使用者執行 `ai-dev --help`
- **THEN** 輸出 SHALL 包含 install、update、clone、status、list、toggle、add-repo、add-custom-repo、update-custom-repo、test、coverage、derive-tests、tui、project、standards、hooks、sync、mem

### Requirement: 子命令組結構
系統 SHALL 支援以下子命令組，每組有獨立的 help：
- `ai-dev project` (init, update)
- `ai-dev standards` (status, list, switch, show, overlaps)
- `ai-dev hooks` (install, uninstall, status)
- `ai-dev sync` (init, push, pull, status, add, remove)
- `ai-dev mem` (register, push, pull, status, reindex)

#### Scenario: 子命令 help
- **WHEN** 使用者執行 `ai-dev sync --help`
- **THEN** 顯示 sync 子命令組的所有子指令 (init, push, pull, status, add, remove)

### Requirement: 指令介面向後相容
所有 v1 指令的名稱和參數 SHALL 在 v2 中保持相同。

#### Scenario: install 指令參數相容
- **WHEN** 使用者執行 `ai-dev install`
- **THEN** 行為與 v1 `ai-dev install` 相同（安裝環境）

#### Scenario: sync push 指令相容
- **WHEN** 使用者執行 `ai-dev sync push`
- **THEN** 行為與 v1 `ai-dev sync push` 相同（推送同步）
