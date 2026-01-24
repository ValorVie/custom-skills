# Design: align-tui-with-cli

## 架構決策

### 1. Clone 按鈕整合

#### 方案 A：直接呼叫 CLI 指令（選用）
```python
def on_button_pressed(self, event: Button.Pressed) -> None:
    if button_id == "btn-clone":
        self.run_cli_command("clone", self._get_sync_project_args())
```

**優點**：
- 與現有 Install/Update 按鈕實作一致
- 複用現有 `run_cli_command()` 方法

**缺點**：
- 需要暫停 TUI 執行外部指令

#### 方案 B：直接呼叫 Python 函式
```python
from ..utils.shared import copy_skills

def on_button_pressed(self, event: Button.Pressed) -> None:
    if button_id == "btn-clone":
        copy_skills(sync_project=self._get_sync_project_value())
        self.notify("Clone completed!")
        self.refresh_resource_list()
```

**優點**：
- 不需暫停 TUI
- 更流暢的使用者體驗

**缺點**：
- 需要處理錯誤顯示
- 與其他按鈕行為不一致

**決策**：採用方案 A，保持與現有按鈕行為一致。

---

### 2. Standards Profile 區塊位置

```
┌─────────────────────────────────────────┐
│ Header                                  │
├─────────────────────────────────────────┤
│ [Install] [Update] [Clone] [Status] ... │
├─────────────────────────────────────────┤
│ Target: [Claude Code ▼] Type: [Skills ▼]│
│ [✓] Sync to Project                     │
├─────────────────────────────────────────┤
│ ┌─────────────────────────────────────┐ │
│ │ □ skill-1 (uds)                     │ │
│ │ □ skill-2 (obsidian)                │ │
│ │ ...                                 │ │
│ └─────────────────────────────────────┘ │
├─────────────────────────────────────────┤
│ Standards Profile                       │  ← 新增區塊
│ Profile: [uds ▼] (2/3 standards)        │
├─────────────────────────────────────────┤
│ MCP Config                              │
│ Path: ~/.claude.json ✓                  │
│ [Open in Editor] [Open Folder]          │
├─────────────────────────────────────────┤
│ Footer (keybindings)                    │
└─────────────────────────────────────────┘
```

**決策**：Standards Profile 區塊放在 MCP Config 上方，因為：
1. 邏輯分組：資源管理 → 標準配置 → 工具配置
2. 使用頻率：標準切換比 MCP 編輯更常用

---

### 3. 快捷鍵分配

| 按鍵 | 功能 | 備註 |
|------|------|------|
| `c` | Clone | 新增 |
| `t` | 切換 Standards Profile | 新增 |
| `e` | Open MCP in Editor | 已有 |
| `f` | Open MCP Folder | 已有 |
| `p` | Add Package | 已有 |
| `s` | Save | 已有 |
| `a` | Select All | 已有 |
| `n` | Select None | 已有 |
| `q` | Quit | 已有 |

---

## 實作順序

1. **Phase 1**：Clone 按鈕（低風險，獨立功能）
2. **Phase 2**：Standards Profile 區塊（需要新增 UI 組件）
3. **Phase 3**：更新文件和規格

---

## 相依模組

```
script/tui/app.py
├── script/commands/clone.py      # Clone 邏輯
├── script/commands/standards.py  # Standards 邏輯
└── script/utils/shared.py        # 共用工具
```

---

## 測試考量

### 手動測試
1. 啟動 TUI 並點擊 Clone 按鈕
2. 驗證 Skills 分發正確
3. 切換 Standards Profile
4. 驗證 `.standards/active-profile.yaml` 更新

### 邊界情況
- `.standards/profiles/` 目錄不存在
- 只有一個 profile 可用（循環切換邏輯）
- Clone 執行時發生錯誤
