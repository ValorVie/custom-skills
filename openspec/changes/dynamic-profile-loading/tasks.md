# Tasks: dynamic-profile-loading

## 總覽

本任務清單實作動態 Profile 載入功能，讓切換 Profile 時實際改變 `.standards/` 中的標準內容。

**前置條件**：`implement-profile-system` 提案必須先完成。

**關鍵目標**：
1. 建立 `profiles/standards/` 標準檔案庫
2. 實作 `activate_profile()` 動態載入函式
3. 更新 `switch` 命令觸發動態載入
4. 實作安全機制（追蹤、保護、同步）

---

## Phase 1: 標準檔案庫建立

### Task 1.1: 建立 profiles/standards/ 目錄結構

**位置**：`profiles/standards/`

**工作內容**：
- 建立 `profiles/standards/` 目錄
- 建立子目錄：`uds/`, `ecc/`, `minimal/`, `shared/`
- 確認目錄權限正確

**驗收標準**：
- [ ] `profiles/standards/` 目錄存在
- [ ] `profiles/standards/uds/` 目錄存在
- [ ] `profiles/standards/ecc/` 目錄存在
- [ ] `profiles/standards/minimal/` 目錄存在
- [ ] `profiles/standards/shared/` 目錄存在

**預期變更檔案**：
- 新建目錄：`profiles/standards/` 及其子目錄

**依賴**：`implement-profile-system` 完成

**狀態**：⏳ 待開始

---

### Task 1.2: 準備 UDS 標準檔案

**位置**：`profiles/standards/uds/`

**工作內容**：
- 複製現有 `.standards/` 中的所有 `.ai.yaml` 和 `.md` 標準檔案到 `profiles/standards/uds/`
- 確保檔案列表與 `profiles/uds.yaml` 的 `includes` 一致
- 不複製 `manifest.json`、`active-profile.yaml`、`options/` 等非標準檔案

**驗收標準**：
- [ ] UDS 目錄包含所有 `profiles/uds.yaml` 的 `includes` 檔案
- [ ] 檔案內容與現有 `.standards/` 一致
- [ ] 至少 10+ 個標準檔案

**預期變更檔案**：
- `profiles/standards/uds/*.ai.yaml`（新建，多個檔案）
- `profiles/standards/uds/*.md`（新建，若有）

**依賴**：Task 1.1

**狀態**：⏳ 待開始

---

### Task 1.3: 準備 Minimal 標準檔案

**位置**：`profiles/standards/minimal/`

**工作內容**：
- 從 `profiles/standards/uds/` 選擇核心標準複製到 `profiles/standards/minimal/`
- 核心標準清單（參考 `profiles/minimal.yaml` 的 `includes`）：
  - `checkin-standards.ai.yaml`
  - `testing.ai.yaml`
  - `commit-message.ai.yaml`
- 確保檔案列表與 `profiles/minimal.yaml` 的 `includes` 一致

**驗收標準**：
- [ ] Minimal 目錄僅包含 3-5 個核心標準
- [ ] 檔案列表與 `profiles/minimal.yaml` 的 `includes` 一致
- [ ] 檔案內容正確

**預期變更檔案**：
- `profiles/standards/minimal/*.ai.yaml`（新建，3-5 個檔案）

**依賴**：Task 1.2

**狀態**：⏳ 待開始

---

### Task 1.4: 準備 ECC 標準檔案

**位置**：`profiles/standards/ecc/`

**工作內容**：
- 基於 `profiles/ecc.yaml` 的定義準備 ECC 專屬標準
- ECC 繼承 minimal，所以只需準備：
  - **額外標準**：`profiles/ecc.yaml` 的 `includes` 中額外的檔案
  - **覆寫版本**：需要覆寫的標準（如 `commit-message.ai.yaml` 使用英文類型）
- 建立 ECC 版本的 `commit-message.ai.yaml`：
  - 類型使用英文：`feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`
  - 移除繁體中文類型

**驗收標準**：
- [ ] ECC 目錄包含 `profiles/ecc.yaml` 的 `includes` 中額外的檔案
- [ ] `commit-message.ai.yaml` 為 ECC 版本（英文類型）
- [ ] 檔案內容與 ECC 定義一致

**預期變更檔案**：
- `profiles/standards/ecc/commit-message.ai.yaml`（新建，ECC 版本）
- `profiles/standards/ecc/*.ai.yaml`（新建，額外標準）

**依賴**：Task 1.2, Task 1.3

**狀態**：⏳ 待開始

---

### Task 1.5: 更新 active.yaml 加入 managed_files

**位置**：`profiles/active.yaml`

**工作內容**：
- 在 `profiles/active.yaml` 中新增 `managed_files` 欄位
- 新增 `last_activated` 欄位（記錄上次啟用時間）
- 初始值設為空列表（等待首次 activate）
- 更新 YAML 結構：
  ```yaml
  active: uds
  managed_files: []
  last_activated: null
  ```

**驗收標準**：
- [ ] `profiles/active.yaml` 包含 `managed_files` 欄位
- [ ] `profiles/active.yaml` 包含 `last_activated` 欄位
- [ ] YAML 格式正確

**預期變更檔案**：
- `profiles/active.yaml`（修改）

**依賴**：Task 1.1

**狀態**：⏳ 待開始

---

## Phase 2: 動態載入邏輯實作

### Task 2.1: 實作 resolve_standard_source() 函式

**位置**：`script/commands/standards.py`

**工作內容**：
- 新增 `resolve_standard_source(profile_name: str, std_file: str) -> Path` 函式
- 解析標準檔案的來源路徑
- 優先順序：
  1. `profiles/standards/{profile_name}/{std_file}`（Profile 專屬版本）
  2. `profiles/standards/shared/{std_file}`（共用版本）
  3. 若都不存在，raise `FileNotFoundError`
- 加入清晰的 docstring

**驗收標準**：
- [ ] `resolve_standard_source("uds", "commit-message.ai.yaml")` 返回正確路徑
- [ ] `resolve_standard_source("ecc", "commit-message.ai.yaml")` 返回 ECC 專屬版本
- [ ] 找不到檔案時拋出 `FileNotFoundError`
- [ ] 函式有清晰的 docstring

**預期變更檔案**：
- `script/commands/standards.py`

**依賴**：Phase 1 所有任務

**狀態**：⏳ 待開始

---

### Task 2.2: 實作 clear_managed_standards() 函式

**位置**：`script/commands/standards.py`

**工作內容**：
- 新增 `clear_managed_standards() -> list[str]` 函式
- 讀取 `profiles/active.yaml` 的 `managed_files` 清單
- 刪除 `.standards/` 中對應的檔案
- 返回已刪除的檔案列表
- **重要**：不刪除不在 `managed_files` 中的檔案（保護使用者自訂）

**驗收標準**：
- [ ] 函式正確讀取 `managed_files` 清單
- [ ] 只刪除 `managed_files` 中的檔案
- [ ] 不刪除使用者自訂的檔案（不在 `managed_files` 中）
- [ ] 返回已刪除的檔案列表
- [ ] 函式有清晰的 docstring

**預期變更檔案**：
- `script/commands/standards.py`

**依賴**：Task 1.5

**狀態**：⏳ 待開始

---

### Task 2.3: 實作 copy_standard_file() 函式

**位置**：`script/commands/standards.py`

**工作內容**：
- 新增 `copy_standard_file(src: Path, dst: Path) -> None` 函式
- 複製標準檔案從來源到目標
- 若目標目錄不存在，自動建立
- 若目標檔案存在，覆蓋
- 保留檔案編碼（UTF-8）

**驗收標準**：
- [ ] 函式正確複製檔案內容
- [ ] 自動建立目標目錄
- [ ] 覆蓋已存在的檔案
- [ ] 保留 UTF-8 編碼

**預期變更檔案**：
- `script/commands/standards.py`

**依賴**：無

**狀態**：⏳ 待開始

---

### Task 2.4: 實作 apply_overrides() 函式

**位置**：`script/commands/standards.py`

**工作內容**：
- 新增 `apply_overrides(overrides: dict) -> None` 函式
- 讀取對應的標準檔案
- 深度合併 `overrides` 的設定
- 寫回檔案
- 處理 YAML 格式錯誤

**驗收標準**：
- [ ] 正確讀取並修改標準檔案
- [ ] 深度合併（不覆蓋整個結構）
- [ ] 保留檔案格式與註解（盡可能）
- [ ] 處理檔案不存在的情況

**預期變更檔案**：
- `script/commands/standards.py`

**依賴**：無

**狀態**：⏳ 待開始

---

### Task 2.5: 實作 activate_profile() 主函式

**位置**：`script/commands/standards.py`

**工作內容**：
- 新增 `activate_profile(name: str) -> dict` 函式
- 完整的啟用流程：
  1. 載入 Profile 定義（使用 `load_profile()`）
  2. 解析完整的 `includes` 清單（處理繼承）
  3. 呼叫 `clear_managed_standards()` 清除舊檔案
  4. 遍歷 `includes`，使用 `resolve_standard_source()` 和 `copy_standard_file()` 複製檔案
  5. 呼叫 `apply_overrides()`（若有 overrides）
  6. 更新 `profiles/active.yaml`：`active`, `managed_files`, `last_activated`
  7. 返回啟用結果（成功、複製的檔案數、警告等）
- 加入詳細的日誌輸出

**驗收標準**：
- [ ] `activate_profile("uds")` 成功複製 UDS 標準到 `.standards/`
- [ ] `activate_profile("minimal")` 後 `.standards/` 只有 minimal 的標準
- [ ] `activate_profile("ecc")` 正確處理繼承與 overrides
- [ ] `profiles/active.yaml` 的 `managed_files` 正確更新
- [ ] 函式返回啟用結果
- [ ] 有清晰的日誌輸出

**預期變更檔案**：
- `script/commands/standards.py`

**依賴**：Task 2.1, Task 2.2, Task 2.3, Task 2.4

**狀態**：⏳ 待開始

---

## Phase 3: CLI 指令更新

### Task 3.1: 更新 switch() 命令觸發 activate_profile()

**位置**：`script/commands/standards.py`

**工作內容**：
- 修改 `switch()` 命令
- 在更新 `active` 欄位後，呼叫 `activate_profile(name)`
- 顯示啟用結果（複製了多少檔案、耗時等）
- 處理啟用失敗的情況（回退到原 Profile）

**驗收標準**：
- [ ] `ai-dev standards switch ecc` 觸發 `activate_profile("ecc")`
- [ ] 成功時顯示啟用結果
- [ ] 失敗時顯示錯誤訊息並回退
- [ ] `.standards/` 實際發生變化

**預期變更檔案**：
- `script/commands/standards.py`

**依賴**：Task 2.5

**狀態**：⏳ 待開始

---

### Task 3.2: 新增 sync 命令

**位置**：`script/commands/standards.py`

**工作內容**：
- 新增 `sync()` 命令
- 功能：重新同步當前 Profile 的標準檔案
- 讀取 `profiles/active.yaml` 的 `active` 欄位
- 呼叫 `activate_profile(active)`
- 使用情境：UDS 更新後，使用者手動重新同步

**驗收標準**：
- [ ] `ai-dev standards sync` 重新啟用當前 Profile
- [ ] 顯示同步結果
- [ ] 處理無 active Profile 的情況

**預期變更檔案**：
- `script/commands/standards.py`

**依賴**：Task 2.5

**狀態**：⏳ 待開始

---

### Task 3.3: 更新 status() 命令顯示 managed_files

**位置**：`script/commands/standards.py`

**工作內容**：
- 修改 `status()` 命令
- 顯示 `managed_files` 的數量
- 顯示 `last_activated` 時間
- 可選：顯示 `.standards/` 中非 managed 的檔案數量（使用者自訂）

**驗收標準**：
- [ ] `ai-dev standards status` 顯示 managed_files 數量
- [ ] 顯示 last_activated 時間
- [ ] 格式清晰美觀

**預期變更檔案**：
- `script/commands/standards.py`

**依賴**：Task 1.5

**狀態**：⏳ 待開始

---

## Phase 4: 安全機制與整合

### Task 4.1: 實作使用者自訂標準保護

**位置**：`script/commands/standards.py`

**工作內容**：
- 在 `clear_managed_standards()` 中加入保護機制
- 偵測 `.standards/` 中不在 `managed_files` 的檔案
- 這些檔案視為「使用者自訂」，不刪除
- 在 `activate_profile()` 中發出警告（若有使用者自訂檔案）

**驗收標準**：
- [ ] 使用者自訂檔案不會被刪除
- [ ] 切換時顯示「保留了 X 個使用者自訂檔案」警告
- [ ] 保護機制正確運作

**預期變更檔案**：
- `script/commands/standards.py`

**依賴**：Task 2.2, Task 2.5

**狀態**：⏳ 待開始

---

### Task 4.2: 整合 TUI Profile 切換

**位置**：`script/tui/app.py`

**工作內容**：
- 驗證 TUI 的 Profile 切換（下拉選單與 `t` 快捷鍵）觸發 `activate_profile()`
- 若 TUI 使用不同的切換邏輯，更新為呼叫 `switch()` 命令
- 在 TUI 中顯示切換結果（Toast 通知或狀態更新）

**驗收標準**：
- [ ] TUI 切換 Profile 時實際觸發 `activate_profile()`
- [ ] `.standards/` 實際發生變化
- [ ] 顯示切換結果通知

**預期變更檔案**：
- `script/tui/app.py`（可能需要修改）

**依賴**：Task 3.1

**狀態**：⏳ 待開始

---

### Task 4.3: 錯誤處理與回復機制

**位置**：`script/commands/standards.py`

**工作內容**：
- 在 `activate_profile()` 中加入錯誤處理
- 若複製過程中失敗，回復到原狀態
- 記錄錯誤日誌
- 提供使用者友善的錯誤訊息

**驗收標準**：
- [ ] 標準檔案不存在時顯示清晰錯誤
- [ ] 複製失敗時不會留下半完成狀態
- [ ] 錯誤訊息包含解決建議

**預期變更檔案**：
- `script/commands/standards.py`

**依賴**：Task 2.5

**狀態**：⏳ 待開始

---

## Phase 5: 文件與測試

### Task 5.1: 更新 README.md

**位置**：`README.md`

**工作內容**：
- 更新 Standards Profile 章節
- 說明動態載入功能
- 說明 `switch` 命令的實際影響
- 說明 `sync` 命令的使用時機
- 說明使用者自訂標準的保護機制

**驗收標準**：
- [ ] 說明清晰完整
- [ ] 包含使用範例
- [ ] 說明各 Profile 的差異

**預期變更檔案**：
- `README.md`

**依賴**：Phase 3 所有任務

**狀態**：⏳ 待開始

---

### Task 5.2: 更新 CHANGELOG.md

**位置**：`CHANGELOG.md`

**工作內容**：
- 在 `[Unreleased]` 區段新增變更條目
- **Added**：
  - 動態 Profile 載入功能
  - `ai-dev standards sync` 命令
  - 使用者自訂標準保護機制
- **Changed**：
  - `ai-dev standards switch` 現在會實際切換標準內容

**驗收標準**：
- [ ] 變更記錄清晰完整
- [ ] 分類正確

**預期變更檔案**：
- `CHANGELOG.md`

**依賴**：Phase 4 所有任務

**狀態**：⏳ 待開始

---

### Task 5.3: CLI 手動測試

**工作內容**：
- 測試完整的 Profile 切換流程：
  - [ ] `ai-dev standards switch minimal` - `.standards/` 只有 3-5 個檔案
  - [ ] `ai-dev standards switch uds` - `.standards/` 有 10+ 個檔案
  - [ ] `ai-dev standards switch ecc` - `commit-message.ai.yaml` 為英文版
- 測試同步功能：
  - [ ] `ai-dev standards sync` 重新同步當前 Profile
- 測試保護機制：
  - [ ] 建立自訂標準檔案（如 `custom.ai.yaml`）
  - [ ] 切換 Profile 後，自訂檔案仍存在

**依賴**：Phase 4 所有任務

**狀態**：⏳ 待開始

---

### Task 5.4: TUI 手動測試

**工作內容**：
- 啟動 TUI (`ai-dev tui`)
- 測試 Profile 切換：
  - [ ] 下拉選單切換功能正常
  - [ ] 快捷鍵 `t` 循環切換正常
  - [ ] 切換後 `.standards/` 實際變化
  - [ ] 顯示切換結果通知

**依賴**：Task 4.2

**狀態**：⏳ 待開始

---

## 總結

### 任務統計

- **Phase 1**：5 個任務（標準檔案庫建立）
- **Phase 2**：5 個任務（動態載入邏輯實作）
- **Phase 3**：3 個任務（CLI 指令更新）
- **Phase 4**：3 個任務（安全機制與整合）
- **Phase 5**：4 個任務（文件與測試）
- **總計**：20 個任務

### 實際變更檔案

- `profiles/standards/` 目錄（新建，含子目錄）
- `profiles/standards/uds/*.ai.yaml`（新建，10+ 個檔案）
- `profiles/standards/minimal/*.ai.yaml`（新建，3-5 個檔案）
- `profiles/standards/ecc/*.ai.yaml`（新建，ECC 專屬版本）
- `profiles/active.yaml`（修改，新增 `managed_files` 欄位）
- `script/commands/standards.py`（重構，新增動態載入函式）
- `script/tui/app.py`（可能需要微調）
- `README.md`（更新）
- `CHANGELOG.md`（更新）

### 關鍵依賴關係

```
implement-profile-system (Phase 2) → 本提案
Phase 1 (所有任務) → Phase 2
Task 2.1, 2.2, 2.3, 2.4 → Task 2.5
Phase 2 (所有任務) → Phase 3
Phase 3 (所有任務) → Phase 4, Phase 5
```

### 並行機會

- Task 1.2, 1.3, 1.4, 1.5 可以部分並行
- Task 2.1, 2.2, 2.3, 2.4 可以部分並行
- Task 5.1, 5.2 可以並行

### 風險項目

- ⚠️ Task 1.4：ECC 標準的具體內容需要確認
- ⚠️ Task 2.5：activate_profile() 是核心函式，需要仔細測試
- ⚠️ Task 4.1：使用者自訂標準保護機制需要仔細設計

### 成功標準總覽

- [ ] 所有 20 個任務完成
- [ ] `switch` 命令實際改變 `.standards/` 內容
- [ ] 三個 Profile 有明顯差異（檔案數量、內容）
- [ ] 使用者自訂標準不被覆蓋
- [ ] 文件更新完整
- [ ] 所有手動測試通過
