# skill-listing Spec Delta

## MODIFIED Requirements

### Requirement: List Command (列表指令)

腳本 MUST (必須) 實作 `list` 指令以顯示已安裝的資源。

> **變更說明**：新增 Codex 和 Gemini CLI 作為支援的目標工具。

#### Scenario: 列出所有 Skills
給定使用者執行 `ai-dev list`
當未指定 `--type` 參數時
則應該顯示所有類型的資源（skills、commands、agents）並標示來源。

#### Scenario: 列出特定類型的資源
給定使用者執行 `ai-dev list --type skills`
當指定 `--type` 參數時
則應該只顯示該類型的資源。

#### Scenario: 列出特定工具的資源
給定使用者執行 `ai-dev list --target <target>` 指令
當 target 為 `claude`、`antigravity`、`opencode`、`codex` 或 `gemini` 時
則應該列出該工具安裝的所有資源

#### Scenario: 標示資源來源
給定使用者執行 `list` 指令
當顯示資源清單時
則每個項目應該標示其來源：
- `universal-dev-standards`：來自 UDS
- `obsidian-skills`：來自 Obsidian Skills
- `anthropic-skills`：來自 Anthropic Skills
- `custom-skills`：來自本專案
- `user`：使用者自建（不在任何來源中）
- `npm:<package>`：來自第三方 npm 套件

## ADDED Requirements

### Requirement: Codex Listing Support (Codex 列表支援)

list 指令 MUST (必須) 支援列出 Codex 的 skills。

#### Scenario: 列出 Codex Skills

給定使用者執行 `ai-dev list --target codex --type skills`
當 `~/.codex/skills` 目錄存在
則應該列出該目錄下的所有 skills 及其來源

### Requirement: Gemini CLI Listing Support (Gemini CLI 列表支援)

list 指令 MUST (必須) 支援列出 Gemini CLI 的 skills 和 commands。

#### Scenario: 列出 Gemini CLI Skills

給定使用者執行 `ai-dev list --target gemini --type skills`
當 `~/.gemini/skills` 目錄存在
則應該列出該目錄下的所有 skills 及其來源

#### Scenario: 列出 Gemini CLI Commands

給定使用者執行 `ai-dev list --target gemini --type commands`
當 `~/.gemini/commands` 目錄存在
則應該列出該目錄下的所有 commands 及其來源
