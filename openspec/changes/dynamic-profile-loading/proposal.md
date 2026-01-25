# Proposal: dynamic-profile-loading

## Summary

實作動態 Profile 載入功能，讓切換 Profile 時**實際改變**載入的標準內容。此提案建立在 `implement-profile-system`（Phase 2）的基礎上，完成 Profile 系統的最後一塊拼圖。

## Background

### 前置提案

**implement-profile-system**（Phase 2）完成後，系統具備：
- ✅ `profiles/` 目錄結構（專案根目錄）
- ✅ Profile 定義檔案（`uds.yaml`, `ecc.yaml`, `minimal.yaml`）
- ✅ Profile 載入與繼承邏輯（`load_profile()`, `merge_profiles()`）
- ✅ CLI 指令（`list`, `show`, `switch`, `status`）
- ❌ **未實作**：切換 Profile 時實際改變標準內容

### 現狀問題

Phase 2 完成後：
- `ai-dev standards switch ecc` 只更新 `profiles/active.yaml` 的 `active` 欄位
- `.standards/` 中的標準檔案**不會改變**
- AI 助手看到的標準仍然一樣（都是 UDS 的內容）
- Profile 切換形同虛設

### 目標

實現真正的動態 Profile 載入：
1. **標準庫管理**：在 `profiles/standards/` 中儲存各 Profile 的標準檔案
2. **動態切換**：切換 Profile 時，更新 `.standards/` 中載入的標準
3. **差異化體驗**：不同 Profile 有不同的標準內容（minimal 最少、uds 最多、ecc 有獨特設定）
4. **安全機制**：備份、還原、衝突處理

## Motivation

### 使用者價值

- **真正的 Profile 切換**：切換後 AI 助手立即遵循不同標準
- **按需載入**：minimal 適合輕量專案、uds 適合完整專案、ecc 適合 TypeScript/React 專案
- **清晰的預期**：「切換」名副其實，不再造成困惑

### 技術價值

- **完成 Profile 系統**：Phase 2 + Phase 3 = 完整功能
- **標準隔離**：各 Profile 的標準獨立管理，不互相影響
- **可擴展**：未來可輕鬆新增更多 Profiles

## Scope

### 包含範圍

1. **標準庫建立**
   - 建立 `profiles/standards/` 目錄結構
   - 為每個 Profile 準備對應的標準檔案集合
   - 定義標準檔案的來源與管理方式

2. **動態載入機制**
   - 實作 `activate_profile(name)` 函式
   - 根據 Profile 定義的 `includes` 啟用對應標準
   - 處理 `inherits` 繼承的標準
   - 套用 `overrides` 覆寫設定

3. **同步與更新**
   - 更新 `switch` 命令呼叫 `activate_profile()`
   - 實作 `ai-dev standards sync` 重新同步當前 Profile 的標準
   - 處理標準檔案遺失或損壞的情況

4. **安全機制**
   - 標準檔案的來源追蹤
   - 使用者自訂標準的保護機制
   - 錯誤處理與回復

### 不包含範圍

- **標準檔案自動下載**：不從遠端 repo 自動下載（標準檔案已內建於 `profiles/standards/`）
- **自訂 Profile 建立**：不提供建立新 Profile 的 UI（僅支援三個內建 Profiles）
- **標準檔案編輯**：不提供標準檔案的編輯功能

## Design Considerations

### 核心設計：符號連結 vs 檔案複製

#### Option A: 符號連結（Symlink）

```
.standards/
  commit-message.ai.yaml → ../profiles/standards/uds/commit-message.ai.yaml
  testing.ai.yaml → ../profiles/standards/uds/testing.ai.yaml
```

**優點**：
- 不佔用額外空間
- 修改即時生效
- 更新來源檔案自動反映

**缺點**：
- Windows 需要管理員權限或開發者模式
- 部分工具不支援符號連結
- 跨平台相容性問題

#### Option B: 檔案複製（推薦）

```
.standards/
  commit-message.ai.yaml  # 從 profiles/standards/uds/ 複製
  testing.ai.yaml         # 從 profiles/standards/uds/ 複製
```

**優點**：
- 跨平台相容
- 無權限問題
- 簡單可靠

**缺點**：
- 佔用空間（但標準檔案很小，可忽略）
- 需要手動同步更新

**選擇**：採用 Option B（檔案複製），確保跨平台相容性。

### 目錄結構

```
profiles/
├── active.yaml           # 目前啟用的 Profile
├── uds.yaml              # UDS Profile 定義
├── ecc.yaml              # ECC Profile 定義
├── minimal.yaml          # Minimal Profile 定義
└── standards/            # 標準檔案庫
    ├── uds/              # UDS 專屬標準
    │   ├── commit-message.ai.yaml
    │   ├── traditional-chinese.ai.yaml
    │   ├── test-driven-development.ai.yaml
    │   └── ...
    ├── ecc/              # ECC 專屬標準（覆寫或額外的）
    │   ├── commit-message.ai.yaml  # ECC 版本（英文類型）
    │   └── ...
    ├── minimal/          # Minimal 專屬標準
    │   ├── checkin-standards.ai.yaml
    │   ├── testing.ai.yaml
    │   └── commit-message.ai.yaml
    └── shared/           # 共用標準（可選）
        └── ...
```

### Profile 啟用流程

```python
def activate_profile(name: str) -> None:
    """
    啟用指定的 Profile，載入對應的標準檔案

    步驟：
    1. 載入 Profile 定義（處理繼承）
    2. 解析 includes 清單（完整的標準檔案列表）
    3. 清除 .standards/ 中由 Profile 管理的檔案
    4. 從 profiles/standards/{profile}/ 複製標準檔案到 .standards/
    5. 套用 overrides（若有）
    6. 更新 profiles/active.yaml
    7. 記錄啟用日誌
    """
    profile = load_profile(name)
    includes = profile['includes']

    # 清除舊的 Profile 管理的檔案（保留使用者自訂）
    clear_managed_standards()

    # 複製新 Profile 的標準檔案
    for std_file in includes:
        src = resolve_standard_source(name, std_file)
        dst = get_standards_dir() / std_file
        copy_standard_file(src, dst)

    # 套用 overrides
    if 'overrides' in profile:
        apply_overrides(profile['overrides'])

    # 更新 active.yaml
    update_active_profile(name)
```

### 標準檔案來源解析

```python
def resolve_standard_source(profile_name: str, std_file: str) -> Path:
    """
    解析標準檔案的來源路徑

    優先順序：
    1. profiles/standards/{profile_name}/{std_file}  # Profile 專屬版本
    2. profiles/standards/shared/{std_file}          # 共用版本
    3. 若都不存在，raise FileNotFoundError
    """
    profile_specific = get_profiles_dir() / 'standards' / profile_name / std_file
    shared = get_profiles_dir() / 'standards' / 'shared' / std_file

    if profile_specific.exists():
        return profile_specific
    elif shared.exists():
        return shared
    else:
        raise FileNotFoundError(f"Standard file not found: {std_file}")
```

### 管理檔案追蹤

為了區分「Profile 管理的標準」與「使用者自訂的標準」，需要追蹤機制：

```yaml
# profiles/active.yaml
active: uds
managed_files:          # 由 Profile 系統管理的檔案
  - commit-message.ai.yaml
  - testing.ai.yaml
  - checkin-standards.ai.yaml
last_activated: "2026-01-25T10:30:00"
```

**規則**：
- `managed_files` 中的檔案會在切換時被覆蓋
- 不在 `managed_files` 中的 `.standards/` 檔案視為使用者自訂，不會被刪除

### Overrides 套用機制

```python
def apply_overrides(overrides: dict) -> None:
    """
    套用 Profile 的 overrides 設定

    overrides 格式：
    {
        "commit-message": {
            "language": "en",
            "types": ["feat", "fix", "docs", ...]
        }
    }

    實作方式：
    1. 讀取對應的標準檔案（.standards/commit-message.ai.yaml）
    2. 深度合併 overrides 的設定
    3. 寫回檔案
    """
    for std_name, settings in overrides.items():
        std_file = f"{std_name}.ai.yaml"
        std_path = get_standards_dir() / std_file

        if std_path.exists():
            content = load_yaml(std_path)
            merged = deep_merge(content, settings)
            save_yaml(std_path, merged)
```

## Success Criteria

### 功能驗收

- [ ] `profiles/standards/` 目錄結構已建立
- [ ] 三個 Profile 的標準檔案已準備完成
- [ ] `ai-dev standards switch ecc` 實際複製 ECC 的標準檔案到 `.standards/`
- [ ] `ai-dev standards switch minimal` 後，`.standards/` 只有 minimal 的標準
- [ ] `ai-dev standards switch uds` 後，`.standards/` 有完整的 UDS 標準
- [ ] 使用者自訂的標準檔案（不在 `managed_files`）不會被刪除
- [ ] `ai-dev standards sync` 可重新同步當前 Profile 的標準

### 差異驗證

- [ ] Minimal Profile：`.standards/` 只有 3-5 個核心標準
- [ ] UDS Profile：`.standards/` 有 10+ 個完整標準
- [ ] ECC Profile：`commit-message.ai.yaml` 使用英文類型（而非繁體中文）

### 文件驗收

- [ ] README.md 更新，說明動態載入功能
- [ ] CHANGELOG.md 記錄 Phase 3 完成
- [ ] 使用者指南說明 Profile 切換的影響

## Risks and Mitigations

### 風險 1: 標準檔案來源不明確

**描述**：各 Profile 的標準檔案內容從哪裡來？如何維護？

**緩解措施**：
- UDS：直接使用現有 `.standards/` 中的檔案（來自 universal-dev-standards）
- Minimal：從 UDS 中選擇核心子集
- ECC：基於 minimal + 參考 `sources/ecc/` 的最佳實踐

### 風險 2: 使用者自訂標準被覆蓋

**描述**：切換 Profile 可能意外刪除使用者自訂的標準檔案。

**緩解措施**：
- 使用 `managed_files` 追蹤 Profile 管理的檔案
- 只刪除/覆蓋 `managed_files` 中的檔案
- 在刪除前檢查是否有未追蹤的修改，若有則警告

### 風險 3: 磁碟空間增加

**描述**：每個 Profile 都有獨立的標準檔案副本，增加磁碟使用量。

**緩解措施**：
- 標準檔案都是文字檔，總量很小（通常 < 1 MB）
- 使用 `shared/` 目錄存放共用標準，減少重複
- 可接受的權衡（簡單可靠 > 空間優化）

### 風險 4: UDS 更新覆蓋問題

**描述**：使用者執行 `ai-dev project init` 或 UDS 更新時，`.standards/` 被重置。

**緩解措施**：
- 在 `init` 流程中加入 Profile 檢測，自動重新啟用當前 Profile
- 提供 `ai-dev standards sync` 讓使用者手動重新同步
- 文件中說明此行為

## Dependencies

- **前置依賴**：`implement-profile-system`（Phase 2）必須先完成
- **下游影響**：無

## Alternative Approaches

### 方案 1: 直接修改 .standards/ 中的檔案（不複製）

**描述**：不建立 `profiles/standards/`，而是動態修改 `.standards/` 中的檔案內容。

**為何不採用**：
- 複雜度高（需要知道每個 Profile 的「應有內容」）
- 難以還原到原始狀態
- 與 UDS 更新機制衝突

### 方案 2: 使用 Git 分支管理不同 Profile

**描述**：每個 Profile 對應一個 Git 分支，切換時 checkout 對應分支。

**為何不採用**：
- 過於複雜，使用者門檻高
- 與專案本身的 Git 歷史混淆
- 不適合這個使用場景

## Open Questions

1. **ECC 標準的具體內容**
   - **問題**：ECC Profile 應該包含哪些獨特的標準？
   - **建議**：先以 minimal 為基礎，加入 `code-review.ai.yaml`，並覆寫 `commit-message` 為英文類型

2. **標準檔案的更新機制**
   - **問題**：當 UDS 上游更新標準檔案時，如何同步到 `profiles/standards/`？
   - **建議**：手動更新，或提供 `ai-dev standards update` 命令（留待未來版本）

3. **manifest.json 的處理**
   - **問題**：`.standards/manifest.json` 是否也應該根據 Profile 變化？
   - **建議**：不處理，保持現有 manifest（它記錄的是 UDS 的版本資訊）

## Timeline Estimate

**注意**：此估計僅供參考，實際時間可能因實作細節而異。

- Phase 1: 標準庫建立（2-3 小時）
- Phase 2: 動態載入實作（3-4 小時）
- Phase 3: CLI 更新與同步（2-3 小時）
- Phase 4: 安全機制與測試（2-3 小時）

總計：約 9-13 小時的開發時間。

## Approval

此提案需要 `implement-profile-system` 完成後才能執行。

核准標準：
- [ ] `implement-profile-system` 已完成並驗證
- [ ] 提案範圍清晰，目標明確
- [ ] 設計方案合理，風險可控
- [ ] 成功標準可驗證
