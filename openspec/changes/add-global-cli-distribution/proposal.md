# Proposal: add-global-cli-distribution

## Summary

將現有的 Python CLI 腳本打包為可全域安裝的工具，並新增 `project` 子命令群組來處理專案級別的初始化與更新操作。

## Problem

### 現況

1. **執行方式不便**：目前 CLI 必須透過 `uv run python script/main.py` 執行，無法在任意目錄下直接使用
2. **缺乏專案級操作**：現有指令（`install`、`maintain`）只處理全域環境，沒有專案級的初始化與更新功能
3. **使用者體驗分散**：使用者需要分別執行 `openspec init`、`uds init` 等多個命令來初始化專案

### 影響

- 新使用者入門門檻高，需要記住多個工具的命令
- 專案初始化步驟容易遺漏
- 專案更新流程沒有統一入口

## Proposed Solution

### 策略：保持分離，加強便利性

採用**薄包裝**模式：不重新實作 openspec/uds 的邏輯，而是提供便利的入口點呼叫底層工具。

### 變更內容

#### 1. 全域安裝支援

在 `pyproject.toml` 新增 entry point，讓 CLI 可透過 `uv tool install` 或 `pipx install` 全域安裝：

```toml
[project.scripts]
ai-dev = "script.main:app"
```

安裝後可直接執行：
```shell
ai-dev install
ai-dev maintain
ai-dev project init
```

#### 2. 新增 `project` 子命令群組

```
ai-dev project
├── init     # 初始化專案（整合 openspec init + uds init）
└── update   # 更新專案配置（整合 openspec update + uds update）
```

#### 3. 實作方式

`project init` 和 `project update` 僅作為**薄包裝**，底層呼叫：
- `subprocess.run(["openspec", "init"])` / `subprocess.run(["openspec", "update"])`
- `subprocess.run(["uds", "init"])` / `subprocess.run(["uds", "update"])`

這樣保持與原生命令的相容性，維護成本極低。

## Why This Approach

| 考量 | 選擇理由 |
|------|---------|
| **維護成本** | openspec/uds 是活躍維護的 npm 套件，包裝而非重寫可避免追蹤上游變更 |
| **單一職責** | 本專案核心是「統一 Skills 管理」，不是取代 openspec/uds |
| **文件一致** | 使用者可查閱 openspec/uds 官方文件，不會有認知落差 |
| **故障隔離** | 底層工具出問題時，責任歸屬清楚 |
| **向後相容** | 使用者仍可直接使用 `openspec init`、`uds init` |

## Impact

### 新增能力

- **cli-distribution**：全域安裝與套件發布機制
- **project-commands**：專案級初始化與更新指令

### 修改能力

- **setup-script**：擴展現有規格，加入 entry point 配置

### 不變

- 現有的 `install`、`maintain`、`status`、`list`、`toggle`、`tui` 指令維持原有行為
- 底層工具（openspec、uds）的功能不變

## Decisions

1. **CLI 命名**：使用 `ai-dev`
2. **發布管道**：透過 GitHub 私有倉庫發布，使用 `uv tool install git+...` 安裝
3. **錯誤處理**：當底層工具（openspec/uds）未安裝時，顯示錯誤訊息並提供安裝指引

## Installation

安裝方式（需要 GitHub 倉庫存取權限）：

```shell
# 使用 uv（推薦）
uv tool install git+https://github.com/ValorVie/custom-skills.git

# 使用 pipx
pipx install git+https://github.com/ValorVie/custom-skills.git

# 私有倉庫需要 token
uv tool install git+https://<GITHUB_TOKEN>@github.com/ValorVie/custom-skills.git
```

更新：
```shell
uv tool upgrade ai-dev
```

## Related

- [setup-script](../../specs/setup-script/spec.md)：現有安裝腳本規格
- [skill-npm-integration](../../specs/skill-npm-integration/spec.md)：NPM 套件整合
