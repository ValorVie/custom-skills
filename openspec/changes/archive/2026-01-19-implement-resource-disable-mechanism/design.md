# Design: implement-resource-disable-mechanism

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    toggle 指令 / TUI                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    utils/shared.py                          │
│                                                             │
│  disable_resource()         enable_resource()               │
│       │                           │                         │
│       ▼                           ▼                         │
│  ┌──────────────┐           ┌──────────────┐               │
│  │ 移動到       │           │ 從 disabled  │               │
│  │ disabled/    │           │ 移回原位     │               │
│  └──────────────┘           └──────────────┘               │
│       │                           │                         │
│       ▼                           ▼                         │
│  ┌──────────────────────────────────────────┐              │
│  │         show_restart_reminder()          │              │
│  └──────────────────────────────────────────┘              │
└─────────────────────────────────────────────────────────────┘

目錄結構：

~/.config/custom-skills/
├── disabled/                          # 被停用的資源
│   ├── claude/
│   │   ├── skills/
│   │   │   └── <skill-name>/
│   │   └── commands/
│   │       └── <command>.md
│   ├── antigravity/
│   │   ├── skills/
│   │   └── workflows/
│   └── opencode/
│       └── agents/
├── toggle-config.yaml                 # 狀態記錄（保留）
└── skills/                            # 來源（不變）

目標工具目錄（會被移除檔案）：

~/.claude/
├── skills/                            # Claude Code skills
└── commands/                          # Claude Code commands

~/.gemini/antigravity/
├── skills/                            # Antigravity skills
└── global_workflows/                  # Antigravity workflows

~/.config/opencode/
└── agent/                             # OpenCode agents
```

## Component Design

### 1. 新增函式：`disable_resource()`

```python
def disable_resource(target: TargetType, resource_type: ResourceType, name: str) -> bool:
    """
    停用資源：將檔案從目標工具目錄移動到 disabled 目錄。

    流程：
    1. 取得目標路徑和 disabled 路徑
    2. 檢查來源是否存在
    3. 確保 disabled 目錄存在
    4. 移動檔案（shutil.move）
    5. 更新 toggle-config.yaml
    6. 顯示重啟提醒

    回傳：True 表示成功，False 表示失敗
    """
```

### 2. 新增函式：`enable_resource()`

```python
def enable_resource(target: TargetType, resource_type: ResourceType, name: str) -> bool:
    """
    啟用資源：將檔案從 disabled 目錄移回目標工具目錄。

    流程：
    1. 取得 disabled 路徑和目標路徑
    2. 檢查 disabled 目錄中是否存在
       - 若存在：移動回目標目錄
       - 若不存在：從來源重新複製
    3. 更新 toggle-config.yaml
    4. 顯示重啟提醒

    回傳：True 表示成功，False 表示失敗
    """
```

### 3. 新增函式：`show_restart_reminder()`

```python
def show_restart_reminder(target: TargetType) -> None:
    """
    顯示重啟提醒訊息。

    訊息範例：
    ┌─────────────────────────────────────────────────────────┐
    │ ⚠️  請重啟 Claude Code 以套用變更                        │
    │                                                         │
    │ 重啟方式：                                               │
    │   1. 在終端機輸入 exit 離開 Claude Code                  │
    │   2. 重新執行 claude 指令                               │
    └─────────────────────────────────────────────────────────┘
    """
```

### 4. 路徑對照表

```python
DISABLED_BASE_PATH = get_custom_skills_dir() / "disabled"

def get_disabled_path(target: TargetType, resource_type: ResourceType) -> Path:
    """取得 disabled 目錄路徑。"""
    return DISABLED_BASE_PATH / target / resource_type
```

### 5. 重啟提示訊息

| 工具 | 提示訊息 |
|------|----------|
| Claude Code | 請重啟 Claude Code（exit → claude） |
| Antigravity | 請重啟 Antigravity（關閉 → 重新開啟 VSCode） |
| OpenCode | 請重啟 OpenCode（exit → opencode） |

## Data Flow

### 停用流程

```
toggle --disable
       │
       ▼
┌──────────────────┐
│ 檢查資源是否存在 │
└──────────────────┘
       │ 存在
       ▼
┌──────────────────┐
│ 建立 disabled    │
│ 目錄結構         │
└──────────────────┘
       │
       ▼
┌──────────────────┐
│ shutil.move()    │
│ 移動檔案/目錄    │
└──────────────────┘
       │
       ▼
┌──────────────────┐
│ 更新 toggle-     │
│ config.yaml      │
└──────────────────┘
       │
       ▼
┌──────────────────┐
│ show_restart_    │
│ reminder()       │
└──────────────────┘
```

### 啟用流程

```
toggle --enable
       │
       ▼
┌──────────────────┐
│ 檢查 disabled    │
│ 目錄是否有檔案   │
└──────────────────┘
       │
       ├─── 有 ───┐
       │          ▼
       │   ┌──────────────────┐
       │   │ shutil.move()    │
       │   │ 移回原位         │
       │   └──────────────────┘
       │
       └─── 無 ───┐
                  ▼
           ┌──────────────────┐
           │ 從來源重新複製   │
           │ copy_single_     │
           │ resource()       │
           └──────────────────┘
                  │
                  ▼
           ┌──────────────────┐
           │ 更新 toggle-     │
           │ config.yaml      │
           └──────────────────┘
                  │
                  ▼
           ┌──────────────────┐
           │ show_restart_    │
           │ reminder()       │
           └──────────────────┘
```

## Migration Strategy

1. **向後相容**：保留 `toggle-config.yaml`，現有配置不受影響
2. **首次停用時遷移**：若舊配置中已有 disabled 項目但檔案仍存在，執行停用時自動遷移
3. **無破壞性**：啟用時若 disabled 目錄不存在檔案，從來源重新複製

## Error Handling

| 錯誤情況 | 處理方式 |
|----------|----------|
| 來源檔案不存在 | 顯示警告，跳過操作 |
| 權限不足 | 顯示錯誤訊息，建議使用者手動處理 |
| 目標已存在 | 覆蓋（啟用時）或跳過（停用時） |
| 移動中斷 | 先複製再刪除，確保完整性 |

## Testing Strategy

1. **單元測試**：
   - `disable_resource()` 正確移動檔案
   - `enable_resource()` 正確還原檔案
   - 權限錯誤時正確處理

2. **整合測試**：
   - CLI `toggle --disable` 完整流程
   - CLI `toggle --enable` 完整流程
   - TUI 停用/啟用流程

3. **手動驗證**：
   - 停用 skill 後，Claude Code 確實不載入
   - 啟用 skill 後，Claude Code 確實載入
