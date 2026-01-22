# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.1] - 2026-01-21

### Fixed

- 修正 TUI 在資源名稱包含特殊字元時的 BadIdentifier 錯誤
  - 新增 `sanitize_widget_id()` 函式處理特殊字元
- 過濾隱藏資源（如 Codex 的 `.system` 系統目錄）不顯示於列表中

## [0.4.0] - 2026-01-21

### Added

- **新增 Codex 目標工具支援**
  - Skills 路徑：`~/.codex/skills`
  - `list`、`toggle`、TUI 皆支援 `--target codex`
- **新增 Gemini CLI 目標工具支援**
  - Skills 路徑：`~/.gemini/skills`
  - Commands 路徑：`~/.gemini/commands`
  - `list`、`toggle`、TUI 皆支援 `--target gemini`
- `install` 和 `update` 指令會自動複製 Skills 到 Codex 和 Gemini CLI 目錄

### Changed

- TUI Target 下拉選單新增 Codex 和 Gemini CLI 選項
- MCP Config 區塊新增 Codex 和 Gemini CLI 的設定檔路徑

## [0.3.1] - 2026-01-21

### Fixed

- 修正 TUI 內部呼叫 CLI 指令的方式，改用 `shutil.which("ai-dev")` 找到已安裝的指令
- 修正打包設定，加入 `[tool.setuptools.package-data]` 以包含 `.tcss` 樣式檔

### Docs

- 新增本地開發安裝的注意事項：需更新版本號才會重新安裝

## [0.3.0] - 2026-01-21

### Changed

- **指令重新命名**：`ai-dev maintain` 改為 `ai-dev update`
  - 使指令名稱更符合「更新」的語意
  - 與常見 CLI 慣例一致（如 `apt update`、`brew update`）
- TUI 介面按鈕標籤從 "Maintain" 改為 "Update"
- 更新所有相關文檔與規格文件

## [0.2.0] - 2026-01-20

### Added

- **全域 CLI 安裝支援**：可透過 `uv tool install` 或 `pipx` 從 GitHub 安裝
- **`project` 指令群組**：新增專案級別操作
  - `ai-dev project init`：整合 `openspec init` + `uds init`
  - `ai-dev project update`：整合 `openspec update` + `uds update`
  - 支援 `--only` 參數選擇特定工具
  - 支援 `--force` 參數強制重新初始化
- 新增 `script/__init__.py` 使模組可被匯入

### Changed

- 重構所有模組匯入為套件相對匯入格式
- 更新 `pyproject.toml` 新增 entry point 配置
- 更新安裝說明文件

## [0.1.0] - 2026-01-15

### Added

- 初始版本
- `install` 指令：首次安裝 AI 開發環境
- `maintain` 指令：每日維護更新
- `status` 指令：檢查環境狀態
- `list` 指令：列出已安裝資源
- `toggle` 指令：啟用/停用資源
- `tui` 指令：互動式終端介面
