# Tasks: 重構 install/update 流程

## 1. 路徑與配置更新

- [x] 1.1 在 `paths.py` 確認所有目錄路徑函式存在
- [x] 1.2 新增 `COPY_TARGETS` 配置表到 `shared.py`
- [x] 1.3 從 `NPM_PACKAGES` 移除 `@anthropic-ai/claude-code`

## 2. Claude Code Native 安裝支援

- [x] 2.1 新增 `check_claude_installed()` 函式
- [x] 2.2 新增 `show_claude_install_instructions()` 函式
- [x] 2.3 在 `install.py` 開始時檢查 Claude Code 並顯示安裝指引

## 3. 三階段複製邏輯重構

- [x] 3.1 新增 `copy_sources_to_custom_skills()` 函式（Stage 2）
- [x] 3.2 新增 `copy_custom_skills_to_targets()` 函式（Stage 3）
- [x] 3.3 重構 `copy_skills()` 使用新的兩階段函式
- [x] 3.4 移除 `copy_skills()` 中的重複程式碼

## 4. OpenCode 完整支援

- [x] 4.1 在 `install.py` 建立 OpenCode 的 skills/commands 目錄
- [x] 4.2 在 `COPY_TARGETS` 新增 OpenCode skills/commands 配置
- [x] 4.3 建立 `command/opencode/` 目錄結構（若需要）
- [x] 4.4 在 `shared.py` 的 `list_installed_resources()` 新增 OpenCode skills/commands 支援
- [x] 4.5 更新 `DEFAULT_TOGGLE_CONFIG` 新增 OpenCode skills/commands

## 5. 專案目錄同步

- [x] 5.1 確認 `get_project_root()` 正確偵測專案目錄
- [x] 5.2 確認專案目錄同步邏輯在 Stage 3 執行
- [x] 5.3 新增專案目錄同步的可選旗標（`--sync-project` / `--no-sync-project`）

## 6. 測試與驗證

- [x] 6.1 手動測試 `ai-dev install --skip-npm --skip-repos`
- [x] 6.2 驗證 OpenCode skills/commands 目錄正確建立
- [x] 6.3 驗證 Claude Code 安裝指引正確顯示
- [x] 6.4 驗證專案目錄同步功能

## 7. 文件更新

- [x] 7.1 更新 README 說明 Claude Code 安裝方式
- [x] 7.2 ~~更新 skills/commands/update.md 說明三階段流程~~ (README 已涵蓋，無需額外文件)

## Dependencies

- Task 3 依賴 Task 1, 2
- Task 4 依賴 Task 3
- Task 5 依賴 Task 3
- Task 6 依賴 Task 3, 4, 5
- Task 7 依賴 Task 6
