# Implementation Tasks: add-global-cli-distribution

## Overview

將 CLI 打包為可全域安裝的工具，並新增 `project` 子命令群組。

## Prerequisites

- [x] 確認 openspec 和 uds 的 CLI 行為（`init`、`update` 命令）
- [x] 決定 CLI 名稱（建議：`ai-dev`）

## Phase 1: Package Configuration (套件配置)

### 1.1 更新 pyproject.toml

- [x] 新增 `[project.scripts]` entry point
- [x] 補全套件元資料（description, authors, license）
- [x] 確認依賴宣告完整

**驗證**：`uv build` 成功產生 wheel ✓

### 1.2 調整模組結構

- [x] 確認 `script/` 目錄可作為 Python 模組匯入
- [x] 新增 `script/__init__.py`（如果不存在）
- [x] 確認相對匯入路徑正確

**驗證**：`python -c "from script.main import app; print(app)"` 成功 ✓

## Phase 2: Project Commands (專案指令)

### 2.1 建立 project 指令群組

- [x] 新增 `script/commands/project.py`
- [x] 建立 `project` Typer app 作為子命令群組
- [x] 在 `main.py` 中註冊 `project` 子命令

**驗證**：`ai-dev project --help` 顯示可用子命令 ✓

### 2.2 實作 project init

- [x] 實作 `check_tool_installed()` 函式（檢查 openspec/uds 是否已安裝）
- [x] 實作 `project init` 指令
- [x] 支援 `--only` 參數
- [x] 處理工具未安裝的錯誤
- [x] 處理已初始化專案的提示

**驗證**：
- 在空目錄執行 `ai-dev project init` 成功建立 `openspec/` 和 `.standards/`（注意：uds init 有互動式選單）
- `ai-dev project init --only uds` 只建立 `.standards/` ✓

### 2.3 實作 project update

- [x] 實作 `project update` 指令
- [x] 支援 `--only` 參數
- [x] 處理未初始化專案的錯誤
- [x] 處理部分初始化專案的警告

**驗證**：
- 在已初始化專案執行 `ai-dev project update` 成功更新配置 ✓
- 在未初始化專案執行顯示錯誤訊息 ✓

## Phase 3: Testing & Documentation (測試與文件)

### 3.1 手動測試

- [x] 測試 `uv tool install .` 安裝流程
- [x] 測試所有現有指令仍正常運作
- [x] 測試 `project init` 各種情境
- [x] 測試 `project update` 各種情境
- [ ] 跨平台測試（macOS/Linux 優先，Windows 可後續）

### 3.2 更新文件

- [x] 更新 `docs/AI開發環境設定指南.md` 的安裝說明
- [x] 新增 `project init` 和 `project update` 使用說明
- [x] 更新 README.md

## Phase 4: Release (發布)

### 4.1 準備發布

- [x] 設定版本號（建議 0.2.0）
- [x] 撰寫 CHANGELOG

### 4.2 發布至 GitHub

- [ ] 確認 GitHub 倉庫權限設定正確
- [x] 更新安裝說明使用 `uv tool install git+https://github.com/ValorVie/custom-skills.git`
- [ ] 測試從 GitHub 安裝流程

## Parallelizable Work

以下任務可並行進行：
- Phase 1.1 + Phase 1.2（套件配置）
- Phase 2.2 + Phase 2.3（init 和 update 指令開發）

## Dependencies

```
Phase 1 (套件配置)
    ↓
Phase 2.1 (project 群組)
    ↓
Phase 2.2 + 2.3 (init/update 指令，可並行)
    ↓
Phase 3 (測試與文件)
    ↓
Phase 4 (發布，選用)
```
