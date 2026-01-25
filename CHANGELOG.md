# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **git-commit PR 模式**
  - 新增 `git-commit pr` 子指令，自動化建立 Pull Request 流程
  - 預設建立草稿 PR，使用 `--direct` 建立正式 PR
  - 支援 `--no-squash` 保留所有提交
  - 支援 `--from` 和 `--range` 指定 commit 範圍
  - 自動生成 PR 標題與內文
  - 新增 `pr.md` 和 `pr-analyze.md` 模組

---

## [0.8.4] - 2026-01-25

### Added

- **project init 反向同步功能**
  - 在 custom-skills 專案中執行 `ai-dev project init --force` 時，會反向同步
  - 同步方向：專案根目錄 → `project-template/`
  - 同步所有 `project-template/` 中的項目，包含隱藏檔案和目錄
  - 允許開發者更新模板檔案後同步回 `project-template/` 目錄

### Fixed

- **project init Git 設定檔智慧合併**
  - `.gitattributes` 和 `.gitignore` 採用合併而非覆蓋
  - 保留目標檔案原有設定，自動加入來源新增的行
  - 以行為單位進行去重，避免重複設定

- **Windows 存取被拒錯誤修正**
  - 新增 `_safe_rmtree()` 函式處理 Windows 唯讀檔案權限問題
  - 刪除目錄前先遞迴移除所有檔案的唯讀屬性

---

## [0.8.3] - 2026-01-25

### Added

- **專案開發 Skills**
  - 新增 `custom-skills-dev` skill：專案開發工作流指引
  - 新增 `doc-updater` skill：文檔維護與更新輔助

### Fixed

- **update 命令參數修正**
  - 移除 `--sync-project` 參數（此功能已無需要）

### Documentation

- 恢復 UDS 預設文件
- 更新 `.standards/` 目錄下的標準規範

---

## [0.7.6] - 2026-01-24

### Added

- **TUI 標準管理介面**
  - 新增 `ai-dev standards` 命令群組
  - 支援 `status`、`list`、`switch`、`show` 子命令
  - TUI 介面支援標準體系 profiles 切換

- **ECC 完整擴展整合**
  - 整合 ecc 的完整 hooks、skills、agents、commands
  - 新增 hooks 目錄支援（memory-persistence、strategic-compact）

- **Claude Code Agents 與 Commands 匯入**
  - 匯入 5 個專業化 Agents（code-architect、test-specialist、reviewer、doc-writer、spec-analyst）
  - 匯入多個開發工作流 Commands

### Changed

- **標準體系 Profiles**
  - 支援 `uds`、`ecc`、`minimal` 三種 profiles
  - 預設使用 `uds` profile

---

## [0.6.0] - 2026-01-24

### Added

- **everything-claude-code (ecc) 整合**
  - 新增 `sources/ecc/` 目錄結構，準備整合 ecc 資源
  - 支援 agents、commands、skills、hooks、contexts、rules 等類型
  - ecc 資源保持 Claude Code 原生格式（不轉換為 UDS 格式）

- **上游追蹤系統**
  - 新增 `upstream/` 目錄追蹤所有第三方 repo 同步狀態
  - `upstream/sources.yaml`: 上游來源註冊表
  - 各 repo 的 `mapping.yaml` 和 `last-sync.yaml`

- **CLI 指令增強**
  - `ai-dev update --sync-upstream`: 同步上游第三方 repo
  - `ai-dev project init`: 改為從 project-template/ 複製模板

- **upstream-sync skill**
  - 新增 `/upstream-sync` skill 用於上游同步審核流程

### Changed

- **project init 行為改變**
  - 從調用 UDS/OpenSpec CLI 改為複製 project-template/ 模板
  - 移除 UDS/OpenSpec 初始化依賴

- **REPOS 配置新增**
  - 新增 `everything_claude_code` 到 REPOS 配置

### Documentation

- 更新 `docs/dev-guide/copy-architecture.md` 至 v2.0.0
- 新增 ecc 整合說明和上游追蹤系統文檔

---

## [0.5.0] - 2026-01-23

### Added

- **版本資訊顯示**
  - CLI 支援 `--version` / `-v` 參數
  - TUI 標題列顯示版本號
- **Claude Code 智慧更新**
  - 自動偵測安裝方式（npm 或 native）
  - npm 用戶會收到切換 native 安裝的提示
  - native 用戶顯示自動更新提示
- **OpenCode 完整支援**
  - 新增 Commands 和 Agents 資源類型支援
  - TUI Type 選單支援 Skills / Commands / Agents
- **TUI Sync to Project 選項**
  - 新增 "Sync to Project" 核取方塊
  - 可控制是否同步到專案目錄

### Changed

- **三階段複製架構**
  - Stage 1: Clone 儲存庫到 `~/.config/`
  - Stage 2: 整合至 `~/.config/custom-skills/`
  - Stage 3: 分發到各 AI 工具目錄
- **專案同步邏輯改進**
  - 只在 custom-skills 專案目錄中執行時才同步回專案
  - 透過 pyproject.toml 的 `name = "ai-dev"` 判斷
- **複製訊息顯示來源與目標路徑**
  - 使用 `~` 簡化路徑顯示
  - 更清晰的複製操作追蹤

### Fixed

- 修正 `get_project_root()` 返回錯誤目錄的問題

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
