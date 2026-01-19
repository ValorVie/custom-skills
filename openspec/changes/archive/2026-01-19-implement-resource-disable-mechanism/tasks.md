# Tasks: implement-resource-disable-mechanism

## Overview

基於 design.md 的架構設計，實作資源停用機制。

---

## Task 1: 實作 disabled 路徑函式 ✅

**File**: `script/utils/shared.py`

### 1.1 新增 `get_disabled_base_dir()` 函式

```python
def get_disabled_base_dir() -> Path:
    """取得 disabled 目錄的基礎路徑。"""
    return get_custom_skills_dir() / "disabled"
```

### 1.2 新增 `get_disabled_path()` 函式

```python
def get_disabled_path(target: str, resource_type: str, name: str) -> Path:
    """取得特定資源在 disabled 目錄中的路徑。

    Args:
        target: 目標工具 (claude, antigravity, opencode)
        resource_type: 資源類型 (skills, commands, agents, workflows)
        name: 資源名稱

    Returns:
        Path: disabled 目錄中的完整路徑
    """
    return get_disabled_base_dir() / target / resource_type / name
```

**Acceptance Criteria**:
- [x] 函式正確回傳路徑
- [x] 路徑結構符合 design.md 規格

---

## Task 2: 實作 `disable_resource()` 函式 ✅

**File**: `script/utils/shared.py`

### 實作內容

```python
def disable_resource(target: str, resource_type: str, name: str) -> bool:
    """
    停用資源：將檔案從目標工具目錄移動到 disabled 目錄。

    Args:
        target: 目標工具 (claude, antigravity, opencode)
        resource_type: 資源類型 (skills, commands, agents, workflows)
        name: 資源名稱

    Returns:
        bool: True 表示成功，False 表示失敗
    """
```

### 流程

1. 取得目標路徑（使用現有的 `get_target_path()` 或相關函式）
2. 檢查來源是否存在
   - 若不存在：顯示警告並回傳 False
3. 取得 disabled 路徑
4. 確保 disabled 目錄存在（`mkdir(parents=True, exist_ok=True)`）
5. 使用 `shutil.move()` 移動檔案/目錄
6. 更新 `toggle-config.yaml`
7. 呼叫 `show_restart_reminder()`
8. 回傳 True

**Acceptance Criteria**:
- [x] 成功移動檔案到 disabled 目錄
- [x] 不存在的資源顯示警告
- [x] 正確更新 toggle-config.yaml
- [x] 顯示重啟提醒

---

## Task 3: 實作 `enable_resource()` 函式 ✅

**File**: `script/utils/shared.py`

### 實作內容

```python
def enable_resource(target: str, resource_type: str, name: str) -> bool:
    """
    啟用資源：將檔案從 disabled 目錄移回目標工具目錄。

    Args:
        target: 目標工具 (claude, antigravity, opencode)
        resource_type: 資源類型 (skills, commands, agents, workflows)
        name: 資源名稱

    Returns:
        bool: True 表示成功，False 表示失敗
    """
```

### 流程

1. 取得 disabled 路徑
2. 取得目標路徑
3. 檢查 disabled 目錄中是否存在
   - 若存在：使用 `shutil.move()` 移回目標目錄
   - 若不存在：從來源目錄重新複製（使用現有的複製函式）
4. 更新 `toggle-config.yaml`（移除 disabled 記錄）
5. 呼叫 `show_restart_reminder()`
6. 回傳 True

**Acceptance Criteria**:
- [x] 從 disabled 目錄還原檔案
- [x] disabled 不存在時從來源重新複製
- [x] 正確更新 toggle-config.yaml
- [x] 顯示重啟提醒

---

## Task 4: 實作 `show_restart_reminder()` 函式 ✅

**File**: `script/utils/shared.py`

### 實作內容

```python
def show_restart_reminder(target: str) -> None:
    """顯示重啟提醒訊息。

    Args:
        target: 目標工具 (claude, antigravity, opencode)
    """
```

### 提示訊息

| 工具 | 訊息 |
|------|------|
| claude | `exit` → `claude` |
| antigravity | 關閉 → 重新開啟 VSCode |
| opencode | `exit` → `opencode` |

**Acceptance Criteria**:
- [x] 根據 target 顯示對應提示
- [x] 訊息格式符合 spec.md 規格

---

## Task 5: 整合 toggle 指令 ✅

**File**: `script/commands/toggle.py`

### 修改內容

1. 當 `--disable` 時呼叫 `disable_resource()`
2. 當 `--enable` 時呼叫 `enable_resource()`
3. 移除或保留現有的 `copy_skills()` 呼叫（根據需求）

**Acceptance Criteria**:
- [x] `toggle --disable` 觸發 `disable_resource()`
- [x] `toggle --enable` 觸發 `enable_resource()`
- [x] 操作成功時顯示重啟提醒

---

## Task 6: 更新 TUI 介面 ✅

**File**: `script/tui/app.py`

### 修改內容

1. 停用 checkbox 時呼叫 `disable_resource()`
2. 啟用 checkbox 時呼叫 `enable_resource()`
3. 操作後重新整理列表

**Acceptance Criteria**:
- [x] TUI checkbox 操作觸發對應函式
- [x] 操作後列表正確更新
- [x] 顯示重啟提醒

---

## Task 7: 測試驗證 ✅

### 7.1 手動測試

- [x] 停用 Claude Code skill → 檔案移動到 disabled
- [x] 啟用 skill → 檔案從 disabled 還原
- [ ] 停用後重啟 Claude Code → skill 確實不載入（需使用者手動驗證）
- [ ] 啟用後重啟 Claude Code → skill 正常載入（需使用者手動驗證）

### 7.2 邊界情況測試

- [x] 停用不存在的資源 → 顯示警告
- [x] 啟用 disabled 目錄中不存在的資源 → 從來源重新複製（已實作）
- [x] 權限錯誤時 → 顯示明確錯誤訊息（已實作 try/except）

---

## Dependencies

- Task 1 必須先完成
- Task 2, 3, 4 可平行開發
- Task 5, 6 依賴 Task 2, 3, 4
- Task 7 依賴所有其他任務

## Estimated Complexity

| Task | 複雜度 | 備註 |
|------|--------|------|
| Task 1 | 低 | 簡單路徑函式 |
| Task 2 | 中 | 核心邏輯 |
| Task 3 | 中 | 需處理多種情況 |
| Task 4 | 低 | 簡單輸出 |
| Task 5 | 中 | 整合現有程式碼 |
| Task 6 | 中 | TUI 整合 |
| Task 7 | 低 | 測試驗證 |

---

## Implementation Summary

**完成日期**: 2026-01-19

**新增函式** (`script/utils/shared.py`):
- `get_disabled_base_dir()` - 取得 disabled 目錄基礎路徑
- `get_disabled_path()` - 取得特定資源的 disabled 路徑
- `get_resource_file_path()` - 取得資源在目標目錄的完整路徑
- `show_restart_reminder()` - 顯示重啟提醒
- `disable_resource()` - 停用資源（移動到 disabled）
- `enable_resource()` - 啟用資源（從 disabled 還原）
- `copy_single_resource()` - 從來源複製單一資源

**修改檔案**:
- `script/commands/toggle.py` - 整合檔案移動機制，移除 `--sync` 參數
- `script/tui/app.py` - checkbox 變更即時觸發停用/啟用操作
