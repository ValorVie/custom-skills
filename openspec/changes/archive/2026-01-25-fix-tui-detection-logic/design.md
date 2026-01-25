# Design: fix-tui-detection-logic

## Architecture

本變更聚焦於 TUI 的偵測與顯示邏輯，採用**臨時修正方案**快速解決當前 bug。

**設計原則**：
1. **最小變更**：只修復偵測邏輯，不擴展功能
2. **向前相容**：確保未來可擴展為完整 Profile 架構
3. **清晰註記**：在程式碼與文件中明確標註臨時性質

### 系統邊界

**在範圍內**：
- `script/tui/app.py` - TUI 主程式
- `script/commands/standards.py` - Standards Profile 相關函式

**在範圍外**：
- `script/commands/hooks.py` - CLI hooks 指令（保持不變）
- `script/utils/shared.py` - 共用工具函式（`get_ecc_hooks_status` 等，保持不變）
- Profile 資料格式與儲存位置

## Component Design

### 1. ECC Hooks Plugin 區塊重構

**目前架構** [Source: Code] `script/tui/app.py:253-261, 621-686`:
```
┌─────────────────────────────┐
│  ECC Hooks Plugin 區塊      │
├─────────────────────────────┤
│  狀態標籤                    │
│  [Install/Update] 按鈕      │
│  [Uninstall] 按鈕           │
│  [View Config] 按鈕         │
└─────────────────────────────┘
```

**新架構**：
```
┌─────────────────────────────┐
│  ECC Hooks Plugin 區塊      │
├─────────────────────────────┤
│  ✓ 已安裝 at ~/.claude/... │
│  或                          │
│  ✗ 未安裝                   │
│  安裝提示：npx skills add...│
│  [View Config] 按鈕（已安裝時）│
└─────────────────────────────┘
```

**變更細節**：
1. **移除元件**：
   - `Button("Install/Update", id="btn-hooks-install")`
   - `Button("Uninstall", id="btn-hooks-uninstall")`
   - Binding `i` (install_hooks)
   - Binding `u` (uninstall_hooks)
   - `action_install_hooks()` 方法
   - `action_uninstall_hooks()` 方法

2. **保留元件**：
   - 狀態標籤 (`hooks-status-label`)
   - View Config 按鈕（僅在已安裝時顯示）
   - Binding `v` (view_hooks_config)
   - `action_view_hooks_config()` 方法
   - `update_hooks_status_display()` 方法

3. **新增元件**：
   - 安裝提示標籤 (`hooks-install-hint`)：顯示 `npx skills add` 指令

**資料流程**：
```
get_ecc_hooks_status() (unchanged)
         ↓
update_hooks_status_display()
         ↓
更新 hooks-status-label
         ↓
條件顯示 View Config 按鈕
         ↓
顯示/隱藏安裝提示
```

### 2. Standards Profile 偵測邏輯重構（臨時方案）

**目前邏輯問題** [Source: Code] `script/tui/app.py:509-514`:
```python
# 錯誤：檢查尚未實作的 profiles/ 目錄
if not profiles_dir.exists():
    # 顯示「未初始化」
```

**新邏輯架構**（簡化清單模式）：
```
檢查專案初始化狀態
    ↓
┌─────────────────────────────┐
│ .standards/ 存在？           │
│ active-profile.yaml 存在？   │
└──┬────────────────────┬─────┘
   │ No                 │ Yes
   ↓                    ↓
未初始化         讀取 active-profile.yaml
   ↓                    ↓
顯示提示         available: [uds, ecc, minimal]
                         ↓
                   顯示 profiles 清單
```

**實作策略 - 清單模式（臨時）**：

1. **初始化檢查函式**（新增）：
   ```python
   def is_standards_initialized() -> bool:
       """檢查專案是否已初始化標準體系"""
       standards_dir = get_standards_dir()
       active_file = get_active_profile_path()
       return standards_dir.exists() and active_file.exists()
   ```

2. **Profile 來源函式重構**（簡化）：
   ```python
   def list_profiles() -> list[str]:
       """列出可用 profiles（從 active-profile.yaml 讀取）

       TODO: Phase 2 應改為讀取 profiles/*.yaml 檔案
       """
       active_config = load_yaml(get_active_profile_path())
       return active_config.get('available', [])
   ```

**邊界條件處理**：

| 情境 | `.standards/` | `active-profile.yaml` | 行為 |
|------|---------------|----------------------|------|
| 未初始化 | ✗ | ✗ | 顯示「未初始化」提示 |
| 已初始化 | ✓ | ✓ | 從 YAML 讀取 available 清單 |
| 損壞狀態 | ✓ | ✗ | 顯示「未初始化」提示 |
| 空清單 | ✓ | ✓ (available: []) | 顯示「無可用 profile」 |

**重要限制**：
- ⚠️ Profile 切換不會載入不同標準（所有 profiles 使用相同 UDS 標準）
- ⚠️ 不讀取 `profiles/*.yaml` 檔案（即使存在）
- ⚠️ 完整實作留待 Phase 2

## Data Flow

### ECC Hooks Plugin 狀態更新流程

```
使用者啟動 TUI
    ↓
on_mount()
    ↓
update_hooks_status_display()
    ↓
get_ecc_hooks_status()  ← 從 shared.py（不變）
    ↓
    ├─ installed: true/false
    ├─ plugin_path: Path
    └─ hooks_json_path: Path | None
    ↓
更新 UI 元件：
    ├─ hooks-status-label: "✓ 已安裝" / "✗ 未安裝"
    ├─ hooks-install-hint: 顯示/隱藏
    └─ btn-hooks-view: 顯示/隱藏
```

### Standards Profile 載入流程

```
使用者啟動 TUI
    ↓
on_mount()
    ↓
update_standards_profile_display()
    ↓
is_standards_initialized() ← 新函式
    ↓
    ├─ False → 顯示「未初始化」
    └─ True
        ↓
    list_profiles() ← 重構函式
        ↓
        ├─ profiles/*.yaml 存在 → 回傳檔案清單
        └─ 否則 → 從 active-profile.yaml 讀取
        ↓
    get_active_profile() ← 不變
        ↓
    更新 UI：
        ├─ profile-select: 設定選項
        ├─ profile-select.value: 目前啟用
        └─ profile-info-label: 顯示資訊
```

### Profile 切換流程（不變）

```
使用者選擇新 profile
    ↓
on_select_changed()
    ↓
switch_standards_profile()
    ↓
更新 active-profile.yaml
    ↓
重新整理 UI
```

## Error Handling

### ECC Hooks Plugin 錯誤處理

1. **狀態讀取失敗**：
   ```python
   try:
       status = get_ecc_hooks_status()
   except Exception as e:
       console.print(f"[red]無法讀取 Hooks 狀態：{e}[/red]")
       # 顯示預設「未知」狀態
   ```

2. **View Config 失敗**：
   ```python
   # 保持既有處理邏輯（script/tui/app.py:670-686）
   if not status["installed"]:
       self.notify("Hooks plugin is not installed", severity="warning")
       return
   ```

### Standards Profile 錯誤處理

1. **YAML 解析失敗**：
   ```python
   def load_yaml(path: Path) -> dict:
       try:
           with open(path, 'r', encoding='utf-8') as f:
               return yaml.safe_load(f) or {}
       except Exception:
           return {}  # 回傳空字典，由呼叫端處理
   ```

2. **Profile 不存在**：
   ```python
   profiles = list_profiles()
   if not profiles:
       # 顯示「無可用 profile」訊息
       profile_select.set_options([("無可用 profile", "none")])
   ```

3. **Active profile 無效**：
   ```python
   active = get_active_profile()
   if active not in profiles:
       # 回退至第一個可用 profile
       profile_select.value = profiles[0]
   ```

## Testing Strategy

### 單元測試範圍

由於 TUI 的互動性，主要依賴手動測試，但以下邏輯函式應有單元測試：

1. **`is_standards_initialized()`**：
   - 測試案例：目錄不存在
   - 測試案例：目錄存在但無 active-profile.yaml
   - 測試案例：完整初始化

2. **`list_profiles()` 重構版本**：
   - 測試案例：只有 active-profile.yaml（清單模式）
   - 測試案例：只有 profiles/*.yaml（檔案模式）
   - 測試案例：兩者都存在（應優先檔案模式）
   - 測試案例：兩者都不存在（回傳空列表）

### 整合測試檢查點

1. **ECC Hooks 顯示**：
   - [ ] 未安裝時：顯示「✗ 未安裝」+ 安裝提示
   - [ ] 已安裝時：顯示「✓ 已安裝」+ 路徑 + View Config 按鈕
   - [ ] View Config 按鈕僅在已安裝時可用
   - [ ] 安裝/移除按鈕已移除
   - [ ] 快捷鍵 `i` 和 `u` 已移除

2. **Standards Profile 偵測**：
   - [ ] 簡單模式（只有 active-profile.yaml）：正確讀取 profiles
   - [ ] 進階模式（有 profiles/ 目錄）：優先使用檔案
   - [ ] 未初始化狀態：顯示提示訊息
   - [ ] Profile 切換功能正常
   - [ ] 快捷鍵 `t` 循環切換正常

## Migration Notes

### 使用者影響

1. **TUI 安裝功能移除**：
   - 原有透過 TUI 安裝 hooks 的使用者需改用 CLI 或 `npx skills add`
   - 影響範圍：小（預期少數使用者依賴此功能）

2. **CLI 指令保留**：
   - `ai-dev hooks install` 仍然可用
   - 進階使用者與腳本不受影響

### 開發者注意事項

1. **Standards Profile 邏輯變更**：
   - 未來新增 profile 管理功能應使用 `list_profiles()` 函式
   - 該函式已支援兩種模式，無需額外處理

2. **TUI 按鈕 ID 變更**：
   - 移除 `btn-hooks-install` 和 `btn-hooks-uninstall`
   - CSS 樣式與測試腳本可能需要更新

## Implementation Order

1. **階段 1：Standards Profile 邏輯修正** (獨立可測試)
   - 實作 `is_standards_initialized()`
   - 重構 `list_profiles()` 支援兩種模式
   - 更新 `update_standards_profile_display()`
   - 手動測試驗證

2. **階段 2：ECC Hooks UI 簡化** (獨立可測試)
   - 移除安裝/移除按鈕與方法
   - 更新 `update_hooks_status_display()` 顯示邏輯
   - 新增安裝提示標籤
   - 更新 CSS 樣式
   - 手動測試驗證

3. **階段 3：整合測試與文件更新**
   - 完整 TUI 流程測試
   - 更新 README 或使用指南
   - 更新 CHANGELOG

## Alternative Designs Considered

### 選項 A：完全移除 ECC Hooks 區塊

**優點**：
- 更簡潔的 TUI
- 減少維護負擔

**缺點**：
- 失去可見性（使用者不知道 hooks 狀態）
- 需要文件說明如何檢查狀態

**決策**：❌ 不採用。保留狀態顯示有助於除錯與使用者理解。

### 選項 B：實作完整 Profile 架構

**優點**：
- 符合原始設計意圖
- 真正實現 UDS/ECC/Minimal 切換
- 長期正確

**缺點**：
- 工作量大（建立 profile 定義檔案、整合 ECC 標準）
- 涉及更多模組變更
- 風險較高

**決策**：❌ 不在本提案範圍。留待 Phase 2 實作。

### 選項 C：臨時修正 + 明確標註（採用方案）

**優點**：✅
- 快速修復當前 bug
- 最小變更，風險低
- 保留正確的長期方向
- 使用者體驗立即改善

**缺點**：
- Profile 切換功能無實質作用（需文件說明）
- 技術債累積（需未來重構）

**決策**：✅ **採用**。階段式實作，先修復再擴展。
