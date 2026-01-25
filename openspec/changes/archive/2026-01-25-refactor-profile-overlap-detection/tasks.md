# Tasks: refactor-profile-overlap-detection

## 1. 重疊定義建立

- [x] 1.1 建立 `profiles/overlaps.yaml` 骨架檔案
- [x] 1.2 分析現有 skills/ 與 sources/ecc/skills/ 的重疊
- [x] 1.3 分析現有 commands/ 與 sources/ecc/commands/ 的重疊
- [x] 1.4 分析 .standards/*.ai.yaml 與 ECC 原生組件的重疊
- [x] 1.5 定義 groups（tdd-workflow, commit-message, code-review, documentation）
- [x] 1.6 定義 exclusive（UDS 獨有、ECC 獨有）
- [x] 1.7 驗證 overlaps.yaml 格式正確

## 2. Profile 定義更新

- [x] 2.1 更新 `profiles/uds.yaml` 為新格式（移除 includes/inherits/overrides）
- [x] 2.2 更新 `profiles/ecc.yaml` 為新格式
- [x] 2.3 更新 `profiles/minimal.yaml` 為新格式
- [x] 2.4 新增 overlap_preference 欄位
- [x] 2.5 新增 enable_exclusive 欄位
- [x] 2.6 驗證各 profile 定義格式正確

## 3. disabled.yaml 格式擴展

- [x] 3.1 更新 `script/commands/standards.py` 支援新的 disabled.yaml 格式
- [x] 3.2 新增 `_profile`, `_profile_disabled`, `_manual` 欄位處理
- [x] 3.3 確保向後相容（現有工具仍可讀取 skills/commands/agents 欄位）
- [x] 3.4 實作合併手動與 profile 停用邏輯

## 4. Profile 切換邏輯

- [x] 4.1 實作 `load_overlaps()` 載入重疊定義
- [x] 4.2 實作 `collect_items()` 收集項目
- [x] 4.3 實作 `compute_disabled_items()` 計算需停用項目
- [x] 4.4 實作 `switch_profile()` 核心切換邏輯
- [x] 4.5 實作 dry-run 模式預覽變更
- [x] 4.6 保護手動停用項目（不被 profile 覆蓋）
- [x] 4.7 實作 `sync_resources()` 自動同步檔案狀態
- [x] 4.8 整合 switch_profile() 自動呼叫 sync_resources()

## 5. CLI 指令更新

- [x] 5.1 更新 `ai-dev standards switch` 使用新邏輯
- [x] 5.2 新增 `--dry-run` 參數
- [x] 5.3 更新 `ai-dev standards show` 顯示重疊分析
- [x] 5.4 更新 `ai-dev standards list` 顯示格式
- [x] 5.5 新增 `ai-dev standards overlaps` 顯示重疊定義
- [x] 5.6 更新 `ai-dev standards status` 顯示當前停用項目

## 6. upstream-sync/compare 整合

- [x] 6.1 更新 `upstream-sync/scripts/analyze_upstream.py` 新增重疊偵測
- [x] 6.2 新增 `detect_overlaps()` 函式
- [x] 6.3 更新 `upstream-compare/SKILL.md` 新增 overlap_analysis 輸出格式
- [x] 6.4 新增 `--generate-overlaps` 參數自動生成 overlaps.yaml
- [x] 6.5 更新報告模板包含重疊建議

## 7. TUI 更新

- [x] 7.1 更新 Profile Selector 顯示重疊摘要
- [x] 7.2 更新切換使用新的 switch_profile 邏輯
- [x] 7.3 新增重疊預覽功能

## 8. 舊設計清理

- [x] 8.1 刪除 `profiles/standards/` 相關程式碼（無此目錄）
- [x] 8.2 移除 `includes`, `inherits`, `overrides` 處理邏輯
- [x] 8.3 更新相關文件

## 9. Spec 更新

- [x] 9.1 更新 `standards-profiles` spec 反映新設計
- [x] 9.2 更新 `resource-disable` spec 新增 profile 來源標記
- [x] 9.3 建立 `overlap-detection` spec（新規格）

## 10. 文件與測試

- [x] 10.1 更新 README.md Profile 系統說明
- [x] 10.2 更新 CHANGELOG.md
- [x] 10.3 手動測試 `ai-dev standards switch uds`
- [x] 10.4 手動測試 `ai-dev standards switch ecc`
- [x] 10.5 手動測試 `ai-dev standards switch minimal`
- [x] 10.6 驗證切換後 disabled.yaml 正確
- [x] 10.7 驗證 TUI Profile 選單正常運作（Python 語法驗證通過）
- [ ] 10.8 測試 `/upstream-compare` 重疊分析輸出（需人工測試）

## 11. 遷移

- [x] 11.1 建立遷移腳本（從舊格式到新格式）— 無需遷移腳本，直接使用新格式
- [x] 11.2 執行遷移 — 建立新的 profiles 目錄與檔案
- [x] 11.3 驗證遷移結果 — 程式碼已更新使用新格式
- [x] 11.4 刪除舊檔案（profiles/standards/ 等）— 無此目錄
