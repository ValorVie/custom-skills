# standards-profile-detection Specification Delta

**重要說明**：本 spec delta 為**臨時修正方案**，採用簡化的清單模式。完整 Profile 架構（包含 `profiles/*.yaml` 定義檔案）留待 Phase 2 實作。

## MODIFIED Requirements

### Requirement: Standards Profile Initialization Detection (Standards Profile 初始化偵測)

TUI MUST (必須) 正確偵測專案是否已初始化標準體系。

**變更理由**：
1. 原邏輯依賴 `.standards/profiles/` 目錄，但該功能尚未完成實作
2. 當前專案使用 `active-profile.yaml` 的 `available` 欄位儲存 profiles 清單
3. 臨時方案：繞過對 `profiles/` 目錄的依賴，改從 `active-profile.yaml` 讀取

#### Scenario: 偵測已初始化專案

給定專案已執行 `ai-dev project init`
當 `.standards/` 目錄存在
且 `.standards/active-profile.yaml` 檔案存在
則 TUI 應該識別為「已初始化」狀態
且從 `active-profile.yaml` 的 `available` 欄位讀取 profiles 清單

#### Scenario: 偵測未初始化專案

給定專案未執行 `ai-dev project init`
當 `.standards/` 目錄不存在
或 `.standards/active-profile.yaml` 檔案不存在
則 TUI Standards Profile 區塊應該顯示：
- 「未初始化」狀態提示
- 「執行 `ai-dev project init` 初始化」建議

### Requirement: Profile List from YAML (從 YAML 讀取 Profile 清單) - 臨時實作

Standards Profile 管理功能 MUST (必須) 從 `active-profile.yaml` 讀取 profiles 清單。

**變更理由**：採用臨時修正方案，繞過對未實作的 `profiles/` 目錄的依賴。

**已知限制**：Profile 切換不會載入不同標準（所有 profiles 使用相同的 UDS 標準）。

#### Scenario: 從 active-profile.yaml 讀取清單

給定 `.standards/active-profile.yaml` 存在
當系統需要列出可用 profiles 時
則應該讀取 `active-profile.yaml` 的 `available` 欄位
且回傳該欄位的值（字串陣列）

#### Scenario: 空狀態處理

給定 `.standards/active-profile.yaml` 的 `available` 欄位不存在或為空陣列
當系統需要列出可用 profiles 時
則應該回傳空列表
且 TUI 顯示「無可用 profile」訊息

#### Scenario: Profile 切換無實質作用（已知限制）

給定使用者切換到不同的 profile（如從 `uds` 切換到 `ecc`）
當切換完成時
則應該：
- 更新 `active-profile.yaml` 的 `active` 欄位
- ⚠️ **不會**載入不同的標準檔案（所有 profiles 使用相同標準）
- ⚠️ 使用者應理解此為臨時限制

## ADDED Requirements

### Requirement: Standards Initialization Check Function (Standards 初始化檢查函式)

CLI 與 TUI MUST (必須) 提供統一的函式來檢查專案是否已初始化標準體系。

#### Scenario: 提供 `is_standards_initialized()` 函式

給定任何需要檢查初始化狀態的程式碼
當呼叫 `is_standards_initialized()` 函式時
則應該：
1. 檢查 `.standards/` 目錄是否存在
2. 檢查 `.standards/active-profile.yaml` 是否存在
3. 回傳布林值：兩個條件都滿足時為 `True`，否則為 `False`

### Requirement: Simplified Profile Listing Function (簡化 Profile 列表函式) - 臨時實作

`list_profiles()` 函式 MUST (必須) 從 `active-profile.yaml` 讀取 profiles 清單。

**重要**：函式應包含 TODO 註解，標註 Phase 2 應改為讀取 `profiles/*.yaml` 檔案。

#### Scenario: 函式回傳型別一致性

給定任何呼叫 `list_profiles()` 的程式碼
當函式執行完成時
則應該：
- 回傳型別為 `list[str]`（profile 名稱清單）
- 若無可用 profile，回傳空列表 `[]`
- 包含 TODO 註解說明未來方向

## Impact

### 對現有功能的影響

1. **`list_profiles()` 函式行為變更**（臨時）：
   - 原本：檢查 `profiles/*.yaml` 檔案（依賴未實作功能）
   - 修改後：只讀取 `active-profile.yaml.available` 欄位
   - 影響範圍：所有呼叫此函式的程式碼（CLI, TUI）

2. **新增函式**：
   - `is_standards_initialized()` - 新增公開函式
   - 可被其他模組匯入與使用

3. **TUI 顯示邏輯**：
   - `update_standards_profile_display()` 判斷邏輯修正
   - 已初始化專案不再誤顯示「未初始化」訊息

4. **Profile 切換功能**：
   - ⚠️ 切換 profile 不會載入不同標準（所有 profiles 使用相同 UDS 標準）
   - ⚠️ 這是已知限制，需在文件中說明

### 向後相容性

- **非破壞性變更**：修復 bug，不移除既有支援
- **現有專案影響**：
  - 所有專案均使用 `active-profile.yaml` 清單模式
  - Profile 切換功能已存在但無實質作用（修正後仍相同）

### 相關 Capabilities

- 與 `standards-profiles` spec 緊密相關（定義 profiles 的核心概念）
- 與 `tui-standards-profile` spec 相關（定義 TUI 顯示行為）
- **重要**：本變更為臨時方案，完整實作需等待 Phase 2 提案（建立 `profiles/` 目錄與實作標準來源切換）

## Edge Cases

### Case 1: 損壞的 active-profile.yaml

**情境**：`.standards/active-profile.yaml` 存在但無法解析（YAML 語法錯誤）

**預期行為**：
- `is_standards_initialized()` 回傳 `True`（檔案存在）
- `list_profiles()` 回傳空列表（解析失敗時的安全回退）
- TUI 顯示「無可用 profile」訊息

### Case 2: available 欄位格式錯誤

**情境**：`.standards/active-profile.yaml` 的 `available` 欄位不是陣列（如字串或數字）

**預期行為**：
- `list_profiles()` 回傳空列表
- TUI 顯示「無可用 profile」訊息

### Case 3: Active profile 不在可用列表中

**情境**：`active-profile.yaml` 的 `active` 欄位指向不存在的 profile

**預期行為**：
- TUI 回退至第一個可用 profile
- 不顯示錯誤訊息（靜默修正）

## Testing Guidance

### 測試矩陣（臨時方案）

| `.standards/` | `active-profile.yaml` | `available` 欄位 | 預期行為 |
|---------------|----------------------|----------------|----------|
| ✗ | ✗ | - | 未初始化 |
| ✓ | ✗ | - | 未初始化 |
| ✓ | ✓ | ✓ | 已初始化（顯示清單） |
| ✓ | ✓ | ✗ 或空陣列 | 已初始化（無可用 profile） |

### 單元測試建議

1. **`is_standards_initialized()` 測試**：
   - 測試目錄不存在情境
   - 測試檔案不存在情境
   - 測試完整初始化情境

2. **`list_profiles()` 測試**：
   - 測試檔案模式
   - 測試清單模式
   - 測試兩者都存在（驗證優先順序）
   - 測試兩者都不存在（驗證空列表回傳）
   - 測試 YAML 解析失敗情境

### 整合測試建議（臨時方案）

1. 在已初始化專案中執行 TUI，驗證正確顯示 profiles
2. 測試 Profile 切換功能（雖然無實質作用，但 UI 應正常）
3. 驗證「未初始化」提示不再誤顯示
4. 驗證 CLI 指令（`ai-dev standards list/status/switch`）正常運作
