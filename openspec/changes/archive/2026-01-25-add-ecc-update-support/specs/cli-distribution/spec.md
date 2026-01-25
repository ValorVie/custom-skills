## MODIFIED Requirements

### Requirement: Entry Point Configuration (進入點配置)

CLI 工具 MUST (必須) 透過 `pyproject.toml` 配置 entry point，使其可透過標準 Python 工具鏈安裝。

> **變更說明**：新增 everything-claude-code 儲存庫到更新清單。

#### Scenario: 使用 uv tool install 安裝

給定已配置 entry point 的專案
當執行 `uv tool install .` 於專案目錄時
則應該：
1. 安裝 CLI 到使用者的 tool 環境
2. `ai-dev` 命令可在任意目錄下執行
3. 所有子命令（`install`、`update`、`project` 等）皆可使用

#### Scenario: update 指令更新所有上游儲存庫

給定 CLI 已安裝且上游儲存庫已克隆
當執行 `ai-dev update` 時
則應該更新以下儲存庫：
1. `~/.config/custom-skills`
2. `~/.config/superpowers`
3. `~/.config/universal-dev-standards`
4. `~/.config/opencode/superpowers`
5. `~/.config/obsidian-skills`
6. `~/.config/anthropic-skills`
7. `~/.config/everything-claude-code`

## ADDED Requirements

### Requirement: Update Notification (更新通知)

`ai-dev update` 指令 MUST (必須) 在更新完成後顯示哪些儲存庫有新的更新。

#### Scenario: 顯示有更新的儲存庫

給定多個上游儲存庫
當執行 `ai-dev update` 且部分儲存庫有新 commits 時
則應該：
1. 在更新完成後顯示摘要
2. 列出所有有新更新的儲存庫名稱
3. 若無任何更新，顯示「所有儲存庫皆為最新」

#### Scenario: 沒有更新時的顯示

給定所有上游儲存庫皆為最新
當執行 `ai-dev update` 時
則應該顯示「所有儲存庫皆為最新」訊息
