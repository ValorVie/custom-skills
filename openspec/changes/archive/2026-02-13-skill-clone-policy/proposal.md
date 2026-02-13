## Why

`ai-dev clone` 使用 `shutil.copytree(dirs_exist_ok=True)` 複製整個 skill 目錄，會無條件覆蓋目標中的同名檔案。對於含有使用者資料的 skill（如 `auto-skill` 的 `knowledge-base/` 和 `experience/`），每次 clone 都會將使用者累積的知識庫內容覆蓋為空模板。目前的衝突檢測是以整個 skill 目錄為單位，無法做到「更新 SKILL.md 但保留 knowledge-base」的精細控制。

## What Changes

- 新增 `.clonepolicy.json` 配置檔格式，允許 skill 作者宣告檔案層級的複製策略
- 修改 `_copy_with_log()` 中的 skills 複製邏輯，當偵測到 `.clonepolicy.json` 時改用逐檔複製並依策略處理
- 支援三種策略：
  - **default**（未匹配規則的檔案）：比對 hash，不同則互動提示覆蓋/跳過/備份
  - **`key-merge`**：JSON 按 key 合併，新增來源的條目、保留目標既有的使用者資料
  - **`skip-if-exists`**：目標檔案已存在就跳過，不存在才複製
- 為 `auto-skill` 新增 `.clonepolicy.json`，保護 `knowledge-base/` 和 `experience/` 目錄

## Capabilities

### New Capabilities
- `clone-policy`: 檔案層級的複製策略機制，支援 `.clonepolicy.json` 宣告式配置，涵蓋 default/key-merge/skip-if-exists 三種策略

### Modified Capabilities
- `clone-command`: 修改 `_copy_with_log()` 的 skills 複製邏輯，當 skill 目錄含有 `.clonepolicy.json` 時啟用逐檔複製

## Impact

- **程式碼**：`script/utils/shared.py`（`_copy_with_log` 函式）、`script/utils/manifest.py`（可能需要檔案層級 hash 工具函式）
- **新增檔案**：`skills/auto-skill/.clonepolicy.json`
- **相容性**：無 `.clonepolicy.json` 的 skill 行為完全不變，零破壞性
- **ManifestTracker**：現有目錄層級 hash 機制不受影響，新增的檔案層級 hash 比對僅在有 policy 時使用
