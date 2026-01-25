# Proposal: fix-tui-detection-logic

## Summary

修正 TUI 介面中兩個偵測邏輯問題：
1. **ECC Hooks Plugin 偵測**：目前 TUI 顯示完整的安裝/移除功能，但根據新的架構（使用者透過 `@plugins` 自行安裝），應改為只顯示**是否已安裝**的狀態偵測
2. **Standards Profile 偵測**：目前 TUI 檢查 `.standards/profiles/` 目錄是否存在來判斷初始化狀態，但專案實際已初始化（`.standards/` 目錄存在且包含 `active-profile.yaml`），導致 TUI 錯誤顯示「未初始化」訊息

**重要說明**：本提案為**臨時修正方案**，採用簡化的清單模式讀取 profiles。完整的 Profile 架構（包含 `profiles/*.yaml` 定義檔案與真正的標準來源切換）將在後續提案中實作。

## Problem

### 問題 1: ECC Hooks Plugin 顯示邏輯過時

**現況分析** [Source: Code] `script/tui/app.py:253-260`:
```python
# ECC Hooks Plugin 區塊
with Container(id="hooks-section"):
    yield Static("ECC Hooks Plugin", id="hooks-title")
    yield Label("", id="hooks-status-label")
    with Horizontal(id="hooks-button-row"):
        yield Button("Install/Update", id="btn-hooks-install", variant="success")
        yield Button("Uninstall", id="btn-hooks-uninstall", variant="error")
        yield Button("View Config", id="btn-hooks-view", variant="default")
```

TUI 提供完整的安裝/移除按鈕，但根據 [Source: User Request] 使用者需求：「ecc hook 改成偵測是否安裝就好，現在已經改成使用者透過 @plugins 自行安裝」

**根本原因**：TUI 的設計假設 ai-dev 負責管理 ECC Hooks Plugin 的安裝，但實際上新架構已改為使用者自行透過 `@plugins` 或 `npx skills add` 安裝。

### 問題 2: Standards Profile 偵測邏輯錯誤

**現況分析** [Source: Code] `script/tui/app.py:509-514`:
```python
def update_standards_profile_display(self) -> None:
    profiles_dir = get_profiles_dir()
    # ...
    if not profiles_dir.exists():
        # 專案未初始化
        profile_select.set_options([("未初始化", "none")])
        profile_select.value = "none"
        info_label.update("執行 `ai-dev project init` 初始化")
        return
```

**偵測邏輯** [Source: Code] `script/commands/standards.py:40-42`:
```python
def get_profiles_dir() -> Path:
    """取得 profiles 目錄路徑"""
    return get_standards_dir() / 'profiles'
```

**實際專案狀態** [確認]：
- `.standards/` 目錄存在 ✅
- `.standards/active-profile.yaml` 存在 ✅
- `.standards/active-profile.yaml` 內容包含 `active: uds` 和 `available: [uds, ecc, minimal]` ✅
- `.standards/profiles/` 目錄**不存在** ❌

**根本原因**：
1. **設計意圖** [Source: Spec] `openspec/specs/standards-profiles/spec.md`：應該有 `profiles/` 目錄存放各 profile 的定義檔案（如 `uds.yaml`, `ecc.yaml`）
2. **當前實作**：Profile 架構未完成，只有 `active-profile.yaml` 的簡化清單模式
3. **程式邏輯錯誤**：程式依賴尚未實作的 `profiles/` 目錄，導致偵測失敗

**臨時修正策略**：改為從 `active-profile.yaml` 的 `available` 欄位讀取 profiles 清單，繞過對 `profiles/` 目錄的依賴。

## Goals

1. **簡化 ECC Hooks Plugin 區塊**：移除安裝/移除功能，只保留狀態顯示
2. **修正 Standards Profile 偵測邏輯**（臨時方案）：
   - 正確偵測專案是否已初始化（檢查 `.standards/` 目錄和 `active-profile.yaml`）
   - 從 `active-profile.yaml` 的 `available` 欄位讀取可用 profiles
   - **不實作** profiles 定義檔案機制（留待後續提案）

## Non-goals

- 不改變 CLI 指令的 `ai-dev hooks install/uninstall` 功能（保留供進階使用者使用）
- 不修改 Standards Profile 的儲存格式或資料結構
- 不新增任何 profile 管理功能
- **不實作完整的 Profile 架構**（包含 `profiles/*.yaml` 定義檔案、標準來源切換機制等）
- **不整合 ECC 標準體系**（`sources/ecc/` 的內容整合留待後續）

## Context

### ECC Hooks Plugin 架構變更

根據最近的整合工作（[Source: OpenSpec] `openspec/changes/integrate-ecc-hooks-mcp/`），專案已改為：
1. 使用者透過 `@plugins` 目錄自行管理 plugins
2. `npx skills add` 可安裝第三方 plugins
3. ai-dev 不再負責 plugin 的生命週期管理

### Standards Profile 架構的現狀

**原始設計意圖** [Source: Spec] `openspec/specs/standards-profiles/spec.md:36-62`：
```
.standards/
├── profiles/              ← 應該存在（未實作）
│   ├── uds.yaml          ← 定義 UDS 包含哪些標準
│   ├── ecc.yaml          ← 定義 ECC 包含哪些標準
│   └── minimal.yaml      ← 定義 Minimal 包含哪些標準
├── active-profile.yaml   ← 記錄當前啟用哪個
└── *.ai.yaml             ← 標準檔案
```

**當前實作狀態** [確認]：
```
.standards/
├── active-profile.yaml   ✅ 存在（包含 available 清單）
└── *.ai.yaml             ✅ 存在（但都是 UDS 格式）
# ❌ profiles/ 目錄不存在
# ❌ ECC 標準體系未整合
```

**問題根源**：Profile 架構設計完整，但實作未完成。程式依賴未實作的 `profiles/` 目錄導致功能失效。

## Open Questions

1. **臨時方案的限制**：
   - Profile 切換功能在本提案後仍無實質作用（全部使用相同的 UDS 標準）
   - 使用者切換到 `ecc` 或 `minimal` 不會載入不同的標準檔案
   - 是否需要在 UI 中顯示警告？

2. **後續 Phase 2 範圍**：
   - 建立 `profiles/*.yaml` 定義檔案
   - 整合 `sources/ecc/` 中的標準內容
   - 實作標準來源切換邏輯
   - 何時排程？

3. **ECC Hooks 安裝建議**：
   - 移除安裝按鈕後，顯示安裝提示：`npx skills add affaan-m/everything-claude-code`
   - 是否需要連結到說明文件？

## Success Criteria

1. **ECC Hooks Plugin 區塊**：
   - ✅ 只顯示「已安裝」或「未安裝」狀態
   - ✅ 移除 Install/Uninstall 按鈕
   - ✅ 保留 View Config 按鈕（檢視 hooks.json）
   - ✅ 顯示安裝提示（建議使用者如何安裝）

2. **Standards Profile 區塊**（臨時方案）：
   - ✅ 正確偵測專案已初始化（當 `.standards/active-profile.yaml` 存在）
   - ✅ 從 `active-profile.yaml` 的 `available` 欄位讀取 profiles 清單
   - ✅ 保留所有既有的切換與顯示功能
   - ⚠️ **已知限制**：Profile 切換不會載入不同標準（所有 profiles 使用相同的 UDS 標準）

3. **使用者體驗**：
   - ✅ 不再顯示誤導性的「未初始化」訊息
   - ✅ 清楚說明 ECC Hooks 的安裝方式
   - ✅ 所有快捷鍵與互動功能正常運作
   - ⚠️ 使用者需理解當前 profile 切換的限制

4. **後續擴展準備**：
   - ✅ 程式架構允許未來擴展為完整 Profile 機制
   - ✅ 變更不會破壞未來的 `profiles/` 目錄實作

## Risks

1. **中斷使用者工作流程**：移除 TUI 安裝按鈕可能影響習慣透過 TUI 管理 hooks 的使用者
   - **緩解措施**：在狀態顯示區域提供清楚的安裝指引

2. **功能完整性誤解**：使用者可能認為 Profile 切換會改變標準，但實際上所有 profiles 使用相同標準
   - **緩解措施**：在文件中明確說明當前限制，並標註「完整功能開發中」
   - **緩解措施**：考慮在 TUI 中顯示提示訊息

3. **技術債累積**：臨時方案可能導致後續重構成本增加
   - **緩解措施**：確保程式架構支援未來擴展
   - **緩解措施**：在程式碼中加入 TODO 註解標記待完成項目
   - **緩解措施**：建立 Phase 2 提案追蹤完整實作

4. **測試覆蓋不足**：TUI 的互動性使得自動化測試困難
   - **緩解措施**：提供詳細的手動測試步驟與驗收標準
