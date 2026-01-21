# skill-tui Spec Delta

## MODIFIED Requirements

### Requirement: TUI Layout (TUI 佈局)

TUI MUST (必須) 包含以下區域：

> **變更說明**：Target 下拉選單新增 Codex 和 Gemini CLI 選項。

#### Scenario: 頂部操作列
給定 TUI 已啟動
則頂部應該顯示：
- Install 按鈕 - 執行安裝流程
- Update 按鈕 - 執行更新流程
- Status 按鈕 - 顯示環境狀態
- Add Skills 按鈕 - 開啟新增第三方 Skills 對話框
- Quit 按鈕 - 退出 TUI

#### Scenario: 過濾器列
給定 TUI 已啟動
當顯示過濾器列時
則應該包含：
- Target 下拉選單：Claude Code / Antigravity / OpenCode / Codex / Gemini CLI
- Type 下拉選單：Skills / Commands / Agents / Workflows（依據 Target 動態變更）

#### Scenario: 資源列表
給定使用者選擇了 Target 與 Type
則應該顯示該組合下的所有資源：
- Checkbox 顯示啟用/停用狀態
- 資源名稱
- 資源來源（uds/obsidian/anthropic/custom/user）

#### Scenario: 底部快捷鍵列
給定 TUI 已啟動
則底部應該顯示可用的快捷鍵提示。

## ADDED Requirements

### Requirement: Codex Target in TUI (TUI 中的 Codex 目標)

TUI MUST (必須) 支援 Codex 作為目標工具。

#### Scenario: 選擇 Codex 目標

給定使用者在 Target 下拉選單選擇 "Codex"
當選擇完成時
則 Type 下拉選單應該只顯示 "Skills" 選項
且資源列表應該顯示 `~/.codex/skills` 目錄下的 skills

### Requirement: Gemini CLI Target in TUI (TUI 中的 Gemini CLI 目標)

TUI MUST (必須) 支援 Gemini CLI 作為目標工具。

#### Scenario: 選擇 Gemini CLI 目標

給定使用者在 Target 下拉選單選擇 "Gemini CLI"
當選擇完成時
則 Type 下拉選單應該顯示 "Skills" 和 "Commands" 選項
且資源列表應該根據選擇的類型顯示對應目錄的資源

### Requirement: MCP Config for New Targets (新目標的 MCP 設定)

TUI MUST (必須) 在 MCP Config 區塊顯示新目標的設定檔路徑。

#### Scenario: Codex MCP 設定檔路徑

給定使用者選擇 Codex 目標
當顯示 MCP Config 區塊時
則應該顯示 Codex 的設定檔路徑（如 `~/.codex/config.json`）

#### Scenario: Gemini CLI MCP 設定檔路徑

給定使用者選擇 Gemini CLI 目標
當顯示 MCP Config 區塊時
則應該顯示 Gemini CLI 的設定檔路徑（如 `~/.gemini/settings.json`）
