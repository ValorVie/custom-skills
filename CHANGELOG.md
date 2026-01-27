# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **ECC Hooks Plugin 測試框架**
  - 新增 Jest 測試框架與測試配置
  - 重構 Code Quality Hooks 為 CLI + lib 模式
  - 實現依賴注入設計，支援完整 mock 測試
  - 109 個測試，覆蓋率 95.25%
  - 支援 JS/TS、PHP、Python 的格式化與靜態分析

- **語言無關測試工作流 Commands**
  - `/custom-skills-python-test`: 執行 Python 測試並分析結果（原 `/custom-skills-test`）
  - `/custom-skills-python-coverage`: 執行 Python 覆蓋率分析（原 `/custom-skills-coverage`）
  - `/custom-skills-python-derive-tests`: 從 OpenSpec specs 生成 pytest 測試
  - `/custom-skills-php-test`: 執行 PHPUnit 測試並分析結果
  - `/custom-skills-php-coverage`: 執行 PHPUnit 覆蓋率分析
  - `/custom-skills-php-derive-tests`: 從 OpenSpec specs 生成 PHPUnit 測試
  - `/custom-skills-report`: 生成測試報告供人工審閱（結構化資料 + AI 分析）

- **開發指南文件**
  - 新增 `docs/dev-guide/DEVELOPMENT-WORKFLOW.md`：OpenSpec 開發工作流程
  - 新增 `docs/dev-guide/GIT-WORKFLOW.md`：Git 分支與 PR 流程

- **CLI 新增 `derive-tests` 指令**
  - 讀取 OpenSpec specs 內容供 AI 生成測試

- **OpenSpec Main Specs 同步**
  - 同步 coverage, metadata-detection, test-execution, test-generation specs 至 `openspec/specs/`

### Changed

- **Commands 重命名**
  - `/custom-skills-test` → `/custom-skills-python-test`
  - `/custom-skills-coverage` → `/custom-skills-python-coverage`

- **專案專屬工具前綴統一** (**BREAKING CHANGE**)
  - Skills 重命名：
    - `git-commit-custom` → `custom-skills-git-commit`
    - `tool-overlap-analyzer` → `custom-skills-tool-overlap-analyzer`
    - `upstream-sync` (name 欄位) → `custom-skills-upstream-sync`
  - Commands 重命名：
    - `/git-commit` → `/custom-skills-git-commit`
    - `/upstream-sync` → `/custom-skills-upstream-sync`
  - **遷移指引**：
    - `/git-commit` → `/custom-skills-git-commit`
    - `/upstream-sync` → `/custom-skills-upstream-sync`

- **`/coverage` 命令整合**
  - 新增 `--generate` / `-g` 參數，用於生成缺失的測試檔案
  - 預設模式（無參數）僅分析覆蓋率並提供建議
  - 生成模式（`--generate`）會分析並生成測試骨架

- **`tool-overlap-analyzer` Skill 更新**
  - 新增 Step 3.5: Cross-Reference Analysis（合併/移除工具前檢查引用）

### Removed

- **`/test-coverage` 命令移除** (**BREAKING CHANGE**)
  - 功能已整合至 `/coverage --generate`
  - **遷移指引**：使用者請改用 `/coverage --generate` 取代 `/test-coverage`

### Added

- **OpenSpec 實驗性工作流 (OPSX)**
  - 新增 10 個 OpenSpec Skills：
    - `openspec-explore`: 探索與釐清需求
    - `openspec-new-change`: 建立新變更
    - `openspec-continue-change`: 繼續變更工作
    - `openspec-ff-change`: 快速建立所有 artifacts
    - `openspec-apply-change`: 實作變更
    - `openspec-verify-change`: 驗證實作
    - `openspec-sync-specs`: 同步 delta specs 至 main specs
    - `openspec-archive-change`: 歸檔變更
    - `openspec-bulk-archive-change`: 批次歸檔
    - `openspec-onboard`: 引導式教學
  - 新增對應的 opsx commands（10 個）
  - 支援所有平台：Claude Code、Gemini、GitHub Copilot、OpenCode

- **上游整合**
  - 新增 `database-reviewer` agent（PostgreSQL 專家，整合 Supabase patterns）
  - 新增 `cloud-infrastructure-security` skill（雲端安全檢查清單）

- **新增 Skills**
  - `ai-friendly-architecture`: AI 友好架構設計
  - `ai-instruction-standards`: AI 指令檔案標準
  - `docs-generator`: 文件生成器

- **文件**
  - 新增 `commands/claude/COMMAND-FAMILY-OVERVIEW.md` 指令家族總覽
  - 新增 `commands/claude/generate-docs.md` 文件生成指令

### Changed

- **Skills 更新**
  - `ai-collaboration-standards`: 更新反幻覺協議
  - `methodology-system`: 更新整合流程
  - `spec-driven-dev`: 更新規格驅動開發
  - `release-standards`: 更新發布流程
  - `forward-derivation`: 更新正向推導
  - `test-coverage-assistant`: 更新測試覆蓋評估
  - `custom-skills-upstream-compare`: 新增報告檔案輸出規範

### Removed

- **舊 OpenSpec Commands**
  - 移除 `/openspec:apply`、`/openspec:archive`、`/openspec:proposal`
  - 已由新的 opsx 系列指令取代

---

## [0.9.7] - 2026-01-25

### Added

- **Profile 重疊檢測系統**
  - 新增 `profiles/overlaps.yaml` 定義功能等效的資源群組
  - 新增 `shared` 區塊定義所有 Profile 共用且強制啟用的資源
  - 新增 `ai-dev standards overlaps` 指令顯示重疊定義
  - 新增 `ai-dev standards sync` 指令同步檔案狀態
  - 新增 `--dry-run` 參數預覽 profile 切換影響
  - Profile 切換時自動停用重疊資源，保留手動停用項目與共用項目

- **upstream-sync 重疊偵測整合**
  - `analyze_upstream.py` 新增 `detect_overlaps()` 函式
  - 新增 `--detect-overlaps` 和 `--generate-overlaps` CLI 參數
  - 分析新 repo 時自動偵測與現有資源的重疊
  - 報告包含 overlap_analysis 區塊與建議

- **TUI Profile 預覽對話框**
  - 在下拉選單切換 profile 前顯示預覽確認
  - 顯示將停用的項目清單與手動保留項目
  - 快捷鍵 `t` 循環切換時跳過預覽

- **Plugin Marketplace 支援**
  - 新增 `.claude-plugin/marketplace.json` 設定檔
  - 支援 `claude plugin marketplace add` 安裝方式
  - 更新 `plugins/ecc-hooks/README.md` 安裝說明

- **第三方資源目錄 (Third-Party Resource Catalog)**
  - 新增 `third-party/` 目錄作為參考資源庫
  - 提供專案資訊模板 (`templates/project-entry.md`)
  - 提供評估檢查清單 (`templates/evaluation-checklist.md`)
  - 收錄 wshobson/agents 專案資訊作為首個範例
  - 在 README.md 和 openspec/project.md 中加入說明

- **git-commit PR 模式**
  - 新增 `git-commit pr` 子指令，自動化建立 Pull Request 流程
  - 預設建立草稿 PR，使用 `--direct` 建立正式 PR
  - 支援 `--no-squash` 保留所有提交
  - 支援 `--from` 和 `--range` 指定 commit 範圍
  - 自動生成 PR 標題與內文
  - 新增 `pr.md` 和 `pr-analyze.md` 模組

### Fixed

- **ECC Hooks Python 執行錯誤修正**
  - 改用 `python3` 執行所有 Python 腳本（僅使用標準函式庫，無需 uv）
  - 修正 Linux 系統上的 "python: Permission denied" 錯誤

- **TUI Standards Profile 偵測邏輯修正**
  - 修正 TUI 誤判專案為「未初始化」的問題
  - 改用 `.standards/` 目錄與 `active-profile.yaml` 檔案判斷初始化狀態

- **Profile 切換冗餘輸出修正**
  - 批次停用/啟用資源時使用靜默模式
  - 僅顯示摘要而非每個操作的個別訊息

### Changed

- **Profile 系統完全重構**
  - 從清單模式升級為基於重疊檢測的完整架構
  - `profiles/` 目錄包含 `uds.yaml`, `ecc.yaml`, `minimal.yaml`, `overlaps.yaml`
  - `switch_profile()` 函式基於 `overlaps.yaml` 計算需停用的項目
  - `disabled.yaml` 新增 `_profile`, `_profile_disabled`, `_manual` 欄位追蹤來源
  - 自動呼叫 `sync_resources()` 同步檔案狀態

- **TUI ECC Hooks 區塊簡化**
  - 移除安裝狀態偵測功能
  - 移除「Install/Update」、「Uninstall」和「View Config」按鈕
  - 移除快捷鍵 `i`（安裝）、`u`（移除）和 `v`（檢視設定）
  - 改為僅顯示安裝方式參考：`@plugins/ecc-hooks/README.md`
  - 提供快速安裝指令：`claude --plugin-dir "/path/to/custom-skills/plugins/ecc-hooks"`

### Compatibility

- CLI 指令完全向後相容，不影響現有使用者
- TUI 移除的安裝功能可改用 CLI 指令或 `npx skills add` 完成
- `disabled.yaml` 向後相容，舊格式仍可讀取

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
