# Tasks: implement-profile-system

## 總覽

本任務清單實作完整的 Standards Profile 系統架構，取代 `fix-tui-detection-logic` 中的臨時方案。

**關鍵目標**：
1. 建立 `profiles/*.yaml` 定義檔案
2. 實作 profile 載入與解析邏輯
3. 更新 CLI 指令使用新的 profile 系統
4. 移除所有臨時方案註解與警告

---

## Phase 1: Profile 定義檔案建立

### Task 1.1: 建立 profiles 目錄結構

**位置**：`profiles/`

**工作內容**：
- 建立 `profiles/` 目錄
- 確認目錄權限正確

**驗收標準**：
- [ ] `profiles/` 目錄存在
- [ ] 目錄可讀寫

**預期變更檔案**：
- 新建目錄：`profiles/`

**依賴**：無

**狀態**：⏳ 待開始

---

### Task 1.2: 遷移 active-profile.yaml 到 profiles/active.yaml

**位置**：`profiles/active.yaml`（新位置）、`.standards/active-profile.yaml`（舊位置）

**工作內容**：
- 檢查 `.standards/active-profile.yaml` 是否存在
- 若存在，將其內容複製到 `profiles/active.yaml`
- 若不存在，建立 `profiles/active.yaml` 並設定預設值：
  ```yaml
  active: uds
  available:
    - uds
    - ecc
    - minimal
  last_updated: '<當前日期>'
  ```
- 保留舊檔案 `.standards/active-profile.yaml`（避免破壞現有功能，後續可由使用者手動刪除）

**驗收標準**：
- [ ] `profiles/active.yaml` 檔案已建立
- [ ] 檔案內容包含 `active`、`available`、`last_updated` 欄位
- [ ] 若舊檔案存在，內容已正確遷移

**預期變更檔案**：
- `profiles/active.yaml`（新建）

**依賴**：Task 1.1

**狀態**：⏳ 待開始

---

### Task 1.3: 建立 uds.yaml 定義檔案

**位置**：`profiles/uds.yaml`

**工作內容**：
- 建立 `uds.yaml` 定義檔案
- 定義欄位：
  - `name`: "uds"
  - `display_name`: "Universal Dev Standards"
  - `description`: 完整的 UDS 標準體系說明
  - `version`: "1.0.0"
  - `includes`: 列出所有 UDS 標準檔案
- 確認所有 `includes` 中的檔案在 `.standards/` 中存在

**驗收標準**：
- [ ] `uds.yaml` 檔案已建立
- [ ] YAML 語法正確（可用 `yaml.safe_load` 驗證）
- [ ] 所有 `includes` 檔案存在於 `.standards/`
- [ ] 檔案包含完整的 UDS 標準清單（至少 10+ 個標準）

**預期變更檔案**：
- `profiles/uds.yaml`（新建）

**依賴**：Task 1.1

**狀態**：⏳ 待開始

---

### Task 1.4: 建立 minimal.yaml 定義檔案

**位置**：`profiles/minimal.yaml`

**工作內容**：
- 建立 `minimal.yaml` 定義檔案
- 定義欄位：
  - `name`: "minimal"
  - `display_name`: "Minimal Standards"
  - `description`: 基礎標準體系說明
  - `version`: "1.0.0"
  - `includes`: 僅包含核心標準（3-5 個）
- 選擇核心標準：`checkin-standards.ai.yaml`, `testing.ai.yaml`, `commit-message.ai.yaml`

**驗收標準**：
- [ ] `minimal.yaml` 檔案已建立
- [ ] YAML 語法正確
- [ ] `includes` 僅包含核心標準（少於 uds）
- [ ] 所有 `includes` 檔案存在於 `.standards/`

**預期變更檔案**：
- `profiles/minimal.yaml`（新建）

**依賴**：Task 1.1

**狀態**：⏳ 待開始

---

### Task 1.5: 建立 ecc.yaml 定義檔案

**位置**：`profiles/ecc.yaml`

**工作內容**：
- 建立 `ecc.yaml` 定義檔案
- 定義欄位：
  - `name`: "ecc"
  - `display_name`: "Everything Claude Code"
  - `description`: ECC 標準體系說明
  - `version`: "1.0.0"
  - `inherits`: "minimal"（繼承 minimal profile）
  - `includes`: 額外包含的標準（在 minimal 基礎上）
  - `overrides`: 覆寫設定（例如：commit-message 語言設為英文）
- 設計合理的覆寫內容（可參考 proposal.md 範例）

**驗收標準**：
- [ ] `ecc.yaml` 檔案已建立
- [ ] YAML 語法正確
- [ ] `inherits` 欄位指向 "minimal"
- [ ] `includes` 包含額外的標準（如 `code-review.ai.yaml`）
- [ ] `overrides` 定義清晰（至少包含一個覆寫範例）

**預期變更檔案**：
- `profiles/ecc.yaml`（新建）

**依賴**：Task 1.1, Task 1.3（minimal 需先存在）

**狀態**：⏳ 待開始

---

## Phase 2: Profile 載入邏輯實作

### Task 2.1: 更新路徑函式與實作 load_profile()

**位置**：`script/commands/standards.py`

**工作內容**：
- **更新 `get_profiles_dir()` 函式**：
  - 改為返回 `get_project_root() / 'profiles'`（專案根目錄）
  - 而非 `get_standards_dir() / 'profiles'`（避免 .standards 目錄依賴）
- **更新 `get_active_profile_path()` 函式**：
  - 改為返回 `get_profiles_dir() / 'active.yaml'`
  - 而非 `get_standards_dir() / 'active-profile.yaml'`
- **新增 `load_profile(name: str) -> dict` 函式**：
  - 讀取 `profiles/{name}.yaml` 檔案
  - 解析 YAML 內容
  - 處理檔案不存在的錯誤（raise ValueError）
  - 返回 profile 字典

**驗收標準**：
- [ ] `get_profiles_dir()` 返回專案根目錄的 `profiles/` 路徑
- [ ] `get_active_profile_path()` 返回 `profiles/active.yaml` 路徑
- [ ] `load_profile("uds")` 成功返回 uds profile 字典
- [ ] `load_profile("invalid")` 拋出 ValueError
- [ ] 函式包含錯誤處理（檔案不存在、YAML 語法錯誤）
- [ ] 所有函式有清晰的 docstring

**預期變更檔案**：
- `script/commands/standards.py`

**依賴**：Phase 1 所有任務（profile 檔案需先存在）

**狀態**：⏳ 待開始

---

### Task 2.2: 實作 merge_profiles() 函式

**位置**：`script/commands/standards.py`

**工作內容**：
- 新增 `merge_profiles(parent: dict, child: dict) -> dict` 函式
- 合併父子 profile 的 `includes` 欄位（追加，不覆蓋）
- 合併父子 profile 的 `overrides` 欄位（子覆蓋父）
- 更新基本資訊欄位（name, display_name 等使用子 profile 的值）
- 返回合併後的 profile 字典

**驗收標準**：
- [ ] 合併後的 `includes` 包含父子兩個 profile 的所有項目
- [ ] 合併後的 `overrides` 正確覆蓋（子優先）
- [ ] 基本資訊欄位使用子 profile 的值
- [ ] 函式有清晰的 docstring 與範例

**預期變更檔案**：
- `script/commands/standards.py`

**依賴**：無（獨立函式）

**狀態**：⏳ 待開始

---

### Task 2.3: 更新 load_profile() 處理繼承

**位置**：`script/commands/standards.py`

**工作內容**：
- 在 `load_profile()` 中檢查 `inherits` 欄位
- 若存在 `inherits`，遞迴呼叫 `load_profile(inherits)` 載入父 profile
- 使用 `merge_profiles()` 合併父子 profile
- 處理循環繼承錯誤（A inherits B, B inherits A）
- 返回合併後的 profile

**驗收標準**：
- [ ] `load_profile("ecc")` 正確載入並合併 minimal profile
- [ ] 合併後的 profile 包含 minimal 的所有 `includes`
- [ ] 循環繼承檢測正常（拋出錯誤並提示）
- [ ] 函式有清晰的繼承處理註解

**預期變更檔案**：
- `script/commands/standards.py`

**依賴**：Task 2.1, Task 2.2

**狀態**：⏳ 待開始

---

## Phase 3: CLI 指令更新

### Task 3.1: 更新 list_profiles() 函式

**位置**：`script/commands/standards.py`

**工作內容**：
- 移除「臨時方案」註解
- 移除從 `profiles/active.yaml` 的 `available` 欄位讀取的邏輯
- 改為掃描 `profiles/` 目錄，返回所有 `.yaml` 檔案的名稱（去掉副檔名）
- 處理目錄不存在的情況（返回空列表）

**驗收標準**：
- [ ] `list_profiles()` 返回 `['ecc', 'minimal', 'uds']`（按字母排序）
- [ ] 目錄不存在時返回空列表（不拋出錯誤）
- [ ] 移除所有「TODO: Phase 2」註解
- [ ] 函式 docstring 已更新

**預期變更檔案**：
- `script/commands/standards.py`

**依賴**：Phase 1, Task 2.1

**狀態**：⏳ 待開始

---

### Task 3.2: 重構 show() 命令

**位置**：`script/commands/standards.py`

**工作內容**：
- 移除「臨時清單模式」警告訊息
- 使用 `load_profile(profile_name)` 載入 profile
- 顯示完整資訊：
  - `display_name` 與 `description`
  - `version`
  - `inherits`（若有）
  - `includes` 清單
  - `overrides`（若有，使用 `console.print_json` 美化輸出）
- 處理 profile 不存在的錯誤

**驗收標準**：
- [ ] `ai-dev standards show uds` 顯示完整的 uds profile 資訊
- [ ] `ai-dev standards show ecc` 正確顯示 `inherits: minimal`
- [ ] `ai-dev standards show minimal` 正確顯示（無 inherits）
- [ ] 顯示格式清晰美觀（使用 Rich 排版）
- [ ] 移除所有「臨時」警告訊息

**預期變更檔案**：
- `script/commands/standards.py`

**依賴**：Task 2.3（需要 load_profile 支援繼承）

**狀態**：⏳ 待開始

---

### Task 3.3: 更新 status() 命令

**位置**：`script/commands/standards.py`

**工作內容**：
- 移除「Profile 切換目前為臨時功能」警告訊息
- 保持原有功能：顯示目前啟用的 profile 與可用 profiles
- 可選：增加顯示目前 profile 的簡短描述

**驗收標準**：
- [ ] `ai-dev standards status` 正確顯示目前啟用的 profile
- [ ] 移除臨時功能警告
- [ ] 顯示格式清晰

**預期變更檔案**：
- `script/commands/standards.py`

**依賴**：Task 3.1

**狀態**：⏳ 待開始

---

### Task 3.4: 更新 list() 命令

**位置**：`script/commands/standards.py`

**工作內容**：
- 移除表格標題中的「(臨時清單模式)」字樣
- 移除「Profile 切換目前為臨時功能」警告訊息
- 保持原有功能：列出所有可用 profiles 並標示啟用狀態
- 可選：增加顯示每個 profile 的簡短描述

**驗收標準**：
- [ ] `ai-dev standards list` 正確列出所有 profiles
- [ ] 表格標題為「可用的 Standards Profiles」（移除「臨時清單模式」）
- [ ] 移除警告訊息
- [ ] 顯示格式清晰

**預期變更檔案**：
- `script/commands/standards.py`

**依賴**：Task 3.1

**狀態**：⏳ 待開始

---

### Task 3.5: 更新 switch() 命令（可選）

**位置**：`script/commands/standards.py`

**工作內容**：
- 移除「當前為臨時實作，切換不會載入不同標準」警告訊息
- 保持原有功能：更新 `profiles/active.yaml` 的 `active` 欄位
- 可選：新增提示訊息說明當前實作範圍（定義已切換，實際標準載入將在未來版本提供）

**驗收標準**：
- [ ] `ai-dev standards switch ecc` 正確切換 profile
- [ ] 移除「臨時實作」警告
- [ ] 可選：新增清晰的提示訊息（說明當前範圍）

**預期變更檔案**：
- `script/commands/standards.py`

**依賴**：Task 3.1

**狀態**：⏳ 待開始

---

## Phase 4: TUI 更新（若需要）

### Task 4.1: 驗證 TUI Profile 選單

**位置**：`script/tui/app.py`

**工作內容**：
- 驗證 TUI 的 `update_standards_profile_display()` 使用更新後的 `list_profiles()`
- 確認 TUI Profile 選單正確載入 profiles（從 `profiles/*.yaml`）
- 測試 Profile 切換功能（下拉選單與快捷鍵 `t`）
- 確認無需修改（因為 TUI 使用 `list_profiles()` 函式，已自動更新）

**驗收標準**：
- [ ] TUI Profile 選單顯示三個 profiles（uds, ecc, minimal）
- [ ] Profile 切換功能正常運作
- [ ] 無錯誤或警告訊息

**預期變更檔案**：
- 無（僅驗證，不修改）或 `script/tui/app.py`（若需調整）

**依賴**：Task 3.1

**狀態**：⏳ 待開始

---

## Phase 5: 文件與清理

### Task 5.1: 移除程式碼中的臨時註解

**位置**：`script/commands/standards.py`

**工作內容**：
- 搜尋並移除所有「TODO: Phase 2」、「臨時方案」、「臨時實作」等註解
- 確認程式碼註解清晰，說明新的 profile 載入邏輯
- 更新 docstring 反映新的實作方式

**驗收標準**：
- [ ] `grep -r "TODO: Phase 2" script/commands/standards.py` 無結果
- [ ] `grep -r "臨時" script/commands/standards.py` 無結果（除非是合理的描述性文字）
- [ ] 所有函式有清晰的 docstring

**預期變更檔案**：
- `script/commands/standards.py`

**依賴**：Phase 3 所有任務

**狀態**：⏳ 待開始

---

### Task 5.2: 更新 README.md

**位置**：`README.md`

**工作內容**：
- 搜尋 Profile 相關章節
- 移除「已知限制」警告（「Profile 切換目前為臨時功能」等）
- 更新說明文字反映新的實作（Profile 定義檔案已建立）
- 可選：新增「Profile 定義檔案格式」說明章節

**驗收標準**：
- [ ] README.md 不再包含「臨時功能」、「已知限制」等警告
- [ ] Profile 功能說明清晰準確
- [ ] 可選：包含 profile 定義檔案格式範例

**預期變更檔案**：
- `README.md`

**依賴**：Phase 3 所有任務

**狀態**：⏳ 待開始

---

### Task 5.3: 更新 CHANGELOG.md

**位置**：`CHANGELOG.md`

**工作內容**：
- 在 `[Unreleased]` 區段新增變更條目
- 分類為 **Added**（新增功能）與 **Changed**（變更）
- 記錄：
  - **Added**: Profile 定義檔案系統（uds.yaml, ecc.yaml, minimal.yaml）
  - **Added**: Profile 繼承與覆寫機制
  - **Changed**: `ai-dev standards` 命令改為從 `profiles/*.yaml` 讀取
  - **Changed**: 移除所有臨時方案註解與警告
- 移除 **Known Limitation** 區段中關於 Profile 的限制（或更新為新的範圍說明）

**驗收標準**：
- [ ] CHANGELOG.md 包含清晰的變更記錄
- [ ] 分類正確（Added/Changed）
- [ ] 移除或更新已知限制章節

**預期變更檔案**：
- `CHANGELOG.md`

**依賴**：Phase 3 所有任務

**狀態**：⏳ 待開始

---

## Phase 6: 測試與驗證

### Task 6.1: CLI 指令手動測試

**工作內容**：
- 在已初始化專案中測試：
  - [ ] `ai-dev standards list` 列出三個 profiles
  - [ ] `ai-dev standards status` 顯示目前啟用的 profile
  - [ ] `ai-dev standards show uds` 顯示完整資訊
  - [ ] `ai-dev standards show ecc` 顯示繼承關係
  - [ ] `ai-dev standards show minimal` 顯示基礎資訊
  - [ ] `ai-dev standards switch ecc` 切換成功
  - [ ] `ai-dev standards switch invalid` 顯示錯誤訊息
- 在未初始化專案中測試：
  - [ ] `ai-dev standards list` 顯示未初始化提示

**依賴**：Phase 3 所有任務

**狀態**：⏳ 待開始

---

### Task 6.2: TUI 手動測試

**工作內容**：
- 啟動 TUI (`ai-dev tui`)
- 測試 Standards Profile 區塊：
  - [ ] Profile 選單顯示三個 profiles
  - [ ] 下拉選單切換功能正常
  - [ ] 快捷鍵 `t` 循環切換正常
  - [ ] 無臨時功能警告訊息

**依賴**：Task 4.1

**狀態**：⏳ 待開始

---

### Task 6.3: Profile 繼承驗證

**工作內容**：
- 驗證 `ecc` profile 正確繼承 `minimal`：
  - [ ] `load_profile("ecc")` 返回的 `includes` 包含 minimal 的所有項目
  - [ ] `load_profile("ecc")` 返回的 `includes` 包含 ecc 額外的項目
  - [ ] `load_profile("ecc")` 返回的 `overrides` 正確設定
- 驗證 `show ecc` 顯示繼承資訊：
  - [ ] 顯示 `Inherits: minimal`

**依賴**：Task 2.3, Task 3.2

**狀態**：⏳ 待開始

---

## 總結

### 任務統計

- **Phase 1**：5 個任務（Profile 定義檔案建立與遷移）
- **Phase 2**：3 個任務（Profile 載入邏輯實作）
- **Phase 3**：5 個任務（CLI 指令更新）
- **Phase 4**：1 個任務（TUI 驗證）
- **Phase 5**：3 個任務（文件與清理）
- **Phase 6**：3 個任務（測試與驗證）
- **總計**：20 個任務

### 實際變更檔案

- `profiles/` 目錄（新建，專案根目錄）
- `profiles/active.yaml`（新建，從 `.standards/active-profile.yaml` 遷移）
- `profiles/uds.yaml`（新建）
- `profiles/ecc.yaml`（新建）
- `profiles/minimal.yaml`（新建）
- `script/commands/standards.py`（重構，更新所有路徑參考）
- `script/tui/app.py`（可能需要微調）
- `README.md`（更新）
- `CHANGELOG.md`（更新）

### 關鍵依賴關係

```
Phase 1 (所有任務) → Phase 2, Phase 3
Task 2.1, 2.2 → Task 2.3
Phase 2 (所有任務) → Phase 3
Phase 3 (所有任務) → Phase 4, Phase 5, Phase 6
```

### 並行機會

- Task 1.2, 1.3, 1.4 可以並行執行（獨立的 profile 檔案）
- Task 2.1, 2.2 可以並行執行（獨立函式）
- Task 3.1, 3.3, 3.4, 3.5 可以部分並行（CLI 指令獨立）
- Phase 5 與 Phase 6 可以部分並行（文件更新與測試）

### 風險項目

- ⚠️ Task 2.3：繼承邏輯需仔細處理循環依賴
- ⚠️ Task 6.3：繼承驗證需確保 merge 邏輯正確
- ⚠️ Phase 6：手動測試需覆蓋所有情境

### 成功標準總覽

- [ ] 所有 19 個任務完成
- [ ] CLI 指令 (`list`, `show`, `status`, `switch`) 正常運作
- [ ] TUI Profile 選單正常運作
- [ ] 程式碼無「臨時」、「TODO: Phase 2」註解
- [ ] 文件更新完整，無誤導性警告
- [ ] 所有手動測試通過
