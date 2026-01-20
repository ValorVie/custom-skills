# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

## [0.1.0] - 2025-01-01

### Added

- 初始版本
- `install` 指令：首次安裝 AI 開發環境
- `maintain` 指令：每日維護更新
- `status` 指令：檢查環境狀態
- `list` 指令：列出已安裝資源
- `toggle` 指令：啟用/停用資源
- `tui` 指令：互動式終端介面
