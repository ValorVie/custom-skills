# Proposal: align-tui-with-cli

## 摘要

對齊 TUI 介面與 CLI 的功能，確保 TUI 能存取所有 CLI 提供的核心功能。

## 背景

目前 `ai-dev` CLI 提供以下指令：

| 指令 | TUI 支援 | 說明 |
|------|----------|------|
| `install` | ✓ | 首次安裝 |
| `update` | ✓ | 更新工具（但缺少 `--sync-upstream` 選項） |
| `status` | ✓ | 環境狀態 |
| `clone` | ✗ | 分發 Skills 到各工具目錄 |
| `list` | ✓（資源列表） | 列出已安裝資源 |
| `toggle` | ✓（checkbox） | 啟用/停用資源 |
| `tui` | N/A | 啟動 TUI |
| `add-repo` | ✗ | 新增 Git repo |
| `project init` | ✗ | 專案初始化 |
| `project update` | ✗ | 專案配置更新 |
| `standards status` | ✗ | 標準體系狀態 |
| `standards list` | ✗ | 列出可用 profiles |
| `standards switch` | ✗ | 切換 profile |
| `standards show` | ✗ | 顯示 profile 內容 |

### 分析

TUI 缺少以下關鍵功能：

1. **Clone 按鈕**：分發 Skills 到各工具目錄（v0.6.0 新增功能，拆分自 update）
2. **Standards Profile 管理**：切換 uds/ecc/minimal 標準體系
3. **Update --sync-upstream 選項**：同步上游第三方 repo

### 優先級評估

| 功能 | 優先級 | 理由 |
|------|--------|------|
| Clone 按鈕 | 高 | v0.6.0 將 clone 從 update 拆分，TUI 需對應調整 |
| Standards Profile | 中 | 新功能，但使用頻率較低 |
| sync-upstream | 低 | 進階功能，可透過 CLI 使用 |

## 範圍

### 包含

1. 新增 Clone 按鈕到頂部操作列
2. 新增 Standards Profile 下拉選單或專區
3. Update 按鈕增加 sync-upstream 選項（可選）

### 不包含

- `add-repo` 指令（進階功能，保持 CLI only）
- `project init/update`（專案初始化，保持 CLI only）

## 相依性

- 已完成 v0.6.0 ECC 整合
- 已完成 clone 和 standards 指令

## 相關規格

- `openspec/specs/skill-tui/spec.md`

## 預估影響

- 修改 `script/tui/app.py`
- 可能需要擴展 `script/utils/shared.py`
