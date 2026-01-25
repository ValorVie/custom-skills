# Tasks: add-codex-gemini-cli-targets

## Phase 1: 基礎設施

- [x] 1.1 在 `script/utils/paths.py` 新增路徑函式
  - 新增 `get_codex_config_dir()` 回傳 `~/.codex`
  - 新增 `get_gemini_cli_config_dir()` 回傳 `~/.gemini`

- [x] 1.2 更新 `script/utils/shared.py` 類型定義
  - 更新 `TargetType` 新增 `"codex"` 和 `"gemini"`

## Phase 2: 複製邏輯

- [x] 2.1 更新 `copy_skills()` 函式
  - 新增 Codex skills 目標: `~/.codex/skills`
  - 新增 Gemini CLI skills 目標: `~/.gemini/skills`
  - 新增 Gemini CLI commands 目標: `~/.gemini/commands`

- [x] 2.2 更新 `get_target_path()` 函式
  - 新增 `("codex", "skills")` 映射
  - 新增 `("gemini", "skills")` 映射
  - 新增 `("gemini", "commands")` 映射

## Phase 3: 列表指令

- [x] 3.1 更新 `list_installed_resources()`
  - 在 `type_mapping` 新增 codex 和 gemini 的資源類型映射
  - 新增對應的來源識別

- [x] 3.2 更新 `script/commands/list.py`
  - 更新 `--target` 選項支援 codex 和 gemini

## Phase 4: Toggle 指令

- [x] 4.1 更新 `script/commands/toggle.py`
  - 新增 codex 和 gemini 到 `TARGETS` 映射

- [x] 4.2 更新 `show_restart_reminder()`
  - 新增 Codex 和 Gemini CLI 的重啟提醒訊息

- [x] 4.3 更新 disabled 目錄支援
  - `get_disabled_path()` 已能正確處理新目標（使用通用邏輯）

## Phase 5: TUI 介面

- [x] 5.1 更新 `script/tui/app.py`
  - 更新 `TARGET_OPTIONS` 新增 Codex 和 Gemini CLI
  - 更新 `TYPE_OPTIONS_BY_TARGET` 新增對應資源類型

- [x] 5.2 更新 MCP Config 路徑
  - 新增 `get_mcp_config_path()` 對 codex 和 gemini 的支援
  - Codex: `~/.codex/config.json`
  - Gemini CLI: `~/.gemini/settings.json`

## Phase 6: 文件更新

- [x] 6.1 更新 `README.md`
  - 在「支援的 AI 工具」區塊新增 Codex 和 Gemini CLI
  - 更新 `list` 和 `toggle` 指令的 `--target` 說明

- [x] 6.2 更新 `docs/AI開發環境設定指南.md`
  - 在「支援的 AI 工具」區塊新增 Codex 和 Gemini CLI
  - 更新相關指令說明
  - 更新架構圖

- [x] 6.3 更新 `CHANGELOG.md`
  - 新增 v0.4.0 變更記錄

## Phase 7: 驗證與修正

- [x] 7.0 修正 TUI BadIdentifier 錯誤
  - 問題：Codex 有 `.system` skill，產生無效 ID `cb-.system`
  - 解法：新增 `sanitize_widget_id()` 函式清理資源名稱
  - 將 `.` 等無效字元替換為 `_`，並移除開頭底線

- [ ] 7.1 手動測試
  - 執行 `ai-dev install` 驗證複製到新目標
  - 執行 `ai-dev list --target codex` 驗證列表功能
  - 執行 `ai-dev list --target gemini` 驗證列表功能
  - 執行 `ai-dev tui` 驗證 TUI 下拉選單
