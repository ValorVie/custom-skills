# Proposal: implement-profile-system

## Summary

實作完整的 Standards Profile 系統架構，取代目前的臨時清單模式。此提案將建立 `profiles/*.yaml` 定義檔案，實現真正的標準來源切換功能，讓不同 profiles 能載入不同的標準內容。

## Background

### 現狀

在 `fix-tui-detection-logic` 提案中，我們實作了一個**臨時方案**來快速修正 TUI 的 Profile 檢測邏輯：

- **簡化的清單模式**：`list_profiles()` 函式從 `profiles/active.yaml` 的 `available` 欄位讀取 profile 清單
- **無實質切換**：切換 profile 只更新 `active` 欄位，**不會載入不同的標準內容**
- **缺少定義檔案**：沒有 `profiles/*.yaml` 定義檔案，無法描述各 profile 的內容與來源
- **功能受限**：`show` 命令無法顯示 profile 詳細資訊

所有 profiles (uds, ecc, minimal) 目前都使用相同的 UDS 標準檔案。

### 問題

1. **Profile 切換無效**：使用者切換 profile 後，看到的仍是相同的標準內容
2. **無法自訂 Profile**：沒有定義檔案，無法描述 profile 應包含哪些標準
3. **缺少繼承機制**：無法實現 `ecc` 繼承 `minimal` 並覆寫部分設定的設計
4. **技術債累積**：程式碼中充滿「臨時」、「Phase 2」的註解，影響程式碼品質

### 目標

建立完整的 Profile 系統架構，實現：

1. **Profile 定義檔案**：建立 `profiles/uds.yaml`, `profiles/ecc.yaml`, `profiles/minimal.yaml`
2. **真正的標準切換**：切換 profile 時載入對應的標準檔案
3. **繼承與覆寫**：支援 `inherits` 和 `overrides` 機制
4. **詳細資訊顯示**：`show` 命令能顯示 profile 的完整內容
5. **移除臨時方案**：清除所有「臨時」註解，完成正式實作

## Motivation

### 使用者價值

- **清晰的標準體系**：使用者能清楚了解每個 profile 包含哪些標準
- **真正的切換功能**：切換 profile 後立即看到不同的標準內容
- **靈活的自訂**：進階使用者可自訂 profile，組合不同的標準

### 技術價值

- **可維護性**：移除臨時方案，程式碼更清晰
- **可擴展性**：未來可輕鬆新增更多 profiles
- **符合規格**：實現 `standards-profiles` spec 中定義的所有需求

## Scope

### 包含範圍

1. **Profile 定義檔案**
   - 建立專案根目錄的 `profiles/` 目錄（獨立於 `.standards/`，避免被 UDS 覆蓋）
   - 建立 `uds.yaml`, `ecc.yaml`, `minimal.yaml` 定義檔案
   - 定義每個 profile 的 `name`, `description`, `includes`, `inherits`, `overrides` 欄位

2. **Profile 載入邏輯**
   - 實作 `load_profile(name)` 函式，根據定義檔案載入標準
   - 實作 `resolve_profile_includes(profile)` 處理 `includes` 欄位
   - 實作 `apply_profile_inheritance(profile)` 處理 `inherits` 欄位
   - 實作 `apply_profile_overrides(profile)` 處理 `overrides` 欄位

3. **CLI 指令更新**
   - 更新 `list_profiles()` 從 `profiles/*.yaml` 讀取清單
   - 更新 `show` 命令顯示 profile 詳細內容（包含的標準、繼承關係）
   - 更新 `switch` 命令實際套用 profile 設定（若需要的話）

4. **文件與測試**
   - 移除所有「臨時」、「Phase 2」註解
   - 更新 README.md，移除已知限制警告
   - 更新 CHANGELOG.md，記錄正式實作完成
   - 手動測試所有 profile 切換情境

### 不包含範圍

- **動態標準載入**：不在此階段實作真正的「載入不同標準檔案到 `.standards/`」機制（僅更新定義與邏輯，實際檔案仍保持 UDS 內容）
- **Profile 建立 UI**：不提供新增自訂 profile 的 TUI 介面（僅支援三個內建 profiles）
- **標準檔案自動下載**：不實作從上游 repo 自動下載標準檔案的功能

## Design Considerations

### Profile 定義檔案格式

```yaml
# profiles/uds.yaml (專案根目錄)
name: uds
display_name: "Universal Dev Standards"
description: "完整的 UDS 標準體系，包含繁體中文提交訊息與完整 SDD/TDD/BDD 整合"
version: "1.0.0"

includes:
  # 標準檔案路徑相對於 .standards/ 目錄
  - commit-message.ai.yaml
  - traditional-chinese.ai.yaml
  - test-driven-development.ai.yaml
  - code-review.ai.yaml
  - spec-driven-development.ai.yaml
  - behavior-driven-development.ai.yaml
  - acceptance-test-driven-development.ai.yaml
  - checkin-standards.ai.yaml
  - git-workflow.ai.yaml
  - documentation-structure.ai.yaml
  - error-codes.ai.yaml
  - logging.ai.yaml
  - versioning.ai.yaml
  - changelog.ai.yaml

# 可選欄位（此 profile 不使用）
# inherits: null
# overrides: {}
```

```yaml
# profiles/minimal.yaml
name: minimal
display_name: "Minimal Standards"
description: "基礎標準體系，僅包含核心開發規範"
version: "1.0.0"

includes:
  - checkin-standards.ai.yaml
  - testing.ai.yaml
  - commit-message.ai.yaml
```

```yaml
# profiles/ecc.yaml
name: ecc
display_name: "Everything Claude Code"
description: "ECC 標準體系，採用 TypeScript/React 導向的實戰開發標準"
version: "1.0.0"

inherits: minimal

includes:
  # 額外包含的標準（在 minimal 基礎上）
  - code-review.ai.yaml
  - test-driven-development.ai.yaml

overrides:
  # 覆寫 commit-message 使用英文類型（而非繁體中文）
  commit-message:
    language: en
    types:
      - feat
      - fix
      - docs
      - style
      - refactor
      - test
      - chore
```

### Profile 載入邏輯

```python
def load_profile(name: str) -> dict:
    """載入並解析 profile 定義"""
    profile_path = get_profiles_dir() / f"{name}.yaml"
    if not profile_path.exists():
        raise ValueError(f"Profile '{name}' not found")

    profile = load_yaml(profile_path)

    # 處理繼承
    if 'inherits' in profile and profile['inherits']:
        parent = load_profile(profile['inherits'])
        profile = merge_profiles(parent, profile)

    return profile

def merge_profiles(parent: dict, child: dict) -> dict:
    """合併父子 profile（處理 includes 與 overrides）"""
    merged = parent.copy()

    # 合併 includes（子 profile 的 includes 追加到父 profile）
    merged['includes'] = parent.get('includes', []) + child.get('includes', [])

    # 套用 overrides（子 profile 的 overrides 覆蓋父 profile）
    if 'overrides' in child:
        merged['overrides'] = {**parent.get('overrides', {}), **child['overrides']}

    # 更新基本資訊（name, description 等使用子 profile 的值）
    for key in ['name', 'display_name', 'description', 'version']:
        if key in child:
            merged[key] = child[key]

    return merged
```

### CLI 指令更新

```python
def list_profiles() -> list[str]:
    """列出所有可用的 profiles"""
    profiles_dir = get_profiles_dir()
    if not profiles_dir.exists():
        return []

    return [p.stem for p in profiles_dir.glob("*.yaml")]

def show_profile(name: str):
    """顯示 profile 詳細內容"""
    profile = load_profile(name)

    console.print(f"[bold]{profile['display_name']}[/bold]")
    console.print(f"Description: {profile['description']}")
    console.print(f"Version: {profile.get('version', 'N/A')}")

    if profile.get('inherits'):
        console.print(f"Inherits: {profile['inherits']}")

    console.print("\nIncluded Standards:")
    for std in profile.get('includes', []):
        console.print(f"  - {std}")

    if profile.get('overrides'):
        console.print("\nOverrides:")
        console.print_json(data=profile['overrides'])
```

### 架構取捨

#### Option A: 完整動態載入（未採用）

**描述**：切換 profile 時，實際替換 `.standards/` 目錄中的標準檔案。

**優點**：
- 真正的「載入不同標準」
- 使用者在 `.standards/` 看到的檔案就是當前 profile 的內容

**缺點**：
- 複雜度高，需要處理檔案複製、備份、衝突
- 可能覆蓋使用者自訂的標準
- 需要管理標準檔案的來源（從哪裡下載？如何更新？）

#### Option B: 定義與邏輯層（已採用）

**描述**：建立 profile 定義檔案和載入邏輯，但實際標準檔案保持不變。Profile 定義描述「應該包含哪些標準」，但不實際替換檔案。

**優點**：
- 簡單可靠，不涉及檔案操作
- 為未來的動態載入預留空間
- 快速完成 Phase 2，移除臨時方案

**缺點**：
- 仍然是「半完成」狀態（定義存在，但不實際生效）
- 需要在文件中說明當前限制

**選擇理由**：
採用 Option B 作為 Phase 2 的範圍，原因：
1. **降低風險**：避免複雜的檔案操作邏輯
2. **快速交付**：專注於移除臨時方案，建立正確的架構
3. **可擴展**：為 Phase 3（真正的動態載入）打下基礎

## Success Criteria

### 功能驗收

- [ ] 專案根目錄的 `profiles/` 目錄已建立
- [ ] `uds.yaml`, `ecc.yaml`, `minimal.yaml` 定義檔案已建立且格式正確
- [ ] `ai-dev standards list` 從 `profiles/*.yaml` 讀取清單（不再使用 `profiles/active.yaml` 的 `available` 欄位）
- [ ] `ai-dev standards show uds` 顯示完整的 profile 資訊（名稱、描述、包含的標準）
- [ ] `ai-dev standards show ecc` 正確顯示繼承關係（inherits: minimal）
- [ ] 程式碼中所有「臨時」、「TODO: Phase 2」註解已移除
- [ ] 所有警告訊息（「Profile 切換目前為臨時功能」）已移除或更新

### 文件驗收

- [ ] README.md 已更新，移除「已知限制」警告
- [ ] CHANGELOG.md 已記錄 Profile 系統正式實作完成
- [ ] 程式碼註解清晰，說明 profile 載入邏輯

### 測試驗收

- [ ] 手動測試 `ai-dev standards list` 在已初始化專案中正常運作
- [ ] 手動測試 `ai-dev standards show <profile>` 顯示正確資訊
- [ ] 手動測試 TUI 中 Profile 選單正常載入（從 `profiles/*.yaml`）
- [ ] 驗證 `ecc` profile 正確繼承 `minimal` 的內容

## Risks and Mitigations

### 風險 1: Profile 定義格式不穩定

**描述**：初版定義格式可能需要調整，導致後續破壞性變更。

**緩解措施**：
- 在定義檔案中加入 `version` 欄位，為未來的格式升級預留空間
- 在 README 中標註 profile 定義格式為 `v1.0.0`，明確版本化

### 風險 2: 使用者誤解「切換」功能

**描述**：使用者以為切換 profile 會立即改變 `.standards/` 中的檔案內容。

**緩解措施**：
- 在 README 中明確說明當前實作範圍：「Profile 定義已建立，但實際標準檔案仍使用 UDS 內容」
- 在 CLI 輸出中提示：「Profile 定義已切換，實際標準載入將在未來版本提供」

### 風險 3: 與現有規格不一致

**描述**：實作可能與 `standards-profiles` spec 中的某些需求不完全一致。

**緩解措施**：
- 在提案驗證階段仔細檢查 spec deltas
- 若有不一致，更新 spec 或調整實作

## Alternative Approaches

### 方案 1: 一步到位實作動態載入

**描述**：直接實作 Option A（完整動態載入），讓 profile 切換真正替換標準檔案。

**為何不採用**：
- 複雜度過高，風險大
- 需要處理備份、衝突、來源管理等問題
- 超出「移除臨時方案」的原始需求

### 方案 2: 保持臨時方案，不做 Phase 2

**描述**：接受當前的臨時實作，不進行 Phase 2 重構。

**為何不採用**：
- 技術債累積，程式碼品質下降
- 使用者困惑（切換功能名不副實）
- 違背「完整 Profile 架構」的承諾

## Open Questions

1. **Profile 定義檔案的位置**
   - **問題**：應該放在 `.standards/profiles/` 還是專案根目錄的 `profiles/`？
   - **決定**：專案根目錄的 `profiles/`（避免被 UDS 的 `.standards/` 更新覆蓋）

2. **ecc profile 的實際內容**
   - **問題**：`ecc` profile 應該包含哪些標準檔案？是否需要參考 `sources/ecc/` 中的內容？
   - **建議**：先實作一個簡化版（inherits minimal + 少數額外標準），未來再擴展

3. **overrides 的實際應用**
   - **問題**：`overrides` 欄位應該如何影響實際的標準內容？
   - **建議**：此階段僅在 `show` 命令中顯示 overrides，不實際套用（留待 Phase 3）

## Dependencies

- **上游依賴**：無（此提案不依賴其他未完成的變更）
- **下游影響**：
  - TUI 的 Profile 選單將從新的 `list_profiles()` 載入資料
  - 未來的「動態標準載入」功能將基於此架構

## Timeline Estimate

**注意**：此估計僅供參考，實際時間可能因實作細節而異。

- Phase 1: Profile 定義檔案建立（1-2 小時）
- Phase 2: 載入邏輯實作（2-3 小時）
- Phase 3: CLI 指令更新（1-2 小時）
- Phase 4: 測試與文件更新（1-2 小時）

總計：約 5-9 小時的開發時間。

## Approval

此提案需要使用者審核並核准後才能進入 `apply` 階段。

核准標準：
- [ ] 提案範圍清晰，目標明確
- [ ] 設計方案合理，取捨有據
- [ ] 成功標準可驗證
- [ ] 風險已識別並有緩解措施
