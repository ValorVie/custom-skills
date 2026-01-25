# Tasks: add-mcp-config-viewer

## Overview

在 TUI 介面中新增 MCP Config 檢視功能。

## Task List

### Task 1: 實作 MCP 設定檔路徑對應函式
**File**: `script/utils/shared.py`
**Goal**: 新增函式取得各工具的 MCP 設定檔路徑
**Acceptance Criteria**:
- [x] `get_mcp_config_path(target)` 回傳正確路徑
- [x] 支援 claude, antigravity, opencode 三種 target
- [x] 回傳 Path 物件，且標記檔案是否存在

### Task 2: 實作開啟編輯器函式
**File**: `script/utils/shared.py`
**Goal**: 新增函式在外部編輯器中開啟檔案
**Acceptance Criteria**:
- [x] `open_in_editor(file_path)` 正確啟動編輯器
- [x] 優先使用 `EDITOR` 環境變數
- [x] 降級策略：`code` → `open`/`xdg-open`
- [x] 跨平台支援 (macOS, Linux, Windows)
- [x] `open_in_file_manager(file_path)` 在檔案管理器中開啟

### Task 3: 新增 TUI MCP Config 區塊
**File**: `script/tui/app.py`
**Goal**: 在 TUI 介面中顯示 MCP 設定檔路徑
**Acceptance Criteria**:
- [x] 在資源列表下方顯示 MCP Config 區塊
- [x] 顯示目前選擇的 target 對應的設定檔路徑
- [x] 當 target 切換時自動更新路徑顯示
- [x] 顯示檔案是否存在的狀態

### Task 4: 新增「Open in Editor」與「Open Folder」按鈕
**File**: `script/tui/app.py`
**Goal**: 提供按鈕開啟設定檔
**Acceptance Criteria**:
- [x] 點擊「Open in Editor」按鈕開啟設定檔於外部編輯器
- [x] 點擊「Open Folder」按鈕在檔案管理器中開啟
- [x] 檔案不存在時顯示提示訊息
- [x] 新增快捷鍵 `e` 開啟編輯器
- [x] 新增快捷鍵 `f` 開啟檔案管理器

### Task 5: 更新 TUI 樣式
**File**: `script/tui/styles.tcss`
**Goal**: 為 MCP Config 區塊新增樣式
**Acceptance Criteria**:
- [x] MCP Config 區塊有清楚的視覺分隔
- [x] 路徑文字使用適當的字體樣式
- [x] 按鈕樣式與現有設計一致

## Dependencies

```
Task 1 ──┬── Task 3 ── Task 5
         │
Task 2 ──┴── Task 4
```

- Task 1 和 Task 2 可並行執行
- Task 3 依賴 Task 1
- Task 4 依賴 Task 2
- Task 5 可在 Task 3 後執行

## Verification

1. 執行 `uv run script/main.py tui`
2. 切換 Target 下拉選單，確認 MCP 路徑正確更新
3. 點擊「Open in Editor」按鈕，確認編輯器開啟正確檔案
4. 點擊「Open Folder」按鈕，確認檔案管理器開啟正確目錄
5. 按下 `e` 快捷鍵，確認同樣開啟編輯器
6. 按下 `f` 快捷鍵，確認開啟檔案管理器
